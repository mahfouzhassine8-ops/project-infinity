// HOST TEST DOUBLE. Uses a real std::thread and join, not Kodi's CThread.
#pragma once
#include <atomic>
#include <condition_variable>
#include <mutex>
#include <thread>
class CThread {
public:
  explicit CThread(const char*) {}
  virtual ~CThread() { if (worker.joinable()) worker.join(); }
  bool IsRunning() const { return running.load(); }
  void Create() {
    running=true;
    worker=std::thread([this] {
      try { OnStartup(); Process(); OnExit(); }
      catch (...) { OnException(); }
      running=false;
    });
  }
  void StopThread(bool wait) { if (wait && worker.joinable()) worker.join(); }
protected:
  virtual void OnStartup() {}
  virtual void Process() {}
  virtual void OnExit() {}
  virtual void OnException() {}
  std::atomic<bool> m_bStop{false};
private:
  std::atomic<bool> running{false};
  std::thread worker;
};
