#!/usr/bin/env python3
"""Early cooperative JobManager shutdown + exact active-job evidence on 2103326."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json

JOB_CPP = 'xbmc/utils/JobManager.cpp'
JOB_H = 'xbmc/utils/JobManager.h'
APP = 'xbmc/application/Application.cpp'
TRACE = 'xbmc/platform/android/activity/InfinityShutdownTrace.h'
ALLOWED = {JOB_CPP, JOB_H, APP, TRACE}
PARENT_MAP = '14f8672c1eb7ed8ad14cc8f244a47c08ae596df9418eee6c0d85484cd3324193'
PREIMAGES = {
    JOB_CPP: 'f9e8beaed5217578c9e48b0d7e48e28f16c29216eac4ec3c9f955f36551b7f55',
    JOB_H: 'f47e34da97b3a6d5717d1fd1504432bceecfa9c012c4cf0f3ea33901cd6d096c',
    APP: '747d8701b76006bbfecc80f9aa239e1c5eecfebb63c0fe15cd092962b8868d41',
    TRACE: '44774b6d08fe8656cf7fffcb0c98471eb1d85c323d34dfc49b5d8be8841947d8',
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): sha(p.read_bytes())
        for p in root.rglob('*')
        if p.is_file() and '.git' not in p.relative_to(root).parts
    }


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f'Unreviewed preimage ({text.count(old)} matches): {old[:120]}')
    return text.replace(old, new, 1)


def function(text: str, signature: str) -> tuple[int, int, str]:
    start = text.index(signature)
    body_start = text.index('{', start)
    depth = 1
    index = body_start + 1
    while depth:
        if text[index] == '{':
            depth += 1
        elif text[index] == '}':
            depth -= 1
        index += 1
    return start, index, text[start:index]


def transform_header(text: str) -> str:
    text = once(text, '  void CancelJobs();\n',
                '  void BeginShutdown();\n  void CancelJobs();\n')
    return once(text, '  CJob *PopJob();\n',
                '  unsigned int GetJobId(const CJob* job) const;\n\n  CJob *PopJob();\n')


def transform_cpp(text: str) -> str:
    text = once(text, '#include "JobManager.h"\n',
                '#include "JobManager.h"\n\n#if defined(TARGET_ANDROID)\n'
                '#include "platform/android/activity/InfinityShutdownTrace.h"\n#endif\n')

    old_worker = '''    bool success = false;
    try
    {
      success = job->DoWork();
    }
    catch (...)
    {
      CLog::Log(LOGERROR, "{} error processing job {}", __FUNCTION__, job->GetType());
    }
    m_jobManager->OnJobComplete(success, job);
'''
    new_worker = '''    const unsigned int jobId = m_jobManager->GetJobId(job);
    const char* rawJobType = job->GetType();
    const std::string jobType = rawJobType != nullptr ? rawJobType : "";
#if defined(TARGET_ANDROID)
    InfinityShutdownTrace::Scope jobEvidence("jobs.worker_execute", jobId, jobType.c_str());
#endif
    bool success = false;
    try
    {
      success = job->DoWork();
    }
    catch (...)
    {
      CLog::Log(LOGERROR, "{} error processing job {}", __FUNCTION__, jobType);
    }
    m_jobManager->OnJobComplete(success, job);
'''
    text = once(text, old_worker, new_worker)

    old_cancel = '''void CJobManager::CancelJobs()
{
  std::unique_lock<CCriticalSection> lock(m_section);
  m_running = false;

  // clear any pending jobs
  for (unsigned int priority = CJob::PRIORITY_LOW_PAUSABLE; priority <= CJob::PRIORITY_DEDICATED; ++priority)
  {
    std::for_each(m_jobQueue[priority].begin(), m_jobQueue[priority].end(), [](CWorkItem& wi) {
      if (wi.m_callback)
        wi.m_callback->OnJobAbort(wi.m_id, wi.m_job);
      wi.FreeJob();
    });
    m_jobQueue[priority].clear();
  }

  // cancel any callbacks on jobs still processing
  std::for_each(m_processing.begin(), m_processing.end(), [](CWorkItem& wi) {
    if (wi.m_callback)
      wi.m_callback->OnJobAbort(wi.m_id, wi.m_job);
    wi.Cancel();
  });

  // tell our workers to finish
  while (m_workers.size())
  {
    lock.unlock();
    m_jobEvent.Set();
    std::this_thread::yield(); // yield after setting the event to give the workers some time to die
    lock.lock();
  }
}
'''
    new_cancel = '''unsigned int CJobManager::GetJobId(const CJob* job) const
{
  std::unique_lock<CCriticalSection> lock(m_section);
  const auto it = std::find(m_processing.begin(), m_processing.end(), job);
  return it != m_processing.end() ? it->m_id : 0;
}

void CJobManager::BeginShutdown()
{
  std::unique_lock<CCriticalSection> lock(m_section);
  if (!m_running)
  {
#if defined(TARGET_ANDROID)
    InfinityShutdownTrace::Event("milestone", "jobs.begin_shutdown_repeat",
                                 static_cast<long long>(m_processing.size()));
#endif
    m_jobEvent.Set();
    return;
  }

  m_running = false;
#if defined(TARGET_ANDROID)
  InfinityShutdownTrace::Event("milestone", "jobs.begin_shutdown",
                               static_cast<long long>(m_processing.size()));
#endif

  // Reject new jobs and release work that has not started. Preserve the existing
  // OnJobAbort contract before deleting queued jobs.
  for (unsigned int priority = CJob::PRIORITY_LOW_PAUSABLE;
       priority <= CJob::PRIORITY_DEDICATED; ++priority)
  {
    for (CWorkItem& wi : m_jobQueue[priority])
    {
#if defined(TARGET_ANDROID)
      InfinityShutdownTrace::Event("milestone", "jobs.cancel_queued", wi.m_id,
                                   0, 0, 0,
                                   wi.m_job != nullptr ? wi.m_job->GetType() : nullptr);
#endif
      if (wi.m_callback)
        wi.m_callback->OnJobAbort(wi.m_id, wi.m_job);
      wi.FreeJob();
    }
    m_jobQueue[priority].clear();
  }

  // Jobs already inside DoWork keep their worker and object alive. Remove their
  // client callbacks so ShouldCancel() observes cancellation, but do not detach,
  // delete, force-stop or pretend that the worker completed.
  for (CWorkItem& wi : m_processing)
  {
#if defined(TARGET_ANDROID)
    InfinityShutdownTrace::Event("milestone", "jobs.cancel_active", wi.m_id,
                                 0, 0, 0,
                                 wi.m_job != nullptr ? wi.m_job->GetType() : nullptr);
#endif
    if (wi.m_callback)
      wi.m_callback->OnJobAbort(wi.m_id, wi.m_job);
    wi.Cancel();
  }

  m_jobEvent.Set();
}

void CJobManager::CancelJobs()
{
  // Normal Android close calls BeginShutdown during the cooperative pre-destroy
  // window. This repeat is intentional and keeps the ordinary Kodi contract for
  // every other route while preserving the final worker join below.
  BeginShutdown();

  std::unique_lock<CCriticalSection> lock(m_section);
  auto nextEvidence = std::chrono::steady_clock::now();

  // Final teardown still waits for every JobWorker. Periodic records identify
  // the exact job ID/type and worker TID if a non-cooperative job holds this join.
  while (!m_workers.empty())
  {
#if defined(TARGET_ANDROID)
    const auto now = std::chrono::steady_clock::now();
    if (now >= nextEvidence)
    {
      InfinityShutdownTrace::Event("milestone", "jobs.waiting_workers",
                                   static_cast<long long>(m_workers.size()));
      for (const CWorkItem& wi : m_processing)
      {
        InfinityShutdownTrace::Event("milestone", "jobs.waiting_active", wi.m_id,
                                     0, 0, 0,
                                     wi.m_job != nullptr ? wi.m_job->GetType() : nullptr);
      }
      nextEvidence = now + std::chrono::seconds(1);
    }
#endif
    lock.unlock();
    m_jobEvent.Set();
    std::this_thread::yield();
    lock.lock();
  }

#if defined(TARGET_ANDROID)
  InfinityShutdownTrace::Event("milestone", "jobs.cancel_complete");
#endif
}
'''
    text = once(text, old_cancel, new_cancel)

    old_remove = '''  if (i != m_workers.end())
    m_workers.erase(i); // workers auto-delete
'''
    new_remove = '''  if (i != m_workers.end())
  {
#if defined(TARGET_ANDROID)
    InfinityShutdownTrace::Event("milestone", "jobs.worker_removed",
                                 static_cast<long long>(m_workers.size()));
#endif
    m_workers.erase(i); // workers auto-delete
  }
'''
    return once(text, old_remove, new_remove)


def transform_application(text: str) -> str:
    start, end, body = function(text, 'void CApplication::PrepareAndroidShutdownScripts(int exitCode)')
    anchor = '''#ifdef HAS_PYTHON
  CServiceBroker::GetXBPython().BeginShutdown();
#endif
'''
    addition = anchor + '''  {
    InfinityShutdownTrace::Scope evidence("pre.begin_job_shutdown");
    CServiceBroker::GetJobManager()->BeginShutdown();
  }
'''
    if body.count(anchor) != 1:
        raise ValueError('Unexpected cooperative pre-destroy JobManager anchor')
    body = body.replace(anchor, addition, 1)
    text = text[:start] + body + text[end:]

    start, end, body = function(text, 'bool CApplication::Stop(int exitCode)')
    anchor = '''#if defined(TARGET_ANDROID) && defined(HAS_PYTHON)
    CServiceBroker::GetXBPython().BeginShutdown();
#endif
    m_bStop = true;
'''
    addition = '''#if defined(TARGET_ANDROID) && defined(HAS_PYTHON)
    CServiceBroker::GetXBPython().BeginShutdown();
#endif
#if defined(TARGET_ANDROID)
    {
      InfinityShutdownTrace::Scope evidence("stop.begin_job_shutdown");
      CServiceBroker::GetJobManager()->BeginShutdown();
    }
#endif
    m_bStop = true;
'''
    if body.count(anchor) != 1:
        raise ValueError('Unexpected final-stop JobManager anchor')
    body = body.replace(anchor, addition, 1)
    return text[:start] + body + text[end:]


def transform_trace(text: str) -> str:
    text = once(text, 'infinity-shutdown-2103326-v1', 'infinity-shutdown-2103327-v1')
    return once(text,
                'std::strncmp(phase,"capture.",8)==0);',
                'std::strncmp(phase,"capture.",8)==0 || '
                'std::strncmp(phase,"jobs.",5)==0);')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()

    expected = json.loads(args.proof.read_text())['after']
    before = snapshot(args.source)
    if before != expected:
        raise ValueError('Not exact passed 2103326 native source')
    if sha(json.dumps(before, sort_keys=True, separators=(',', ':')).encode()) != PARENT_MAP:
        raise ValueError('Wrong complete 2103326 native source map')
    for name, digest in PREIMAGES.items():
        if before.get(name) != digest:
            raise ValueError('Unexpected 2103326 preimage: ' + name)

    original = {name: (args.source / name).read_text() for name in ALLOWED}
    (args.source / JOB_H).write_text(transform_header(original[JOB_H]))
    (args.source / JOB_CPP).write_text(transform_cpp(original[JOB_CPP]))
    (args.source / APP).write_text(transform_application(original[APP]))
    (args.source / TRACE).write_text(transform_trace(original[TRACE]))

    after = snapshot(args.source)
    changed = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
    if changed != ALLOWED or before.keys() != after.keys():
        raise ValueError('Undeclared JobManager repair delta: ' + repr(sorted(changed)))

    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        'candidate': 2103327,
        'apk_parent': 2103326,
        'locked_rollback': 2103324,
        'kind': 'native',
        'before': before,
        'after': after,
        'changed': sorted(changed),
        'early_job_cancellation': True,
        'final_worker_join_preserved': True,
        'worker_force_stop_added': False,
        'physical_device_verified': False,
        'locked': False,
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    (args.receipt.parent / 'native-reviewed.patch').write_text(''.join(
        ''.join(difflib.unified_diff(
            original[name].splitlines(True),
            (args.source / name).read_text().splitlines(True),
            fromfile='a/' + name,
            tofile='b/' + name))
        for name in sorted(changed)))
    print('PASS: exact 2103326 native parent; early JobManager cancellation, exact active-job evidence, final join preserved')


if __name__ == '__main__':
    main()
