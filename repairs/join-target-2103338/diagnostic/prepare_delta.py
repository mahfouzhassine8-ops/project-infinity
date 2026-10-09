#!/usr/bin/env python3
"""Prepare an isolated diagnostic-only delta; never edit the supplied Kodi tree.

Requires the two exact retained 2103334 source preimages. Writes three replacement
files, a unified patch and a receipt into a NEW output directory. This is not an
APK builder and cannot attest full-source lineage or physical-device acceptance.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CPP = 'xbmc/interfaces/generic/LanguageInvokerThread.cpp'
HEADER = 'xbmc/interfaces/generic/LanguageInvokerThread.h'
HELPER = 'xbmc/interfaces/generic/InfinityInvokerTarget.h'
EXPECTED = {
    CPP: 'abf0632a0904345c22c7f32cab4b9006b342bce5d80b42f3858853655fbafe3f',
    HEADER: 'b4f3cdee3d365eb8c70b5d2f6546b0f770c3aef3ca4055a2e209d4a24625d8e2',
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f'Unexpected source anchor ({text.count(old)}): {old!r}')
    return text.replace(old, new, 1)

def guarded(statement: str, indent: str = '  ') -> str:
    return '#if defined(TARGET_ANDROID)\n' + indent + statement + '\n#endif\n'

def transform(cpp: str, header: str) -> tuple[str, str]:
    header = once(header, '#include "threads/Thread.h"',
                  '#include "threads/Thread.h"\n#if defined(TARGET_ANDROID)\n'
                  '#include "InfinityInvokerTarget.h"\n#endif')
    header = once(header, 'private:\n', 'private:\n#if defined(TARGET_ANDROID)\n'
                  '  InfinityInvokerTarget m_infinityDiagnosticTarget;\n'
                  '  void InfinityTraceTarget(const char* phase) const;\n#endif\n')
    cpp = once(cpp, '#include <utility>', '#include <utility>\n#if defined(TARGET_ANDROID)\n'
               '#include <cstdio>\n#include <sys/syscall.h>\n#include <unistd.h>\n#endif')
    cpp = once(cpp, '  Release();\n', guarded(
               'InfinityTraceTarget("scripts.target_before_stop");') + '  Release();\n')
    # The trace is emitted before the already-existing CThread stop/join scope.
    cpp = once(cpp, '  // stop the thread\n', '  // stop the thread\n' + guarded(
               'InfinityTraceTarget(wait ? "scripts.target_before_join"\n'
               '                           : "scripts.target_before_nonblocking_stop");'))
    cpp = once(cpp, 'void CLanguageInvokerThread::OnStartup()\n{\n',
               'void CLanguageInvokerThread::OnStartup()\n{\n' + guarded(
               '{\n    InfinityShutdownTrace::PreserveErrno keepErrno;\n'
               '    m_infinityDiagnosticTarget.Start(static_cast<std::uint32_t>(::syscall(SYS_gettid)));\n  }'))
    cpp = once(cpp, '  std::unique_lock<std::mutex> lckdl(m_mutex);', guarded(
               'm_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ProcessMutex);') +
               '  std::unique_lock<std::mutex> lckdl(m_mutex);')
    cpp = once(cpp, '    m_invoker->Execute(m_script, m_args);', guarded(
               'm_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::Execute);', '    ') +
               '    m_invoker->Execute(m_script, m_args);')
    cpp = once(cpp, '    m_condition.wait(lckdl, [this] { return m_bStop || m_restart || !m_reusable; });',
               guarded('m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ReuseWait);', '    ') +
               '    m_condition.wait(lckdl, [this] { return m_bStop || m_restart || !m_reusable; });')
    cpp = once(cpp, '  m_invoker->onExecutionDone();\n  m_invocationManager->OnExecutionDone(GetId());',
               guarded('m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::Finalizer);') +
               '  m_invoker->onExecutionDone();\n' +
               guarded('m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ManagerCallback);') +
               '  m_invocationManager->OnExecutionDone(GetId());\n' +
               guarded('m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ExitReported);').rstrip('\n'))
    cpp = once(cpp, '  m_invoker->onExecutionFailed();\n  m_invocationManager->OnExecutionDone(GetId());',
               guarded('m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ExceptionFinalizer);') +
               '  m_invoker->onExecutionFailed();\n' +
               guarded('m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ExceptionManagerCallback);') +
               '  m_invocationManager->OnExecutionDone(GetId());\n' +
               guarded('m_infinityDiagnosticTarget.Mark(InfinityInvokerTarget::Stage::ExceptionReported);').rstrip('\n'))
    cpp += '''

#if defined(TARGET_ANDROID)
void CLanguageInvokerThread::InfinityTraceTarget(const char* phase) const
{
  InfinityShutdownTrace::PreserveErrno keepErrno;
  const auto snapshot = m_infinityDiagnosticTarget.Read();
  char target[65]{};
  std::snprintf(target, sizeof(target), "os_tid.%u.stage.%s",
                static_cast<unsigned>(snapshot.tid), InfinityInvokerTarget::Name(snapshot.stage));
  // Uses the existing selected scripts.* trace stream and its existing budgets.
  // This does not start capture, create a new file, acquire the GIL, or prove
  // that the sampled thread is still alive. TID and stage are one observation.
  InfinityShutdownTrace::Event("milestone", phase, GetId(), 0, 0, 0,
                              m_addon ? m_addon->ID().c_str() : nullptr,
                              snapshot.tid ? "snapshot_not_liveness" : "target_not_started", target);
}
#endif
'''
    return cpp, header

def prepare(source: Path, output: Path) -> dict:
    source = source.resolve()
    output = output.resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError('Output must be a separate directory, not inside/above the source tree')
    if output.exists():
        raise FileExistsError('Output already exists; refusing to overwrite it')
    original = {name: (source / name).read_bytes() for name in EXPECTED}
    if (source / HELPER).exists():
        raise ValueError('Helper already exists in parent source')
    for name, expected in EXPECTED.items():
        if sha(original[name]) != expected:
            raise ValueError('Not the exact retained 3334 preimage: ' + name)
    cpp, header = transform(original[CPP].decode(), original[HEADER].decode())
    changed = {CPP: cpp.encode(), HEADER: header.encode(), HELPER: (HERE / 'InfinityInvokerTarget.h').read_bytes()}
    output.mkdir(parents=True, exist_ok=False)
    patches = []
    for name, content in changed.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        raw_diff = difflib.unified_diff(original.get(name, b'').decode().splitlines(True),
                       content.decode().splitlines(True), fromfile='a/' + name if name in original else '/dev/null',
                       tofile='b/' + name)
        patches.extend(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n' for line in raw_diff)
    receipt = {'diagnostic_only': True, 'root_cause_fixed': False, 'apk_built': False,
               'physical_device_tested': False, 'github_modified': False, 'locked': False,
               'source_scope': 'Two verified preimages; not a whole-engine reconstruction or historical APK proof.',
               'before': EXPECTED, 'after': {name: sha(data) for name, data in changed.items()},
               'original_tree_unchanged': all((source / name).read_bytes() == data for name, data in original.items()),
               'new_trace_phases': ['scripts.target_before_stop','scripts.target_before_join',
                                    'scripts.target_before_nonblocking_stop']}
    (output / 'diagnostic-only.patch').write_text(''.join(patches))
    (output / 'DELTA-RECEIPT.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.source, args.output)
    except (OSError, ValueError) as error:
        parser.exit(2, f'Not prepared: {error}\n')
    print(json.dumps(result, indent=2))
