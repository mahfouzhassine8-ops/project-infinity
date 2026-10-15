#!/usr/bin/env python3
"""Shutdown-only delta on the SHA-verified Rails Handoff RC1 source.

Uses the existing script ledger, database barrier and coordinator. Compilation
is not delivery authorization; packaging requires independent runtime evidence.
"""
import hashlib
import json
from pathlib import Path
import stage_experiment

HERE = Path(__file__).resolve().parent
CHECKPOINT = stage_experiment.CHECKPOINT
MANAGER = 'xbmc/interfaces/generic/ScriptInvocationManager.cpp'
SQLITE = 'xbmc/dbwrappers/sqlitedataset.cpp'
POSIX = 'xbmc/platform/posix/filesystem/PosixFile.cpp'
DIRECTORY = 'xbmc/platform/posix/filesystem/PosixDirectory.cpp'
JOBS = 'xbmc/utils/JobManager.cpp'
INSTALLER = 'xbmc/addons/AddonInstaller.cpp'
PINS = {
    CHECKPOINT: stage_experiment.PIN,
    MANAGER: 'b3ff61b946ed767e3c586caa74fab0ae1c35b404ecef4b46839270d84f57f16e',
    SQLITE: '18206a86843f11bea447ebbe1ecca474bf3ae62aef9bd204e37c671515111920',
    POSIX: '0a880f1de9c1cb9d7c1cd0c99fc1ae0334c87ddb77faa50b81af8d80d7ef3baa',
    DIRECTORY: '68e638f060868bca397dd5a8e1f85232a70df31f92692460b0e741a63205094a',
    JOBS: '8315f6ad8c794d5a96bcb544b0e53eee585faec121e15806edd163f97f4b8d3c',
    INSTALLER: 'a9e21a3b0c9da59b33376d15b53ac7ba8886613c15b59878496cb31833502b9b',
}
once = stage_experiment.once

def checkpoint(text):
    # Reuse the completed sequencing change; replace the historical fake-hook
    # experiment with the existing persistence ledger's real runtime leases.
    text = stage_experiment.checkpoint(text)
    text = text.replace('InfinityEssentialScriptFence.h', 'InfinityProtectedWrites.h')
    text = text.replace('InfinityEssentialScriptFence::Snapshot()', 'InfinityScriptPersistence::EssentialWrites()')
    text = text.replace('InfinityEssentialScriptFence::Authorized(', 'InfinityScriptPersistence::EssentialWritesAuthorized(')
    text = text.replace('essential.sealed', '(essential.phase == 3)')
    text = text.replace('static_cast<uint64_t>(essential.optionalUnfinished)',
                        'static_cast<uint64_t>(InfinityScriptPersistence::OptionalUnfinishedWriters())')
    start = text.index('bool AuthorizeTermination(')
    authorization = text[start:]
    authorization = once(authorization, '    if (!Matches(s, session, owner, pid))',
                         '    if (!Matches(s, session, owner, pid) || s.phase != "SAFE_TO_TERMINATE")')
    text = text[:start] + authorization
    text = once(text, '  InfinityShutdownTrace::Begin();', '''  if (!InfinityScriptPersistence::BeginWriteProtection(infinityDiagnosticGeneration,
        {CSpecialProtocol::TranslatePath("special://profile"),
         CSpecialProtocol::TranslatePath("special://masterprofile")},
        {CSpecialProtocol::TranslatePath("special://temp")}))
  { RecordFatalFailure("native_admission", "protected_write_request_failed"); return false; }
  InfinityShutdownTrace::Begin();''')
    start = text.index('      // First-party callbacks have finished.')
    end = text.index('      Operation("background_jobs");', start)
    text = text[:start] + '''      // Keep optional retirement receipts diagnostic. First-party callbacks
      // above and the required background jobs below are still mandatory.
      const auto scripts = InfinityScriptPersistence::Snapshot();
      if (scripts.durable && scripts.active == 0 && scripts.blockingCount == 0)
        Complete("python_services", true);

''' + text[end:]
    text = once(text, '''      if (!InfinityDatabaseBarrier::Begin(s.generation))''', '''      if (!InfinityScriptPersistence::CloseParticipantWrites(s.generation))
      { RecordFatalFailure("native_admission", "protected_participant_admission_close_failed"); return; }
      if (!InfinityDatabaseBarrier::Begin(s.generation))''')
    text = once(text, '''      if (!InfinityEssentialScriptFence::Seal(s.generation))
      { RecordFatalFailure("native_admission", "essential_script_file_seal_failed"); return; }
      Complete("native_admission", false);
''', '')
    # Seal only AFTER final essential callbacks and native database durability.
    text = once(text, '''      bool databaseBlocked=false;''', '''      if (!InfinityScriptPersistence::SealEssentialWrites(s.generation))
      {
        const auto proof = InfinityScriptPersistence::EssentialWrites();
        RecordFatalFailure("native_admission", proof.blockers.empty() ?
            "protected_write_seal_not_durable" : proof.blockers.front().c_str());
        return;
      }
      Complete("native_admission", false);

      bool databaseBlocked=false;''')
    start = text.index('  result["blocking_jobs"] = CVariant(CVariant::VariantTypeArray);')
    end = text.index('  result["resolved_job_obligations"]', start)
    optional = text[start:end].replace('blocking_jobs', 'optional_unfinished_jobs').replace(
        's.jobs.blockers', 's.jobs.optionalUnfinished')
    text = text[:end] + optional + text[end:]
    assert 'InfinityEssentialScriptFence' not in text
    return text

