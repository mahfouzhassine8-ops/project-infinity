#include "../prototype/owned_lookup.h"
#include <jni.h>
#include <dlfcn.h>
#include <chrono>
#include <cstring>
#include <netdb.h>
#include <sstream>
#include <thread>
#include <unistd.h>
#include <dirent.h>
#include <fstream>
#include <sys/resource.h>
#include <sys/syscall.h>

static int RemainingChildren()
{
  std::ifstream in("/proc/self/task/" + std::to_string(syscall(SYS_gettid)) + "/children");
  if (!in) return -1;
  int count = 0;
  std::string child;
  while (in >> child) ++count;
  return count;
}

static int ThreadCount()
{
  DIR* dir = opendir("/proc/self/task");
  if (!dir) return -1;
  int count = 0;
  while (auto* entry = readdir(dir))
    if (entry->d_name[0] != '.') ++count;
  closedir(dir);
  return count;
}

static unsigned FdCount()
{
  DIR* dir = opendir("/proc/self/fd");
  if (!dir) return 1000000;
  unsigned count = 0;
  while (readdir(dir)) ++count;
  closedir(dir);
  return count;
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_projectinfinity_dnsprobe_ProbeActivity_runNative(JNIEnv* env, jclass,
    jstring javaPath, jint cancellationMs, jint repetitions)
{
  const char* raw = env->GetStringUTFChars(javaPath, nullptr);
  const std::string path(raw);
  env->ReleaseStringUTFChars(javaPath, raw);
  typedef int (*Getter)(uint64_t*);
  const auto getProcess = reinterpret_cast<Getter>(dlsym(RTLD_DEFAULT, "android_getprocnetwork"));
  const auto getDns = reinterpret_cast<Getter>(dlsym(RTLD_DEFAULT, "android_getprocdns"));
  std::ostringstream out; out << '[';
  for (int i = 0; i < repetitions; ++i) {
    if (i) out << ',';
    uint64_t process = 0, dns = 0;
    const bool bindingRead = getProcess && getDns && !getProcess(&process) && !getDns(&dns);
    dns_request request{};
    request.magic = DNS_MAGIC; request.family = AF_UNSPEC; request.socktype = SOCK_STREAM;
    // Android's explicit process binding takes precedence over DNS binding.
    request.network = process ? process : dns;
    std::strcpy(request.hostname, "localhost"); std::strcpy(request.service, "443");
    std::atomic<bool> cancelled{false};
    const unsigned initialFds = FdCount();
    std::thread cancellation;
    if (cancellationMs >= 0)
      cancellation = std::thread([&] {
        std::this_thread::sleep_for(std::chrono::milliseconds(cancellationMs)); cancelled = true;
      });
    auto begin = std::chrono::steady_clock::now();
    DnsResult result;
    if (bindingRead) result = OwnedLookup(path, request, 2000, &cancelled);
    else result.outcome = DnsOutcome::Unsupported;
    double wall = std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
    if (cancellation.joinable()) cancellation.join();
    const unsigned finalFds = FdCount();
    rusage usage{};
    const bool memoryRead = getrusage(RUSAGE_SELF, &usage) == 0;
    out << "{\"outcome\":" << static_cast<int>(result.outcome)
        << ",\"gai_error\":" << result.reply.gai_error
        << ",\"system_errno\":" << result.reply.system_errno
        << ",\"addresses\":" << result.reply.count
        << ",\"postexec_extra_fds\":" << result.reply.extra_fds
        << ",\"preexec_extra_fds\":" << result.preexec_extra_fds
        << ",\"runtime_fd_kind_bits\":" << result.reply.runtime_fd_kinds
        << ",\"binding_read\":" << (bindingRead ? "true" : "false")
        << ",\"explicit_binding\":" << (request.network ? "true" : "false")
        << ",\"caller_seconds\":" << wall
        << ",\"return_seconds\":" << result.return_seconds
        << ",\"cleanup_seconds\":" << result.cleanup_seconds
        << ",\"child_code\":" << result.child_code
        << ",\"child_status\":" << result.child_status
        << ",\"fd_difference\":" << static_cast<int>(finalFds) - static_cast<int>(initialFds)
        << ",\"parent_fd_count\":" << finalFds
        << ",\"parent_thread_count\":" << ThreadCount()
        << ",\"remaining_children\":" << RemainingChildren()
        << ",\"max_rss_kb\":" << (memoryRead ? usage.ru_maxrss : -1)
        << ",\"wait_error\":" << result.wait_error << '}';
  }
  out << ']';
  return env->NewStringUTF(out.str().c_str());
}
