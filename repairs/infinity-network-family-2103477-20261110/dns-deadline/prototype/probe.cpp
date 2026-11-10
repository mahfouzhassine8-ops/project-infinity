#include "owned_lookup.h"
#include <chrono>
#include <cstring>
#include <dirent.h>
#include <fcntl.h>
#include <iostream>
#include <netdb.h>
#include <fstream>
#include <sstream>
#include <sys/resource.h>
#include <thread>
#include <unistd.h>

static unsigned Fds()
{
  DIR* dir = opendir("/proc/self/fd");
  if (!dir) return 1000000;
  unsigned count = 0;
  while (readdir(dir)) ++count;
  closedir(dir);
  return count;
}
int main(int argc, char** argv)
{
  if (argc != 5 && argc != 6) return 2;
  const int repetitions = std::stoi(argv[2]);
  const int cancelMs = std::stoi(argv[3]);
  const int deadlineMs = std::stoi(argv[4]);
  dns_request request{};
  request.magic = DNS_MAGIC; request.family = AF_UNSPEC; request.socktype = SOCK_STREAM;
  request.flags = AI_CANONNAME;
  const std::string name = argc == 6 ? argv[5] : "localhost";
  if (name.size() >= sizeof(request.hostname)) return 3;
  std::strcpy(request.hostname, name.c_str()); std::strcpy(request.service, "443");
  // Deliberately non-CLOEXEC: the helper must not inherit this unrelated FD.
  const int sentinel = open("/dev/null", O_RDONLY);
  const auto initialFds = Fds();
  for (int index = 0; index < repetitions; ++index) {
    std::atomic<bool> cancelled{false};
    std::thread canceller;
    if (cancelMs >= 0)
      canceller = std::thread([&] {
        std::this_thread::sleep_for(std::chrono::milliseconds(cancelMs)); cancelled = true;
      });
    const auto began = std::chrono::steady_clock::now();
    const auto result = OwnedLookup(argv[1], request, deadlineMs, &cancelled);
    const double caller = std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count();
    if (canceller.joinable()) canceller.join();
    const auto currentFds = Fds();
    rusage usage{};
    getrusage(RUSAGE_SELF, &usage);
    std::ifstream children("/proc/self/task/" + std::to_string(getpid()) + "/children");
    unsigned childCount = 0;
    std::string child;
    while (children >> child) ++childCount;
    children.close();
    std::cout << "{\"outcome\":" << static_cast<int>(result.outcome)
              << ",\"gai_error\":" << result.reply.gai_error
              << ",\"addresses\":" << result.reply.count
              << ",\"inherited_extra_fds\":" << result.reply.extra_fds
              << ",\"preexec_extra_fds\":" << result.preexec_extra_fds
              << ",\"runtime_fd_kind_bits\":" << result.reply.runtime_fd_kinds
              << ",\"caller_seconds\":" << caller
              << ",\"return_seconds\":" << result.return_seconds
              << ",\"cleanup_seconds\":" << result.cleanup_seconds
              << ",\"spawn_seconds\":" << result.spawn_seconds
              << ",\"fd_growth\":" << static_cast<int>(currentFds)-static_cast<int>(initialFds)
              << ",\"remaining_children\":" << childCount
              << ",\"max_rss_kb\":" << usage.ru_maxrss
              << ",\"system_errno\":" << result.reply.system_errno
              << ",\"child_code\":" << result.child_code
              << ",\"child_status\":" << result.child_status
              << ",\"wait_error\":" << result.wait_error << "}\n";
  }
  if (sentinel >= 0) close(sentinel);
}
