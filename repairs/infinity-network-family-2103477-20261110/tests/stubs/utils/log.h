#pragma once
constexpr int LOGDEBUG=0;
constexpr int LOGERROR=3;
namespace fmt { template<typename T> T* ptr(T* x) { return x; } }
struct CLog { template<typename... T> static void Log(T&&...) {} };
