/* Test fixture only: delay the real system resolver. Never a release member. */
#define _GNU_SOURCE
#include <errno.h>
#include <time.h>
static void stall_before_lookup(void)
{
  struct timespec delay = {5, 0};
  while (nanosleep(&delay, &delay) && errno == EINTR) {}
}
#define DNS_BEFORE_LOOKUP() stall_before_lookup()
#include "helper.c"
