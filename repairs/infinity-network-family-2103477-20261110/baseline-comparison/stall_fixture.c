// Disposable host process only. Never included in Kodi or an APK.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <netdb.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
int getaddrinfo(const char* host, const char* service, const struct addrinfo* hints,
                struct addrinfo** result)
{
  if (host && !strcmp(host, "infinity-compare.invalid")) {
    char line[120];
    int length = snprintf(line,sizeof(line),"{\"fixture_family\":%d,\"fixture_stall_seconds\":5}\n",
                          hints ? hints->ai_family : -1);
    write(STDERR_FILENO,line,length);
    struct timespec remaining = {5,0};
    while (nanosleep(&remaining,&remaining) && errno==EINTR) {}
    *result = NULL; errno = EAGAIN; return EAI_AGAIN;
  }
  typedef int (*Function)(const char*, const char*, const struct addrinfo*, struct addrinfo**);
  return ((Function)dlsym(RTLD_NEXT,"getaddrinfo"))(host,service,hints,result);
}
