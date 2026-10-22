"""Apply only to the hash-verified, complete 2103401 native source inventory."""
from pathlib import Path
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent
BASELINE = json.loads((HERE / 'BASELINE.json').read_text())
BRIDGE = 'xbmc/interfaces/python/InfinityPythonPersistence.h'
OBSERVER = 'xbmc/interfaces/python/InfinityPythonPersistenceSource.h'
LEDGER = 'xbmc/platform/android/activity/InfinityScriptPersistence.h'
WRITES = 'xbmc/platform/android/activity/InfinityProtectedWrites.h'
HOOKS = 'xbmc/interfaces/python/InfinityPythonWriteHooks.h'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def once(raw, old, new):
    if raw.count(old) != 1:
        raise ValueError('Missing or ambiguous exact source anchor: ' + repr(old[:100]))
    return raw.replace(old, new, 1)


def patches(before):
    if set(before) != set(BASELINE['before']):
        raise ValueError('Unexpected native source scope')
    for name, data in before.items():
        if sha(data) != BASELINE['before'][name]:
            raise ValueError('Native source preimage mismatch: ' + name)
    bridge = before[BRIDGE].decode()
    bridge = once(bridge, '  PyObject* rawWrite{nullptr};',
        '  PyObject* rawWrite{nullptr};\n  PyObject* vfsType{nullptr};\n  PyObject* vfsWrite{nullptr};')
    anchor = 'inline PyObject* Error(PyObject* self,PyObject* args)'
    bridge = once(bridge, anchor, (HERE / 'vfs_outcome.inc').read_text() + '\n' + anchor)
    bridge = once(bridge,
        '  static PyMethodDef errorMethod={"record_failure",Error,METH_VARARGS,nullptr};',
        '  static PyMethodDef vfsWriteMethod={"checked_vfs_write",CheckedVfsWrite,METH_VARARGS,nullptr};\n'
        '  static PyMethodDef errorMethod={"record_failure",Error,METH_VARARGS,nullptr};')
    bridge = once(bridge,
        '    context->observer=PyObject_CallFunctionObjArgs(klass,error,mutation,vfs,hostProbe,protection,context->admissionError,nullptr);',
        '    CaptureNativeVfsContract(context, vfs);\n'
        '    PyObject* vfsWrite=PyCFunction_NewEx(&vfsWriteMethod,capsule,nullptr);\n'
        '    if(vfsWrite) {\n'
        '      context->observer=PyObject_CallFunctionObjArgs(klass,error,mutation,vfs,hostProbe,protection,context->admissionError,vfsWrite,nullptr);\n'
        '      Py_DECREF(vfsWrite);\n'
        '    }')
    bridge = once(bridge, '  Py_CLEAR(context->rawWrite);Py_CLEAR(context->rawType);',
        '  Py_CLEAR(context->rawWrite);Py_CLEAR(context->rawType);\n'
        '  Py_CLEAR(context->vfsWrite);Py_CLEAR(context->vfsType);')
    observer = before[OBSERVER].decode()
    observer = once(observer,
        'def __init__(self, fail, touch, vfs=None, host_probe=False, protect=None, closed_error=None):',
        'def __init__(self, fail, touch, vfs=None, host_probe=False, protect=None, closed_error=None, native_vfs_write=None):')
    observer = once(observer, '        self.closed_error = closed_error',
        '        self.closed_error = closed_error\n        self.native_vfs_write = native_vfs_write')
    observer = once(observer,
        '                        handle = VFSFile(_original(path, mode), observer, translated)',
        '                        handle = VFSFile(_original(path, mode), observer, translated)\n'
        '                        # A writable VFS open may already truncate/create data.\n'
        '                        # Keep its drain obligation until checked native close.\n'
        '                        observer.buffer(handle, (translated,), True)')
    # The native callback dispatches AND classifies the same real callable. It
    # never accepts a Python claim that a TypeError means no data changed.
    observer = once(observer,
        "    @protected_method('vfs.write')\n    def write(self, value):\n        self.observer.check_live()\n",
        "    @protected_method('vfs.write')\n    def write(self, value):\n        self.observer.check_live()\n"
        '        if self.observer.native_vfs_write is not None:\n'
        '            return self.observer.native_vfs_write(self._infinity_handle, value)\n')
    ledger = once(before[LEDGER].decode(), '  std::set<std::string> paths;\n',
        '  std::set<std::string> paths;\n  std::set<std::string> removedNamespaces;\n')
    writes = before[WRITES].decode()
    writes = once(writes, '  const auto token = ++p.nextOperation;',
        '  // Any later admitted operation that overlaps a removed name revokes\n'
        '  // its earlier absence evidence, even when the new operation fails.\n'
        '  if (paths.empty()) p.removedNamespaces.clear();\n'
        '  if (operation != "converted_native_write_target")\n'
        '  for (const auto& raw : paths) {\n'
        '    if (raw == NonPersistentTarget()) continue;\n'
        '    const auto path = Absolute(raw);\n'
        '    const bool removesParent = operation == "rmdir" || operation == "namespace.rmdir";\n'
        '    for (auto it=p.removedNamespaces.begin(); it!=p.removedNamespaces.end();)\n'
        '      if (path.empty() || Within(path,*it) || (!removesParent && Within(*it,path))) it=p.removedNamespaces.erase(it);\n'
        '      else ++it;\n'
        '  }\n'
        '  const auto token = ++p.nextOperation;')
    writes = once(writes, 'inline bool SyncProtectedPath(const std::string& path,',
        (HERE/'namespace_outcome.inc').read_text()+'\ninline bool SyncProtectedPath(const std::string& path,')
    writes = once(writes,
        '                              const std::vector<std::string>& profiles)\n{\n  struct stat st{};',
        '                              const std::vector<std::string>& profiles,\n'
        '                              const std::set<std::string>& removed = {})\n{\n  struct stat st{};')
    writes = once(writes,
        'return errno == ENOENT && SyncRemovedInstallerStage(parent, path, profiles);',
        'return errno == ENOENT && (SyncRemovedNamespace(path, removed) ||\n'
        '                               SyncRemovedInstallerStage(parent, path, profiles));')
    writes = once(writes, '  std::vector<std::string> paths, profiles;',
        '  std::vector<std::string> paths, profiles;\n  std::set<std::string> removed;')
    writes = once(writes, '    profiles = p.profiles;',
        '    removed = p.removedNamespaces;\n    profiles = p.profiles;')
    writes = once(writes, '!SyncProtectedPath(canonical, profiles)',
        '!SyncProtectedPath(canonical, profiles, removed)')
    hooks = before[HOOKS].decode()
    hooks = once(hooks,
        '    if (result && m_kind == EXTENSION_CREATE && !ProtectNativeModule(result))',
        '    if (result && m_token && !m_paths.empty() &&\n'
        '        (m_kind == OS_RENAME || m_kind == OS_REPLACE || m_kind == OS_REMOVE ||\n'
        '         m_kind == OS_UNLINK || m_kind == OS_RMDIR))\n'
        '      Ledger::RecordRemovedNamespace(m_token,m_paths.front());\n'
        '    if (result && m_kind == EXTENSION_CREATE && !ProtectNativeModule(result))')
    return {BRIDGE: bridge.encode(), OBSERVER: observer.encode(),
            LEDGER: ledger.encode(), WRITES: writes.encode(), HOOKS: hooks.encode()}


def apply(source, source_map, output):
    expected = json.loads(source_map.read_text())
    if len(expected) != BASELINE['source_count'] or sha(json.dumps(
            expected, sort_keys=True, separators=(',', ':')).encode()) != BASELINE['source_map_sha256']:
        raise ValueError('Complete matching 2103401 source map required')
    for name, pin in expected.items():
        if sha((source / name).read_bytes()) != pin:
            raise ValueError('Source drift: ' + name)
    after = patches({name: (source / name).read_bytes() for name in BASELINE['before']})
    output.mkdir(parents=True, exist_ok=False)
    for name, data in after.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    proof = dict(before=BASELINE['before'], after={n: sha(b) for n, b in after.items()},
        native_source_count=len(expected), other_native_inputs_unchanged=len(expected)-len(after),
        native_source_only=True, signed_apk_created=False, android_validated=False,
        physical_fold_verified=False, final_lock=False)
    (output / 'SOURCE-DELTA.json').write_text(json.dumps(proof, indent=2) + '\n')
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-map', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.source, args.source_map, args.output), indent=2))