def jobs(text):
    return once(text, '''      if (actualType.find("CRepositoryUpdateJob") != std::string::npos)
      {
        role = CJob::CheckpointResponsibility::Required;''', '''      if (actualType.find("CRepositoryUpdateJob") != std::string::npos)
      {
        // Repository metadata/network completion is optional. Actual native
        // SQLite transactions and file operations retain independent leases;
        // nested installation scopes remain required and admission-controlled.
        role = CJob::CheckpointResponsibility::NonPersistent;''')

def installer(text):
    text = once(text, '#include "AddonInstaller.h"', '''#include "AddonInstaller.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif''')
    return once(text, '''  CAddonOperationReceipt completion("addon_install", m_addon->ID(), m_completionVerified);
#endif''', '''  CAddonOperationReceipt completion("addon_install", m_addon->ID(), m_completionVerified);
  // Also covers synchronous dependency installs from repository callbacks.
  // Empty existing file/database scopes prove unchanged state on rejection.
  // An already-admitted install keeps its original required durability receipt.
  InfinityAndroidCheckpoint::CheckpointWriteGuard admission("jobs");
  if (!admission) return false;
#endif''')

def manager(text):
    text = once(text, '#include "platform/android/activity/InfinityScriptPersistence.h"',
                '#include "platform/android/activity/InfinityScriptPersistence.h"\n#include "platform/android/activity/InfinityProtectedWrites.h"')
    import re
    pattern = r'(?m)^( +)if \(checkpointContract.empty\(\)\)\n +InfinityScriptPersistence::Admit\(invokerThread->GetId\(\),\n +\(addon \? addon->ID\(\) : "unidentified"\) \+ ":" \+ URIUtils::GetFileName\(script\)\);'
    def replace(match):
        pad = match.group(1)
        return pad + '''InfinityScriptPersistence::Admit(invokerThread->GetId(),
''' + pad + '''  (addon ? addon->ID() : "unidentified") + ":" + URIUtils::GetFileName(script));
''' + pad + '''if (checkpointContract == "command_center" || checkpointContract == "compat")
''' + pad + '''  InfinityScriptPersistence::RegisterParticipant(invokerThread->GetId());'''
    text, count = re.subn(pattern, replace, text)
    assert count == 2, count
    return text

def sqlite(text):
    text = once(text, '#include "InfinityDatabaseBarrier.h"',
                '#include "InfinityDatabaseBarrier.h"\n#include "InfinitySQLiteVFS.h"')
    text = once(text, '    int errorCode = sqlite3_open_v2(', '''    if (!InfinitySQLiteVFS::Install())
      throw DbErrors("Protected SQLite VFS installation failed");
    int errorCode = sqlite3_open_v2(''')
    text = once(text, '  rc = sqlite3_open(backup_path.c_str(), &pFile);', '''  if (!InfinitySQLiteVFS::Install()) return DB_UNEXPECTED_RESULT;
  rc = sqlite3_open(backup_path.c_str(), &pFile);''')
    return text

