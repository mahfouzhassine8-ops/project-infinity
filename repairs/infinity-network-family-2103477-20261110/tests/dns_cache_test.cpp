#include "../native/xbmc/network/DNSNameCache.h"
#include "../native/xbmc/filesystem/DllLibCurl.h"
#include "../native/xbmc/filesystem/InfinityNetworkFamily.h"
#include <cassert>
#include <iostream>
int main() {
 std::string address;
 CDNSNameCache::Add("dynamic.test","127.0.0.1");
 assert(CDNSNameCache::GetCached("dynamic.test",address));
 assert(!CDNSNameCache::GetConfigured("dynamic.test",address));
 CDNSNameCache::AddConfigured("manual.test","::1");
 assert(CDNSNameCache::GetConfigured("manual.test",address) && address=="::1");
 assert(CDNSNameCache::GetCached("manual.test",address) && address=="::1");
 CDNSNameCache::Add("mixed.test","127.0.0.1");
 CDNSNameCache::AddConfigured("mixed.test","::1");
 assert(CDNSNameCache::GetConfigured("mixed.test",address) && address=="::1");
 assert(CDNSNameCache::GetCached("mixed.test",address) && address=="127.0.0.1");
 assert(std::string(InfinityNetworkFamily::ConnectedFamily("::ffff:127.0.0.1"))=="ipv4_mapped");
 int mode=6;
 assert(!InfinityNetworkFamily::Configure([](auto,auto) { return CURLE_UNKNOWN_OPTION; },mode,1000L,true));
 std::cout << "PASS dynamic cache bypass; manual override; unchanged legacy lookup; mapped diagnostic; policy setup fail-closed\n";
}
