/* Test fixture only: delay the real system resolver. Never a release member. */
#define _GNU_SOURCE
#include <netdb.h>
#include <time.h>
static int stalled_getaddrinfo(const char *name, const char *service,
                              const struct addrinfo *hints, struct addrinfo **out)
{
  struct timespec delay = {5, 0};
  nanosleep(&delay, 0);
  return getaddrinfo(name, service, hints, out);
}
#define getaddrinfo stalled_getaddrinfo
#include "helper.c"
