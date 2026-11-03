"""Stage a bounded local watched-job receipt; remote/recursive work stays unknown."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json

CPP = 'xbmc/video/jobs/VideoLibraryMarkWatchedJob.cpp'
HEADER = 'xbmc/video/jobs/VideoLibraryMarkWatchedJob.h'
PINS = {CPP: '4acc7acb650dca3b5b99c5ff71ee9c76fc7ccadb162f9fc2f0485b32cd8e1e69',
        HEADER: 'be989bc5d0fca626c5c43d2e3ca9273fad6c0e25162ee2f49399bfbecf7d429d'}

CONTRACT = r'''#if defined(TARGET_ANDROID)
bool CVideoLibraryMarkWatchedJob::IsInfinityLocalWatchedJob() const
{
  // Directory/provider recursion and remote recording/server writes have their
  // own contracts. Never classify them by this local SQLite receipt.
  return typeid(*this) == typeid(CVideoLibraryMarkWatchedJob) && m_item &&
      !m_item->m_bIsFolder && !m_item->HasPVRRecordingInfoTag() &&
      !URIUtils::IsUPnP(m_item->GetPath());
}

CJob::CheckpointResponsibility CVideoLibraryMarkWatchedJob::GetCheckpointResponsibility(
    const IJobCallback* callback) const
{
  return IsInfinityLocalWatchedJob() && callback &&
         typeid(*callback) == typeid(CVideoLibraryQueue) ?
      CheckpointResponsibility::Required : CheckpointResponsibility::Unknown;
}

const char* CVideoLibraryMarkWatchedJob::GetCheckpointPersistenceOwner() const
{
  return IsInfinityLocalWatchedJob() ? "native_databases" : "";
}

bool CVideoLibraryMarkWatchedJob::RequiresCheckpointCompletionReceipt() const
{
  return IsInfinityLocalWatchedJob();
}

bool CVideoLibraryMarkWatchedJob::CheckpointSucceeded(bool success) const
{
  if (!IsInfinityLocalWatchedJob())
    return success; // Preserve its operation result; Unknown still blocks retirement.
  return success && m_infinityCompletionVerified &&
      m_infinityDatabaseFailures == InfinityDatabaseBarrier::ThreadFailureSerial();
}

bool CVideoLibraryMarkWatchedJob::DoWork()
{
  m_infinityCompletionVerified = false;
  m_infinityOutcomeReviewed = false;
  m_infinityDurability = CJobDurability::Pending;
  m_infinityDatabaseFailures = InfinityDatabaseBarrier::ThreadFailureSerial();
  InfinityDatabaseBarrier::WriteObservation writes;
  // Includes open, the original Work implementation and database destruction.
  const bool success = CVideoLibraryJob::DoWork();
  m_infinityCompletionVerified = success && IsInfinityLocalWatchedJob() &&
      m_infinityOutcomeReviewed && writes.Durable() &&
      m_infinityDatabaseFailures == InfinityDatabaseBarrier::ThreadFailureSerial();
  JobCheckpoint::WorkResult(CJobManager::CheckpointRecord(this),
      m_infinityCompletionVerified ? m_infinityDurability : CJobDurability::Unresolved,
      success, m_infinityCompletionVerified ? "" : "watched_job_persistence_unverified");
  return success; // Preserve the actual operation result; no fabricated save.
}
#endif

'''

READBACK = r'''  const bool committed = db.CommitTransaction();
  db.Close();
  if (!committed)
    return false;

#if defined(TARGET_ANDROID)
  if (IsInfinityLocalWatchedJob())
  {
    // Verify through a separate database object after the write connection has
    // closed. The native_databases final fence still owns checkpoint durability.
    CVideoDatabase persisted;
    if (!persisted.Open())
      return false;
    bool verified = m_infinityDatabaseFailures == InfinityDatabaseBarrier::ThreadFailureSerial();
    for (const auto& item : markItems)
    {
      const int count = persisted.GetPlayCount(*item);
      if (m_mark ? count <= 0 : count != 0)
        verified = false;
      std::string path(item->GetPath());
      if (item->HasVideoInfoTag() && !item->GetVideoInfoTag()->GetPath().empty())
        path = item->GetVideoInfoTag()->GetPath();
      CBookmark bookmark;
      if (persisted.GetResumeBookMark(path, bookmark))
        verified = false;
    }
    persisted.Close();
    verified = verified &&
        m_infinityDatabaseFailures == InfinityDatabaseBarrier::ThreadFailureSerial();
    if (!verified)
      return false;
    m_infinityOutcomeReviewed = true;
    m_infinityDurability = CJobDurability::VerifiedCommitted;
  }
#endif
  return true;'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Unexpected watched-job preimage: ' + before[:90])
    return text.replace(before, after, 1)


def transform(name, raw):
    if sha(raw) != PINS[name]:
        raise ValueError('Unreviewed watched-job source: ' + name)
    text = raw.decode()
    if name == HEADER:
        text = once(text, '#include "video/jobs/VideoLibraryJob.h"', '''#include "video/jobs/VideoLibraryJob.h"
#if defined(TARGET_ANDROID)
#include "utils/JobCheckpoint.h"
#endif''')
        text = once(text, '  bool operator==(const CJob* job) const override;', '''  bool operator==(const CJob* job) const override;
#if defined(TARGET_ANDROID)
  bool DoWork() override;
  CheckpointResponsibility GetCheckpointResponsibility(const IJobCallback*) const override;
  const char* GetCheckpointPersistenceOwner() const override;
  bool RequiresCheckpointCompletionReceipt() const override;
  bool RequiresCheckpointCallback() const override { return true; }
  bool CheckpointSucceeded(bool success) const override;
#endif''')
        text = once(text, 'private:\n  std::shared_ptr<CFileItem> m_item;', '''private:
#if defined(TARGET_ANDROID)
  bool IsInfinityLocalWatchedJob() const;
  bool m_infinityCompletionVerified{false};
  bool m_infinityOutcomeReviewed{false};
  uint64_t m_infinityDatabaseFailures{0};
  CJobDurability m_infinityDurability{CJobDurability::Pending};
#endif
  std::shared_ptr<CFileItem> m_item;''')
    elif name == CPP:
        text = once(text, '#include "VideoLibraryMarkWatchedJob.h"', '''#include "VideoLibraryMarkWatchedJob.h"
#if defined(TARGET_ANDROID)
#include "dbwrappers/InfinityDatabaseBarrier.h"
#include "utils/JobManager.h"
#include "video/VideoLibraryQueue.h"
#include <cstring>
#include <typeinfo>
#endif''')
        text = once(text, 'bool CVideoLibraryMarkWatchedJob::Work(CVideoDatabase &db)',
                    CONTRACT + 'bool CVideoLibraryMarkWatchedJob::Work(CVideoDatabase &db)')
        text = once(text, '  if (markItems.empty())\n    return true;', '''  if (markItems.empty())
  {
#if defined(TARGET_ANDROID)
    if (IsInfinityLocalWatchedJob())
    {
      m_infinityOutcomeReviewed = true;
      m_infinityDurability = CJobDurability::VerifiedUnchanged;
    }
#endif
    return true;
  }''')
        text = once(text, '  db.BeginTransaction();', '''  db.BeginTransaction();
#if defined(TARGET_ANDROID)
  if (IsInfinityLocalWatchedJob() &&
      m_infinityDatabaseFailures != InfinityDatabaseBarrier::ThreadFailureSerial())
    return false; // Do not run writes outside a failed transaction.
#endif''')
        text = once(text, '  db.CommitTransaction();\n  db.Close();\n\n  return true;', READBACK)
    else:
        raise ValueError('Unauthorized watched-job path')
    return text.encode()


def stage(source, out):
    if out.exists():
        raise ValueError('Refusing to overwrite a staged candidate')
    originals = {name: (source / name).read_bytes() for name in PINS}
    outputs = {name: transform(name, raw) for name, raw in originals.items()}
    out.mkdir(parents=True)
    patch = []
    for name, raw in outputs.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        patch.extend(difflib.unified_diff(originals[name].decode().splitlines(True),
                                        raw.decode().splitlines(True),
                                        fromfile='a/' + name, tofile='b/' + name, n=0))
    proof = {'kind': 'bounded local watched-job persistence receipt, staged only',
             'before': PINS, 'after': {name: sha(raw) for name, raw in outputs.items()},
             'scope': 'exact class, nonrecursive non-PVR/non-UPnP item, exact VideoLibraryQueue callback',
             'unknown_recursive_and_remote_work_remains_blocking': True,
             'checked_commit_and_separate_connection_readback': True,
             'final_native_database_fence_preserved': True,
             'host_verified': False, 'android_verified': False,
             'full_native_source_map_verified': False, 'apk_built_or_signed': False}
    (out / 'SOURCE-DELTA.json').write_text(json.dumps(proof, indent=2) + '\n')
    (out / 'reviewed.patch').write_text(''.join(patch))
    return proof


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(stage(a.source, a.out), indent=2))