def posix(text):
    text = once(text, '#include "PosixFile.h"', '''#include "PosixFile.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityProtectedWrites.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif''')
    def guard(paths, operation, failure, descriptor='-1'):
        return '''#if defined(TARGET_ANDROID)
  InfinityScriptPersistence::ProtectedOperation infinityWrite(
      InfinityScriptPersistence::CurrentWriteOwner(), {''' + paths + '''}, "''' + operation + '''",
      InfinityAndroidCheckpoint::IsPersistingOnThisThread(), false, ''' + descriptor + ''');
  if (!infinityWrite) return ''' + failure + ''';
#endif
'''
    text = once(text, '  m_fd = open(filename.c_str(), O_RDWR',
                guard('filename', 'posix.open_write', 'false') + '  m_fd = open(filename.c_str(), O_RDWR')
    for method, signature in [('Write', 'ssize_t CPosixFile::Write(const void* lpBuf, size_t uiBufSize)'),
                              ('Truncate', 'int CPosixFile::Truncate(int64_t size)')]:
        opening = signature+'\n{\n  if (m_fd < 0)\n    return -1;\n'
        text = once(text, opening, opening+'\n'+guard(
            'InfinityScriptPersistence::DescriptorPath(m_fd)', 'posix.'+method.lower(), '-1', 'm_fd'))
    text = once(text, '  if (unlink(filename.c_str()) == 0)', guard('filename', 'posix.unlink', 'false')+'  if (unlink(filename.c_str()) == 0)')
    text = once(text, '  if (rename(name.c_str(), newName.c_str()) == 0)\n    return true;', guard('name, newName', 'posix.rename', 'false')+'''  if (rename(name.c_str(), newName.c_str()) == 0)
  {
#if defined(TARGET_ANDROID)
    InfinityScriptPersistence::RememberAlias(name, newName);
#endif
    return true;
  }''')
    return text

def directory(text):
    text = once(text, '#include "PosixDirectory.h"', '''#include "PosixDirectory.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityProtectedWrites.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif''')
    def guard(path, operation):
        return '''#if defined(TARGET_ANDROID)
  InfinityScriptPersistence::ProtectedOperation infinityDirectoryWrite(
      InfinityScriptPersistence::CurrentWriteOwner(), {''' + path + '''}, "''' + operation + '''",
      InfinityAndroidCheckpoint::IsPersistingOnThisThread());
  if (!infinityDirectoryWrite) return false;
#endif
'''
    text = once(text, '  if (mkdir(path.c_str(), 0755) != 0)', guard('path', 'posix.mkdir')+'  if (mkdir(path.c_str(), 0755) != 0)')
    text = once(text, '  if (rmdir(url.Get().c_str()) == 0)', guard('url.Get()', 'posix.rmdir')+'  if (rmdir(url.Get().c_str()) == 0)')
    start = text.index('bool CPosixDirectory::RemoveRecursive(')
    text = text[:start] + once(text[start:], '  DIR *dir = opendir(root.c_str());', guard('root', 'posix.remove_recursive')+'  DIR *dir = opendir(root.c_str());')
    return text

def apply(root, locked_manifest):
    root = Path(root)
    expected = json.loads(Path(locked_manifest).read_text())['after']
    replacements = {}
    for name, transform in [(CHECKPOINT, checkpoint), (MANAGER, manager), (SQLITE, sqlite), (POSIX, posix), (DIRECTORY, directory), (JOBS, jobs), (INSTALLER, installer)]:
        old = (root/name).read_bytes()
        actual = hashlib.sha256(old).hexdigest()
        assert actual == PINS[name] == expected[name], (name, actual)
        replacements[name] = transform(old.decode()).encode()
    for file in (HERE/'runtime/xbmc').rglob('*'):
        if not file.is_file(): continue
        name = str(file.relative_to(HERE/'runtime'))
        target = root/name
        if target.exists():
            assert hashlib.sha256(target.read_bytes()).hexdigest() == expected[name], name
        else:
            assert name not in expected, name
        replacements[name] = file.read_bytes()
    before = {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
              for name in replacements if (root/name).exists()}
    # Resolve every preimage and transform before the first mutation.
    for name, data in replacements.items():
        target = root/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    return {'before': before, 'after': {n: hashlib.sha256(b).hexdigest() for n,b in replacements.items()},
            'changed': sorted(replacements), 'diagnostic_owner_count': 17, 'essential_owner_count': 16,
            'locked': False, 'apk_deliverable': False}

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--locked-manifest', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.write_text(json.dumps(apply(a.source, a.locked_manifest), indent=2)+'\n')
