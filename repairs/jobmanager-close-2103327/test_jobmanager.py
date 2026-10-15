#!/usr/bin/env python3
"""Compile the transformed production JobManager with real host threads/locks."""
import argparse
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

JOB_STUB = r'''
#pragma once
class CJob;
class IJobCallback
{
public:
  virtual ~IJobCallback() = default;
  virtual void OnJobComplete(unsigned int, bool, CJob*) = 0;
  virtual void OnJobAbort(unsigned int, CJob*) {}
  virtual void OnJobProgress(unsigned int, unsigned int, unsigned int, const CJob*) {}
};
class CJobManager;
class CJob
{
public:
  enum PRIORITY { PRIORITY_LOW_PAUSABLE=0, PRIORITY_LOW, PRIORITY_NORMAL,
                  PRIORITY_HIGH, PRIORITY_DEDICATED };
  CJob() : m_callback(nullptr) {}
  virtual ~CJob() = default;
  virtual bool DoWork() = 0;
  virtual const char* GetType() const { return ""; }
  virtual bool operator==(const CJob*) const { return false; }
  virtual bool ShouldCancel(unsigned int progress, unsigned int total) const;
private:
  friend class CJobManager;
  CJobManager* m_callback;
};
'''

CRITICAL_STUB = r'''
#pragma once
#include <mutex>
using CCriticalSection = std::recursive_mutex;
'''

THREAD_STUB = r'''
#pragma once
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <mutex>
#include <string>
#include <thread>

enum class ThreadPriority { LOWEST };

class CEvent
{
public:
  void Set()
  {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_signaled = true;
    m_condition.notify_all();
  }
  bool Wait(std::chrono::milliseconds timeout)
  {
    std::unique_lock<std::mutex> lock(m_mutex);
    if (!m_condition.wait_for(lock, timeout, [this] { return m_signaled; }))
      return false;
    m_signaled = false;
    return true;
  }
private:
  std::mutex m_mutex;
  std::condition_variable m_condition;
  bool m_signaled{false};
};

class CThread
{
public:
  explicit CThread(const char* name) : m_name(name != nullptr ? name : "") {}
  virtual ~CThread()
  {
    if (m_thread.joinable())
    {
      if (m_thread.get_id() == std::this_thread::get_id())
        m_thread.detach();
      else
        m_thread.join();
    }
  }
  void Create(bool autoDelete)
  {
    m_autoDelete = autoDelete;
    m_thread = std::thread([this] {
      Process();
      if (m_autoDelete)
        delete this;
    });
  }
  bool IsAutoDelete() const { return m_autoDelete; }
  void StopThread(bool wait = true)
  {
    if (wait && m_thread.joinable() && m_thread.get_id() != std::this_thread::get_id())
      m_thread.join();
  }
  void SetPriority(ThreadPriority) {}
  virtual void Process() = 0;
private:
  std::string m_name;
  std::thread m_thread;
  bool m_autoDelete{false};
};
'''

BROKER_STUB = r'''
#pragma once
class CJobManager;
class CServiceBroker
{
public:
  static CJobManager* GetJobManager();
  static void SetJobManager(CJobManager* manager);
};
'''

LOG_STUB = r'''
#pragma once
constexpr int LOGERROR = 1;
class CLog
{
public:
  template<typename... Args>
  static void Log(int, const char*, Args&&...) {}
};
'''

TRACE_STUB = r'''
#pragma once
#include <mutex>
#include <string>
#include <vector>
namespace InfinityShutdownTrace
{
inline std::mutex mutex;
inline std::vector<std::string> events;
inline void Event(const char*, const char* phase, long long=-1,
                  unsigned long long=0, unsigned long long=0, long long=0,
                  const char* addon=nullptr, const char*="observed", const char*=nullptr) noexcept
{
  std::lock_guard<std::mutex> lock(mutex);
  events.emplace_back(std::string(phase != nullptr ? phase : "") + ":" +
                      std::string(addon != nullptr ? addon : ""));
}
class Scope
{
public:
  Scope(const char* phase, long long=-1, const char* addon=nullptr, const char*=nullptr) noexcept
    : m_phase(phase != nullptr ? phase : ""), m_addon(addon != nullptr ? addon : "")
  {
    std::lock_guard<std::mutex> lock(mutex);
    events.emplace_back("begin:" + m_phase + ":" + m_addon);
  }
  ~Scope() noexcept
  {
    std::lock_guard<std::mutex> lock(mutex);
    events.emplace_back("end:" + m_phase + ":" + m_addon);
  }
private:
  std::string m_phase;
  std::string m_addon;
};
inline bool Has(const std::string& needle)
{
  std::lock_guard<std::mutex> lock(mutex);
  for (const auto& event : events)
    if (event.find(needle) != std::string::npos)
      return true;
  return false;
}
}
'''

