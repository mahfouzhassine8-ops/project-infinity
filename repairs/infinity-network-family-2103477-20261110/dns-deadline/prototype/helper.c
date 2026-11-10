/* Standalone libc resolver feasibility helper. No application/user data access. */
#define _GNU_SOURCE
#include "wire.h"
#include <dirent.h>
#include <errno.h>
#include <netdb.h>
#include <signal.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#ifndef DNS_BEFORE_LOOKUP
#define DNS_BEFORE_LOOKUP() ((void)0)
#endif
#if defined(__ANDROID__)
#include <dlfcn.h>
#endif

static int extra_fds(uint32_t *kinds)
{
  DIR *dir = opendir("/proc/self/fd");
  if (!dir) return -1;
  int count = 0;
  struct dirent *entry;
  while ((entry = readdir(dir))) {
    char *end;
    long fd = strtol(entry->d_name, &end, 10);
    if (*entry->d_name && !*end && fd > 2 && fd != dirfd(dir)) {
      ++count;
      char target[512];
      ssize_t length = readlinkat(dirfd(dir), entry->d_name, target, sizeof(target)-1);
      if (length < 0) { *kinds |= 128; continue; }
      target[length] = 0;
      // Categories only. Never copy a file path or network endpoint to IPC/logs.
      if (!strncmp(target, "socket:", 7)) *kinds |= 1;
      else if (!strncmp(target, "anon_inode:", 11)) *kinds |= 2;
      else if (!strncmp(target, "/memfd:", 7) || !strncmp(target, "memfd:", 6)) *kinds |= 4;
      else if (!strncmp(target, "/system/", 8) || !strncmp(target, "/apex/", 6)) *kinds |= 8;
      else if (!strncmp(target, "/dev/", 5)) *kinds |= 16;
      else if (!strncmp(target, "/data/app/", 10)) *kinds |= 32;
      else if (!strncmp(target, "/proc/", 6)) *kinds |= 64;
      else *kinds |= 128;
    }
  }
  closedir(dir);
  return count;
}

int main(void)
{
  sigset_t empty;
  sigemptyset(&empty);
  if (sigprocmask(SIG_SETMASK, &empty, NULL)) return 10;
  struct dns_request request;
  size_t offset = 0;
  while (offset < sizeof(request)) {
    ssize_t n = recv(0, (char *)&request + offset, sizeof(request) - offset, 0);
    if (n < 0 && errno == EINTR) continue;
    if (n <= 0) return 11;
    offset += (size_t)n;
  }
  if (request.magic != DNS_MAGIC || request.hostname[sizeof(request.hostname)-1] ||
      request.service[sizeof(request.service)-1]) return 12;
  struct dns_reply *reply = calloc(1, sizeof(*reply));
  if (!reply) return 13;
  reply->magic = DNS_MAGIC;
  reply->extra_fds = extra_fds(&reply->runtime_fd_kinds);
  struct addrinfo hints;
  memset(&hints, 0, sizeof(hints));
  hints.ai_family = request.family;
  hints.ai_socktype = request.socktype;
  hints.ai_protocol = request.protocol;
  hints.ai_flags = request.flags;
  struct addrinfo *addresses = NULL;
  DNS_BEFORE_LOOKUP();
  if (request.network) {
#if defined(__ANDROID__)
    typedef int (*network_gai)(uint64_t, const char *, const char *,
                               const struct addrinfo *, struct addrinfo **);
    network_gai resolve = (network_gai)dlsym(RTLD_DEFAULT, "android_getaddrinfofornetwork");
    if (resolve) reply->gai_error = resolve(request.network, request.hostname,
        request.service, &hints, &addresses);
    else { reply->gai_error = EAI_SYSTEM; errno = ENOSYS; }
#else
    reply->gai_error = EAI_SYSTEM; /* Never discard an explicit binding. */
    errno = ENOSYS;
#endif
  } else {
    reply->gai_error = getaddrinfo(request.hostname, request.service, &hints, &addresses);
  }
  if (reply->gai_error == EAI_SYSTEM) reply->system_errno = errno;
  if (!reply->gai_error) {
    for (const struct addrinfo *a = addresses; a; a = a->ai_next) {
      if (reply->count == DNS_MAX_ADDRESSES || a->ai_addrlen > sizeof(struct sockaddr_storage) ||
          (a->ai_canonname && strlen(a->ai_canonname) >= sizeof(reply->addresses[0].canonical))) {
        reply->gai_error = EAI_OVERFLOW; reply->count = 0; break;
      }
      struct dns_address *row = &reply->addresses[reply->count++];
      row->family = a->ai_family; row->socktype = a->ai_socktype;
      row->protocol = a->ai_protocol; row->flags = a->ai_flags;
      row->length = a->ai_addrlen;
      memcpy(&row->address, a->ai_addr, a->ai_addrlen);
      if (a->ai_canonname) strcpy(row->canonical, a->ai_canonname);
    }
  }
  if (addresses) freeaddrinfo(addresses);
  const size_t length = offsetof(struct dns_reply, addresses) +
                        reply->count * sizeof(reply->addresses[0]);
  offset = 0;
  while (offset < length) {
    ssize_t n = send(0, (char *)reply + offset, length - offset, MSG_NOSIGNAL);
    if (n < 0 && errno == EINTR) continue;
    if (n <= 0) { free(reply); return 14; }
    offset += (size_t)n;
  }
  free(reply);
  return 0;
}
