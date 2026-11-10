#pragma once
#include <mutex>
class CCriticalSection : public std::recursive_mutex {};
