#pragma once
#include <sys/socket.h>
#include <netdb.h>
#include <string>
class CNetworkBase {
public:
 static std::string GetIpStr(const sockaddr* address) {
  char host[NI_MAXHOST]{};
  const socklen_t length=address->sa_family==AF_INET6 ? sizeof(sockaddr_in6) : sizeof(sockaddr_in);
  return getnameinfo(address,length,host,sizeof(host),nullptr,0,NI_NUMERICHOST)==0 ? host : "";
 }
};
