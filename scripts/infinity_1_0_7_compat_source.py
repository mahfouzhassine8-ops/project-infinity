#!/usr/bin/env python3
"""Apply Infinity 1.0.7 Candidate 1 crash hardening after the 1.0.6 source step.

The captured Android tombstone showed Kodi aborting in CPythonInvoker::PyObjectDeleter
because the debug-only exact refcount assertion was violated during add-on module
initialization. PyObjectPtr owns exactly one new reference, so its deleter must release
that owned reference whether PyDict_SetItemString succeeds or fails; it must not require
an exact total refcount. This patch also checks each dictionary insertion and fixes the
existing invoker-id temporary-reference leak.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

PINNED_PYTHON_INVOKER = '87bc2a46f9bda463d5b2f01002b81c7bbc047c97'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)


OLD_INIT = '''  PyObject* moduleDictionary = (PyObject*)moduleDict;\n\n  PyDict_SetItemString(moduleDictionary, "__xbmcaddonid__",\n                       PyObjectPtr(PyUnicode_FromString(m_addon->ID().c_str())).get());\n\n  ADDON::CAddonVersion version = m_addon->GetDependencyVersion("xbmc.python");\n  PyDict_SetItemString(moduleDictionary, "__xbmcapiversion__",\n                       PyObjectPtr(PyUnicode_FromString(version.asString().c_str())).get());\n\n  PyDict_SetItemString(moduleDictionary, "__xbmcinvokerid__", PyLong_FromLong(GetId()));\n'''

NEW_INIT = '''  PyObject* moduleDictionary = (PyObject*)moduleDict;\n\n  // PyDict_SetItemString adds its own reference on success. Keep ownership of the\n  // temporary object in PyObjectPtr and always release only that owned reference.\n  // A failed insertion therefore remains safe instead of tripping an exact-refcount\n  // assertion and aborting the whole Android process.\n  const auto setModuleItem = [this, moduleDictionary](const char* key, PyObjectPtr value)\n  {\n    if (!value)\n    {\n      CLog::Log(LOGERROR, "CPythonInvoker({}, {}): failed creating module item {}", GetId(),\n                m_sourceFile, key);\n      PyErr_Clear();\n      return false;\n    }\n    if (PyDict_SetItemString(moduleDictionary, key, value.get()) != 0)\n    {\n      CLog::Log(LOGERROR, "CPythonInvoker({}, {}): failed setting module item {}", GetId(),\n                m_sourceFile, key);\n      PyErr_Clear();\n      return false;\n    }\n    return true;\n  };\n\n  setModuleItem("__xbmcaddonid__", PyObjectPtr(PyUnicode_FromString(m_addon->ID().c_str())));\n\n  ADDON::CAddonVersion version = m_addon->GetDependencyVersion("xbmc.python");\n  setModuleItem("__xbmcapiversion__",\n                PyObjectPtr(PyUnicode_FromString(version.asString().c_str())));\n\n  setModuleItem("__xbmcinvokerid__", PyObjectPtr(PyLong_FromLong(GetId())));\n'''

OLD_DELETER = '''void CPythonInvoker::PyObjectDeleter::operator()(PyObject* p) const\n{\n  assert(Py_REFCNT(p) == 2);\n  Py_DECREF(p);\n}\n'''

NEW_DELETER = '''void CPythonInvoker::PyObjectDeleter::operator()(PyObject* p) const\n{\n  // PyObjectPtr owns one new reference. The object may have any additional\n  // references (for example from a module dictionary), so exact total refcount\n  // is not an ownership invariant. Release only the reference we own.\n  Py_DECREF(p);\n}\n'''


def apply(source: Path) -> dict:
    source = source.resolve()
    invoker = source / 'xbmc/interfaces/python/PythonInvoker.cpp'
    gradle = source / 'tools/android/packaging/xbmc/build.gradle.in'
    if not invoker.is_file() or not gradle.is_file():
        raise FileNotFoundError('Expected Kodi source files are missing')

    before_invoker = sha(invoker)
    if before_invoker != PINNED_PYTHON_INVOKER:
        raise RuntimeError('Refusing unpinned PythonInvoker.cpp: ' + before_invoker)

    invoker_text = invoker.read_text()
    invoker_text = replace_once(invoker_text, OLD_INIT, NEW_INIT, 'Python module metadata ownership')
    invoker_text = replace_once(invoker_text, OLD_DELETER, NEW_DELETER, 'PyObjectPtr deleter')
    invoker.write_text(invoker_text)

    gradle_text = gradle.read_text()
    gradle_text = replace_once(gradle_text, 'versionCode 2103106', 'versionCode 2103107', 'versionCode')
    gradle_text = replace_once(gradle_text, 'versionName "21.3-Infinity-1.0.6"',
                               'versionName "21.3-Infinity-1.0.7-Candidate-1"', 'versionName')
    gradle.write_text(gradle_text)

    final = invoker.read_text()
    if 'assert(Py_REFCNT(p) == 2)' in final:
        raise RuntimeError('Fatal exact-refcount assertion remains')
    for needle in ('setModuleItem("__xbmcaddonid__"', 'setModuleItem("__xbmcapiversion__"',
                   'setModuleItem("__xbmcinvokerid__"'):
        if needle not in final:
            raise RuntimeError('Missing ownership hardening: ' + needle)

    return {
        'schema': 1,
        'release': '1.0.7 Candidate 1',
        'versionCode': 2103107,
        'crash_evidence_target': 'CPythonInvoker::PyObjectDeleter SIGABRT after Stop',
        'fix_scope': 'Python module metadata temporary-reference ownership and insertion errors',
        'decoder_teardown_changed': False,
        'addon_callbacks_disabled': False,
        'device_tested': False,
        'files': {
            'xbmc/interfaces/python/PythonInvoker.cpp': {'before': before_invoker, 'after': sha(invoker)},
            'tools/android/packaging/xbmc/build.gradle.in': {'after': sha(gradle)},
        },
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--receipt', required=True, type=Path)
    a = p.parse_args()
    receipt = apply(a.source)
    a.receipt.parent.mkdir(parents=True, exist_ok=True)
    a.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print('Infinity 1.0.7 Candidate 1 Python crash hardening applied.')


if __name__ == '__main__':
    main()
