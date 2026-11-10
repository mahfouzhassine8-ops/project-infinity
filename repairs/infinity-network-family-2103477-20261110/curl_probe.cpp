// Focused real-transport harness; compiles the production policy and original pool.
#include "native/xbmc/filesystem/DllLibCurl.h"
#include "native/xbmc/filesystem/InfinityNetworkFamily.h"
#include <chrono>
#include <iostream>
#include <sstream>

XCURL::DllLibCurlGlobal g_curlInterface;
static size_t Write(char* data, size_t size, size_t count, void* out)
{
  static_cast<std::string*>(out)->append(data, size * count);
  return size * count;
}
static int Cancel(void* start, curl_off_t, curl_off_t, curl_off_t, curl_off_t)
{
  return std::chrono::steady_clock::now() -
         *static_cast<std::chrono::steady_clock::time_point*>(start) >
         std::chrono::milliseconds(150);
}
int main(int argc, char** argv)
{
  if (argc != 8) return 2;
  std::stringstream modes(argv[1]);
  std::string part;
  while (std::getline(modes, part, ','))
  {
    int mode = std::stoi(part);
    CURL_HANDLE* easy = nullptr;
    CURLM* multi = nullptr;
    g_curlInterface.easy_acquire("http", "network.test", &easy, &multi);
    bool fresh = g_curlInterface.easy_network_family(easy, mode);
    bool ready = InfinityNetworkFamily::Configure(
        [easy](auto option, auto value) {
          return g_curlInterface.easy_setopt(easy, option, value);
        }, mode, 2000L, fresh);
    if (!ready) return 3;
    std::string body;
    auto start = std::chrono::steady_clock::now();
    g_curlInterface.easy_setopt(easy, CURLOPT_URL, argv[2]);
    g_curlInterface.easy_setopt(easy, CURLOPT_PROXY, argv[5]);
    g_curlInterface.easy_setopt(easy, CURLOPT_NOPROXY, "");
    g_curlInterface.easy_setopt(easy, CURLOPT_COOKIEFILE, "");
    g_curlInterface.easy_setopt(easy, CURLOPT_FOLLOWLOCATION, 1L);
    g_curlInterface.easy_setopt(easy, CURLOPT_MAXREDIRS, 5L);
    g_curlInterface.easy_setopt(easy, CURLOPT_FAILONERROR, 1L);
    g_curlInterface.easy_setopt(easy, CURLOPT_TIMEOUT_MS, 3500L);
    g_curlInterface.easy_setopt(easy, CURLOPT_WRITEFUNCTION, Write);
    g_curlInterface.easy_setopt(easy, CURLOPT_WRITEDATA, &body);
    g_curlInterface.easy_setopt(easy, CURLOPT_HTTPHEADER, nullptr);
    if (*argv[4]) g_curlInterface.easy_setopt(easy, CURLOPT_CAINFO, argv[4]);
    curl_slist* resolve = nullptr;
    if (*argv[3])
    {
      resolve = g_curlInterface.slist_append(resolve, argv[3]);
      g_curlInterface.easy_setopt(easy, CURLOPT_RESOLVE, resolve);
    }
    if (std::string(argv[6]) == "cancel")
    {
      g_curlInterface.easy_setopt(easy, CURLOPT_XFERINFOFUNCTION, Cancel);
      g_curlInterface.easy_setopt(easy, CURLOPT_XFERINFODATA, &start);
      g_curlInterface.easy_setopt(easy, CURLOPT_NOPROGRESS, 0L);
    }
    CURLcode result = g_curlInterface.easy_perform(easy);
    char* ip = nullptr;
    g_curlInterface.easy_getinfo(easy, CURLINFO_PRIMARY_IP, &ip);
    double elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    bool cookie = body.find("cookie=probe=kept") != std::string::npos;
    std::cout << "{\"mode\":" << mode << ",\"result\":" << result
              << ",\"family\":" << (!ip || !*ip ? 0 : std::string(ip).find(':') == std::string::npos ? 4 : 6)
              << ",\"elapsed\":" << elapsed << ",\"cookie\":" << (cookie?"true":"false")
              << ",\"fresh\":" << (fresh?"true":"false") << "}\n";
    g_curlInterface.easy_release(&easy, &multi);
    if (resolve) g_curlInterface.slist_free_all(resolve);
  }
}