TEST_CPP = r'''
#include "JobManager.h"
#include "ServiceBroker.h"
#include "platform/android/activity/InfinityShutdownTrace.h"

#include <atomic>
#include <cassert>
#include <chrono>
#include <thread>

using namespace std::chrono_literals;

namespace
{
CJobManager* g_manager = nullptr;
struct State
{
  std::atomic<bool> started{false};
  std::atomic<bool> cancelled{false};
  std::atomic<int> destroyed{0};
};
class Callback : public IJobCallback
{
public:
  void OnJobComplete(unsigned int, bool, CJob*) override { ++completed; }
  void OnJobAbort(unsigned int, CJob*) override { ++aborted; }
  std::atomic<int> completed{0};
  std::atomic<int> aborted{0};
};
class CooperativeJob : public CJob
{
public:
  explicit CooperativeJob(State& state) : m_state(state) {}
  ~CooperativeJob() override { ++m_state.destroyed; }
  const char* GetType() const override { return "CooperativeJob"; }
  bool DoWork() override
  {
    m_state.started = true;
    while (!ShouldCancel(0, 1))
      std::this_thread::sleep_for(2ms);
    m_state.cancelled = true;
    return false;
  }
private:
  State& m_state;
};
class SlowUncooperativeJob : public CJob
{
public:
  explicit SlowUncooperativeJob(State& state) : m_state(state) {}
  ~SlowUncooperativeJob() override { ++m_state.destroyed; }
  const char* GetType() const override { return "SlowUncooperativeJob"; }
  bool DoWork() override
  {
    m_state.started = true;
    std::this_thread::sleep_for(320ms);
    return true;
  }
private:
  State& m_state;
};
class NeverStartedJob : public CJob
{
public:
  explicit NeverStartedJob(State& state) : m_state(state) {}
  ~NeverStartedJob() override { ++m_state.destroyed; }
  const char* GetType() const override { return "NeverStartedJob"; }
  bool DoWork() override { m_state.started = true; return true; }
private:
  State& m_state;
};
void waitStarted(const State& state)
{
  const auto deadline = std::chrono::steady_clock::now() + 2s;
  while (!state.started.load())
  {
    assert(std::chrono::steady_clock::now() < deadline);
    std::this_thread::sleep_for(1ms);
  }
}
}

CJobManager* CServiceBroker::GetJobManager() { return g_manager; }
void CServiceBroker::SetJobManager(CJobManager* manager) { g_manager = manager; }

int main()
{
  CJobManager manager;
  CServiceBroker::SetJobManager(&manager);
  Callback callback;
  State cooperative;
  State slow;

  assert(manager.AddJob(new CooperativeJob(cooperative), &callback, CJob::PRIORITY_DEDICATED) != 0);
  assert(manager.AddJob(new SlowUncooperativeJob(slow), &callback, CJob::PRIORITY_DEDICATED) != 0);
  waitStarted(cooperative);
  waitStarted(slow);

  const auto begin = std::chrono::steady_clock::now();
  manager.BeginShutdown();
  const auto beginElapsed = std::chrono::steady_clock::now() - begin;
  assert(beginElapsed < 100ms);

  // Repetition is idempotent and cannot extend or restart shutdown.
  manager.BeginShutdown();
  assert(callback.aborted == 2);

  State rejected;
  assert(manager.AddJob(new NeverStartedJob(rejected), &callback, CJob::PRIORITY_NORMAL) == 0);
  assert(!rejected.started);
  assert(rejected.destroyed == 1);

  const auto finalJoin = std::chrono::steady_clock::now();
  manager.CancelJobs();
  const auto joinElapsed = std::chrono::steady_clock::now() - finalJoin;

  // Cooperative work observes cancellation; non-cooperative work is still joined,
  // proving there is no detach, fake completion or force-stop shortcut.
  assert(cooperative.cancelled);
  assert(cooperative.destroyed == 1);
  assert(slow.destroyed == 1);
  assert(joinElapsed >= 180ms);
  assert(callback.completed == 0);
  assert(callback.aborted == 2);

  assert(InfinityShutdownTrace::Has("jobs.worker_execute:CooperativeJob"));
  assert(InfinityShutdownTrace::Has("jobs.worker_execute:SlowUncooperativeJob"));
  assert(InfinityShutdownTrace::Has("jobs.cancel_active:CooperativeJob"));
  assert(InfinityShutdownTrace::Has("jobs.cancel_active:SlowUncooperativeJob"));
  assert(InfinityShutdownTrace::Has("jobs.waiting_active:SlowUncooperativeJob"));
  assert(InfinityShutdownTrace::Has("jobs.cancel_complete"));
  return 0;
}
'''


