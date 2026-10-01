// SPDX-License-Identifier: GPL-2.0-or-later
#include <sys/select.h>
#include "../InfinitySocketPoll.h"
#include <sys/socket.h>
#include <sys/resource.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <unistd.h>
#include <dirent.h>
#include <signal.h>
#include <pthread.h>
#include <cassert>
#include <chrono>
#include <cstdio>
#include <thread>
#include <limits>
#include <atomic>
using namespace InfinitySocketPoll;
using Clock=std::chrono::steady_clock;
static std::atomic<int> assertions{0};
#define CHECK(x) do {++assertions; if(!(x)){ std::fprintf(stderr,"FAIL %s:%d: %s errno=%d\n",__FILE__,__LINE__,#x,errno); std::abort(); }} while(0)
static int groups=0;
static void pass(const char* s){++groups; std::printf("PASS %s\n",s);}
struct Pair {int p[2]; Pair(){CHECK(socketpair(AF_UNIX,SOCK_STREAM,0,p)==0);} ~Pair(){for(int& f:p){if(f>=0)close(f);f=-1;}}};
struct Fd {int n; explicit Fd(int f):n(f){CHECK(n>=0);} ~Fd(){if(n>=0)close(n);}};
int countFds(){DIR* d=opendir("/proc/self/fd");CHECK(d);int n=0;while(auto e=readdir(d)){if(e->d_name[0]!='.')++n;}closedir(d);return n;}
static volatile sig_atomic_t signals=0;
static void handler(int){++signals;}
int main(){
  rlimit lim{}; CHECK(getrlimit(RLIMIT_NOFILE,&lim)==0); if(lim.rlim_cur<2048){lim.rlim_cur=std::min<rlim_t>(lim.rlim_max,2048);CHECK(setrlimit(RLIMIT_NOFILE,&lim)==0);} CHECK(lim.rlim_cur>=2048);
  const int before=countFds();
  {
    Pair s; FdSet r,w,e; Clear(&r);Clear(&w);Clear(&e);Add(s.p[0],&r);Add(s.p[0],&w);Add(s.p[0],&e);timeval t{0,0};
    CHECK(Wait(s.p[0]+1,&r,&w,&e,&t)==1);CHECK(!Contains(s.p[0],&r));CHECK(Contains(s.p[0],&w));CHECK(!Contains(s.p[0],&e));
    CHECK(write(s.p[1],"x",1)==1);Clear(&r);Clear(&w);Add(s.p[0],&r);Add(s.p[0],&w);t={0,0};
    fd_set nr,nw;FD_ZERO(&nr);FD_ZERO(&nw);FD_SET(s.p[0],&nr);FD_SET(s.p[0],&nw);timeval nt{0,0};int expected=select(s.p[0]+1,&nr,&nw,nullptr,&nt);
    CHECK(expected==2);CHECK(Wait(s.p[0]+1,&r,&w,nullptr,&t)==expected);CHECK(Contains(s.p[0],&r));CHECK(Contains(s.p[0],&w));
    pass("low-FD read/write results match native select including ready-bit count");
  }
  for(int target:{1094,1219,1277,1327,1504,1542}){
    Pair s; Fd high(fcntl(s.p[0],F_DUPFD_CLOEXEC,target));CHECK(high.n>=target);FdSet r,w,e;Add(high.n,&r);Add(high.n,&r);CHECK(r.descriptors.size()==1);Add(high.n,&w);Add(high.n,&e);CHECK(write(s.p[1],"ok",2)==2);timeval t{0,0};
    CHECK(Wait(high.n+1,&r,&w,&e,&t)==2);CHECK(Contains(high.n,&r));CHECK(Contains(high.n,&w));CHECK(!Contains(high.n,&e));char b[2];CHECK(read(high.n,b,2)==2);CHECK(fcntl(high.n,F_GETFD)>=0);
    std::printf("PASS actual high descriptor %d\n",high.n);
  }
  pass("all six observed high descriptor numbers operate without fixed fd_set");
  {
    Pair s; Fd high(fcntl(s.p[0],F_DUPFD_CLOEXEC,1542));FdSet r;Add(high.n,&r);CHECK(write(s.p[1],"x",1)==1);timeval t{0,0};CHECK(Wait(high.n,&r,nullptr,nullptr,&t)==0);CHECK(r.descriptors.empty());
    pass("nfds upper bound and duplicate membership are respected");
  }
  {
    Pair s;FdSet r;Add(s.p[0],&r);timeval t{0,30000};auto begin=Clock::now();CHECK(Wait(s.p[0]+1,&r,nullptr,nullptr,&t)==0);CHECK(r.descriptors.empty());CHECK(Clock::now()-begin>=std::chrono::milliseconds(20));CHECK(t.tv_sec==0&&t.tv_usec<10000);
    t={0,10000};CHECK(Wait(0,nullptr,nullptr,nullptr,&t)==0);
    pass("finite and empty-set timeout clears readiness without busy loop");
  }
  {
    Pair s;Fd high(fcntl(s.p[0],F_DUPFD_CLOEXEC,1504));FdSet r;Add(high.n,&r);std::thread producer([&]{std::this_thread::sleep_for(std::chrono::milliseconds(10));CHECK(write(s.p[1],"x",1)==1);});
    CHECK(Wait(high.n+1,&r,nullptr,nullptr,nullptr)==1);producer.join();CHECK(Contains(high.n,&r));
    pass("infinite wait wakes on real high-FD socket data");
  }
  {
    Pair s;Fd high(fcntl(s.p[0],F_DUPFD_CLOEXEC,1219));close(s.p[1]);s.p[1]=-1;FdSet r;Add(high.n,&r);timeval t{0,0};CHECK(Wait(high.n+1,&r,nullptr,nullptr,&t)==1);char b;CHECK(read(high.n,&b,1)==0);
    FdSet e;Add(high.n,&e);t={0,20000};auto begin=Clock::now();CHECK(Wait(high.n+1,nullptr,nullptr,&e,&t)==0);CHECK(Clock::now()-begin>=std::chrono::milliseconds(10));CHECK(e.descriptors.empty());
    pass("HUP maps to EOF readability but not false exceptional readiness");
  }
  {
    Pair s;Fd high(fcntl(s.p[0],F_DUPFD_CLOEXEC,1327));int dead=high.n;close(high.n);high.n=-1;FdSet r;Add(dead,&r);timeval t{0,0};errno=0;CHECK(Wait(dead+1,&r,nullptr,nullptr,&t)==-1);CHECK(errno==EBADF);CHECK(Contains(dead,&r));
    Clear(&r);Add(-1,&r);t={0,0};CHECK(Wait(1,&r,nullptr,nullptr,&t)==-1&&errno==EBADF);
    Clear(&r);t={-1,0};CHECK(Wait(0,&r,nullptr,nullptr,&t)==-1&&errno==EINVAL);t={0,1000000};CHECK(Wait(0,&r,nullptr,nullptr,&t)==-1&&errno==EINVAL);t={0,0};CHECK(Wait(-1,&r,nullptr,nullptr,&t)==-1&&errno==EINVAL);
    pass("invalid descriptors/timeouts fail with errno and preserve input sets");
  }
  {
    struct sigaction act{},old{};act.sa_handler=handler;sigemptyset(&act.sa_mask);CHECK(sigaction(SIGUSR1,&act,&old)==0);
    Pair s;Fd high(fcntl(s.p[0],F_DUPFD_CLOEXEC,1542));FdSet r;Add(high.n,&r);const pthread_t main=pthread_self();std::thread interrupt([&]{std::this_thread::sleep_for(std::chrono::milliseconds(15));pthread_kill(main,SIGUSR1);});timeval t{0,100000};
    int result=Wait(high.n+1,&r,nullptr,nullptr,&t);int error=errno;interrupt.join();CHECK(result==-1&&error==EINTR);CHECK(signals>0);CHECK(Contains(high.n,&r));CHECK(t.tv_sec==0&&t.tv_usec<99000&&t.tv_usec>0);
    CHECK(write(s.p[1],"x",1)==1);CHECK(Wait(high.n+1,&r,nullptr,nullptr,&t)==1);CHECK(sigaction(SIGUSR1,&old,nullptr)==0);
    pass("EINTR retains watches and decrements deadline before successful retry");
  }
  {
    Pair data,cancel;Fd high(fcntl(data.p[0],F_DUPFD_CLOEXEC,1277)),wake(fcntl(cancel.p[0],F_DUPFD_CLOEXEC,1542));FdSet r,w,e;Add(high.n,&r);Add(high.n,&e);Add(wake.n,&r);
    std::thread canceller([&]{std::this_thread::sleep_for(std::chrono::milliseconds(10));CHECK(write(cancel.p[1],"!",1)==1);});timeval t{1,0};CHECK(Wait(wake.n+1,&r,&w,&e,&t)==1);canceller.join();CHECK(Contains(wake.n,&r));CHECK(!Contains(high.n,&r));
    pass("separate high cancellation descriptor interrupts socket wait");
  }
  {
    Fd reserved(socket(AF_INET,SOCK_STREAM,0));sockaddr_in addr{};addr.sin_family=AF_INET;addr.sin_addr.s_addr=htonl(INADDR_LOOPBACK);CHECK(bind(reserved.n,(sockaddr*)&addr,sizeof(addr))==0);socklen_t size=sizeof(addr);CHECK(getsockname(reserved.n,(sockaddr*)&addr,&size)==0);
    Fd s(socket(AF_INET,SOCK_STREAM|SOCK_NONBLOCK,0));Fd high(fcntl(s.n,F_DUPFD_CLOEXEC,1327));int rc=connect(high.n,(sockaddr*)&addr,sizeof(addr));CHECK(rc==-1&&(errno==EINPROGRESS||errno==ECONNREFUSED));FdSet w,e;Add(high.n,&w);Add(high.n,&e);timeval t{1,0};CHECK(Wait(high.n+1,nullptr,&w,&e,&t)>0);int err=0;size=sizeof(err);CHECK(getsockopt(high.n,SOL_SOCKET,SO_ERROR,&err,&size)==0);CHECK(err==ECONNREFUSED);CHECK(Contains(high.n,&w));
    pass("failed asynchronous connect is signalled and SO_ERROR remains authoritative");
  }
  {
    Fd listener(socket(AF_INET,SOCK_STREAM,0));sockaddr_in a{};a.sin_family=AF_INET;a.sin_addr.s_addr=htonl(INADDR_LOOPBACK);CHECK(bind(listener.n,(sockaddr*)&a,sizeof(a))==0);CHECK(listen(listener.n,1)==0);socklen_t len=sizeof(a);CHECK(getsockname(listener.n,(sockaddr*)&a,&len)==0);Fd c(socket(AF_INET,SOCK_STREAM,0));CHECK(connect(c.n,(sockaddr*)&a,len)==0);Fd s(accept(listener.n,nullptr,nullptr));Fd high(fcntl(s.n,F_DUPFD_CLOEXEC,1219));CHECK(send(c.n,"!",1,MSG_OOB)==1);FdSet e;Add(high.n,&e);timeval t{1,0};CHECK(Wait(high.n+1,nullptr,nullptr,&e,&t)==1);CHECK(Contains(high.n,&e));char b;CHECK(recv(high.n,&b,1,MSG_OOB)==1);
    pass("TCP urgent data remains exceptional readiness on high descriptor");
  }
  for(int i=0;i<1000;++i){Pair s;Fd high(fcntl(s.p[0],F_DUPFD_CLOEXEC,1094));FdSet w;Add(high.n,&w);timeval t{0,0};CHECK(Wait(high.n+1,nullptr,&w,nullptr,&t)==1);}
  CHECK(countFds()==before);pass("1000 create/wait/close cycles leave actual FD count unchanged");
  std::printf("RESULT groups=%d assertions=%d PASS\n",groups,assertions.load());
}
