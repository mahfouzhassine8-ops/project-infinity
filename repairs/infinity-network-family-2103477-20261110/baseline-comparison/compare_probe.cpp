// Controlled host comparison; this does not execute an Android application.
#include "DllLibCurl.h"
#ifndef INFINITY_COMPARE_BASELINE
#include "InfinityNetworkFamily.h"
#endif
#include <chrono>
#include <dirent.h>
#include <iostream>
#include <string>
#include <unistd.h>

XCURL::DllLibCurlGlobal g_curlInterface;
using Clock = std::chrono::steady_clock;
struct Progress { Clock::time_point began; double firstAbort = -1; };
static int Abort(void* opaque, curl_off_t, curl_off_t, curl_off_t, curl_off_t)
{
  auto& p = *static_cast<Progress*>(opaque);
  const double elapsed = std::chrono::duration<double>(Clock::now()-p.began).count();
  if (elapsed < .150) return 0;
  if (p.firstAbort < 0) p.firstAbort = elapsed;
  return 1;
}
static int Fds()
{
  DIR* d = opendir("/proc/self/fd");
  if (!d) return -1;
  int count = 0;
  while (readdir(d)) ++count;
  closedir(d); return count;
}
int main(int argc, char** argv)
{
  if (argc != 2) return 2;
  const auto* version = curl_version_info(CURLVERSION_NOW);
  if (version->version_num != 0x080a00 || !(version->features & CURL_VERSION_ASYNCHDNS))
    return 3;
  CURL_HANDLE* easy = nullptr; CURLM* multi = nullptr;
  g_curlInterface.easy_acquire("http", "infinity-compare.invalid", &easy, &multi);
  g_curlInterface.easy_setopt(easy, CURLOPT_NOSIGNAL, 1L);
  g_curlInterface.easy_setopt(easy, CURLOPT_CONNECTTIMEOUT_MS, 2000L);
  g_curlInterface.easy_setopt(easy, CURLOPT_TIMEOUT_MS, 3500L);
#ifndef INFINITY_COMPARE_BASELINE
  int mode = InfinityNetworkFamily::Automatic;
  const bool changed = g_curlInterface.easy_network_family(easy, mode);
  if (!InfinityNetworkFamily::Configure([&](auto o, auto v) {
        return g_curlInterface.easy_setopt(easy,o,v);
      }, mode, 2000L, changed)) return 4;
#endif
  g_curlInterface.easy_setopt(easy, CURLOPT_PROXY, "");
  g_curlInterface.easy_setopt(easy, CURLOPT_NOPROXY, "*");
  g_curlInterface.easy_setopt(easy, CURLOPT_URL, "http://infinity-compare.invalid/");
  Progress progress{Clock::now()};
  if (std::string(argv[1]) == "cancel") {
    g_curlInterface.easy_setopt(easy, CURLOPT_XFERINFOFUNCTION, Abort);
    g_curlInterface.easy_setopt(easy, CURLOPT_XFERINFODATA, &progress);
    g_curlInterface.easy_setopt(easy, CURLOPT_NOPROGRESS, 0L);
  }
  const auto began = Clock::now();
  const int initialFds = Fds();
  const CURLcode result = g_curlInterface.easy_perform(easy);
  const auto returned = Clock::now();
  curl_off_t curlTime = 0;
  g_curlInterface.easy_getinfo(easy, CURLINFO_TOTAL_TIME_T, &curlTime);
  g_curlInterface.easy_release(&easy, &multi);
  const auto released = Clock::now();
  std::cout << "{\"result\":" << result
            << ",\"perform_seconds\":" << std::chrono::duration<double>(returned-began).count()
            << ",\"release_seconds\":" << std::chrono::duration<double>(released-returned).count()
            << ",\"caller_seconds\":" << std::chrono::duration<double>(released-began).count()
            << ",\"curl_reported_seconds\":" << curlTime/1000000.0
            << ",\"first_progress_abort_seconds\":" << progress.firstAbort
            << ",\"fd_difference\":" << Fds()-initialFds << "}\n";
}