def run(source: Path) -> None:
    job_cpp = source / 'xbmc/utils/JobManager.cpp'
    job_h = source / 'xbmc/utils/JobManager.h'
    app = (source / 'xbmc/application/Application.cpp').read_text()
    trace = (source / 'xbmc/platform/android/activity/InfinityShutdownTrace.h').read_text()

    assert 'void CJobManager::BeginShutdown()' in job_cpp.read_text()
    assert 'jobs.worker_execute' in job_cpp.read_text()
    assert 'jobs.cancel_active' in job_cpp.read_text()
    assert 'jobs.waiting_active' in job_cpp.read_text()
    assert 'jobs.cancel_complete' in job_cpp.read_text()
    assert 'while (!m_workers.empty())' in job_cpp.read_text()
    assert 'detach' not in job_cpp.read_text()
    assert 'kill' not in job_cpp.read_text().lower()
    assert 'infinity-shutdown-2103327-v1' in trace
    assert 'std::strncmp(phase,"jobs.",5)==0' in trace

    pre_start = app.index('void CApplication::PrepareAndroidShutdownScripts(int exitCode)')
    pre_end = app.index('bool CApplication::Stop(int exitCode)', pre_start)
    pre = app[pre_start:pre_end]
    assert pre.count('GetJobManager()->BeginShutdown()') == 1
    assert pre.index('GetSettings()->Save()') < pre.index('GetJobManager()->BeginShutdown()')
    assert pre.index('g_SkinInfo->SaveSettings()') < pre.index('GetJobManager()->BeginShutdown()')
    assert pre.index('GetJobManager()->BeginShutdown()') < pre.index('GetServiceAddons().Stop()')

    with tempfile.TemporaryDirectory(prefix='infinity-jobmanager-') as tmp_name:
        tmp = Path(tmp_name)
        (tmp / 'threads').mkdir()
        (tmp / 'utils').mkdir()
        (tmp / 'platform/android/activity').mkdir(parents=True)
        (tmp / 'JobManager.cpp').write_text(job_cpp.read_text())
        (tmp / 'JobManager.h').write_text(job_h.read_text())
        (tmp / 'Job.h').write_text(JOB_STUB)
        (tmp / 'threads/CriticalSection.h').write_text(CRITICAL_STUB)
        (tmp / 'threads/Thread.h').write_text(THREAD_STUB)
        (tmp / 'ServiceBroker.h').write_text(BROKER_STUB)
        (tmp / 'utils/XTimeUtils.h').write_text('#pragma once\n')
        (tmp / 'utils/log.h').write_text(LOG_STUB)
        (tmp / 'platform/android/activity/InfinityShutdownTrace.h').write_text(TRACE_STUB)
        (tmp / 'test.cpp').write_text(TEST_CPP)
        binary = tmp / 'jobmanager_test'
        subprocess.run([
            'g++', '-std=c++17', '-pthread', '-DTARGET_ANDROID',
            '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
            '-I' + str(tmp), str(tmp / 'JobManager.cpp'), str(tmp / 'test.cpp'),
            '-o', str(binary)
        ], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    run(parser.parse_args().source)
    print('PASS: production JobManager begins cancellation early, reports exact active jobs, and preserves the final worker join')
