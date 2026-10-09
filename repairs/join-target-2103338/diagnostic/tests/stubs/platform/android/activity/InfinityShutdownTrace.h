// HOST TEST DOUBLE. Captures rows in memory; NOT the production trace writer.
#pragma once
#include <cerrno>
#include <functional>
#include <mutex>
#include <string>
#include <vector>
namespace InfinityShutdownTrace {
struct PreserveErrno { int value{errno}; ~PreserveErrno() noexcept { errno=value; } };
struct Row { std::string phase; long long invoker; std::string addon,outcome,target; };
inline std::mutex rowMutex;
inline std::vector<Row> rows;
inline bool enabled=true;
inline void Event(const char*,const char* phase,long long invoker=-1,
                  unsigned long long=0,unsigned long long=0,long long=0,
                  const char* addon=nullptr,const char* outcome="observed",const char* target=nullptr) {
  if (!enabled) return;
  std::lock_guard<std::mutex> lock(rowMutex);
  rows.push_back({phase,invoker,addon?addon:"",outcome,target?target:""});
}
class Scope { public: explicit Scope(const char*, long long = -1, const char* = nullptr, const char* = nullptr) {} };
}
