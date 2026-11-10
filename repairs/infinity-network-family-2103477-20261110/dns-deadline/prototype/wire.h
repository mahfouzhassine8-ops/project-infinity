/* Feasibility protocol only. Not activated in production curl or an APK. */
#pragma once
#include <stdint.h>
#include <sys/socket.h>
#define DNS_MAGIC 0x49444e53u
#define DNS_MAX_ADDRESSES 64u
struct dns_request {
  uint32_t magic;
  int32_t family, socktype, protocol, flags;
  uint64_t network;
  char hostname[1024];
  char service[16];
};
struct dns_address {
  int32_t family, socktype, protocol, flags;
  uint32_t length;
  struct sockaddr_storage address;
  char canonical[1024];
};
struct dns_reply {
  uint32_t magic, count;
  int32_t gai_error, system_errno, extra_fds;
  struct dns_address addresses[DNS_MAX_ADDRESSES];
};
