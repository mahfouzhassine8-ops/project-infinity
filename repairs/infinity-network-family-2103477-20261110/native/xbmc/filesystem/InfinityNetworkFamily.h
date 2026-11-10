/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <string>
#include <curl/curl.h>
#if defined(TARGET_ANDROID) || defined(__linux__)
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#endif

// Request-local policy. No global resolver, CURL share handle or JVM changes.
namespace InfinityNetworkFamily
{
enum Mode : int { Unmanaged = -1, Automatic = 0, IPv4 = 4, IPv6 = 6 };
constexpr long FallbackDelayMs = 200;
constexpr long MaxConnectMs = 15000;

inline Mode Parse(const std::string& value)
{
  return value == "ipv4" ? IPv4 : value == "ipv6" ? IPv6 : Automatic;
}

inline const char* Label(int value)
{
  return value == IPv4 ? "ipv4" : value == IPv6 ? "ipv6" : "auto";
}

inline const char* ConnectedFamily(const char* address)
{
  if (!address || !*address)
    return "unconnected";
#if defined(TARGET_ANDROID) || defined(__linux__)
  in6_addr parsed{};
  if (inet_pton(AF_INET6, address, &parsed) == 1)
    return IN6_IS_ADDR_V4MAPPED(&parsed) ? "ipv4_mapped" : "ipv6";
#endif
  return "ipv4";
}

inline long Resolve(int value)
{
  return value == IPv4 ? CURL_IPRESOLVE_V4 : value == IPv6 ? CURL_IPRESOLVE_V6
                                                                     : CURL_IPRESOLVE_WHATEVER;
}

#if defined(TARGET_ANDROID) || defined(__linux__)
inline curl_socket_t OpenSocket(void* context, curlsocktype, struct curl_sockaddr* address)
{
  const int mode = *static_cast<const int*>(context);
  if ((mode == IPv4 && address->family != AF_INET) ||
      (mode == IPv6 && address->family != AF_INET6))
    return CURL_SOCKET_BAD;
  if (mode == IPv6 && address->family == AF_INET6 &&
      IN6_IS_ADDR_V4MAPPED(&reinterpret_cast<const sockaddr_in6*>(&address->addr)->sin6_addr))
    return CURL_SOCKET_BAD;
  return ::socket(address->family, address->socktype, address->protocol);
}
#endif

// The same option application is exercised against real curl by focused tests.
// Streaming has no total-duration cap; connection setup has a finite deadline.
template<typename Setter>
bool Configure(Setter&& set, int& mode, long existingConnectMs, bool changedMode)
{
  const long deadline = existingConnectMs > 0 && existingConnectMs < MaxConnectMs
                            ? existingConnectMs : MaxConnectMs;
  bool ready = set(CURLOPT_IPRESOLVE, Resolve(mode)) == CURLE_OK &&
         set(CURLOPT_HAPPY_EYEBALLS_TIMEOUT_MS, FallbackDelayMs) == CURLE_OK &&
         set(CURLOPT_CONNECTTIMEOUT_MS, deadline) == CURLE_OK &&
         set(CURLOPT_DNS_CACHE_TIMEOUT, 30L) == CURLE_OK &&
         set(CURLOPT_FRESH_CONNECT, changedMode ? 1L : 0L) == CURLE_OK;
#if defined(TARGET_ANDROID) || defined(__linux__)
  if (mode == IPv4 || mode == IPv6)
    ready = ready && set(CURLOPT_OPENSOCKETFUNCTION, OpenSocket) == CURLE_OK &&
            set(CURLOPT_OPENSOCKETDATA, &mode) == CURLE_OK;
#endif
  return ready;
}
} // namespace InfinityNetworkFamily
