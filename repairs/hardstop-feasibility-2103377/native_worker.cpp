// Disposable native POSIX thread-signal feasibility test.
// No Kodi code or user data is modified.
#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <pthread.h>
#include <thread>

int main(int argc, char** argv) {
  if (argc != 2) return 3;
  const std::string mode = argv[1];
  std::atomic<bool> ready{false};
  std::thread simulated_python_invoker([&] {
    ready.store(true, std::memory_order_release);
    if (mode == "abort_from_worker") std::abort();
    while (true) std::this_thread::sleep_for(std::chrono::milliseconds(40));
  });
  for (int i = 0; i < 100 && !ready.load(std::memory_order_acquire); ++i)
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
  if (!ready.load(std::memory_order_acquire)) return 4;
  std::cout << "worker_started" << std::endl;
  if (mode == "term_worker") {
    int code = pthread_kill(simulated_python_invoker.native_handle(), SIGTERM);
    if (code) {
      std::cerr << "pthread_kill_failed: " << std::strerror(code) << std::endl;
      return 5;
    }
  } else if (mode != "abort_from_worker") return 6;
  std::this_thread::sleep_for(std::chrono::seconds(2));
  std::cout << "ERROR_process_survived_fatal_worker_operation" << std::endl;
  std::quick_exit(7);
}
