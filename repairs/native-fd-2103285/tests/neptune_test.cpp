// SPDX-License-Identifier: GPL-2.0-or-later
// Compile the real patched Neptune socket implementation in this translation unit.
#include "NptBsdSockets.cpp"
#include <cassert>
#include <cstdio>
#include <thread>
#include <chrono>
#include <fcntl.h>
#include <unistd.h>
static void check(bool b){if(!b)std::abort();}
int main(){
  int p[2];check(socketpair(AF_UNIX,SOCK_STREAM,0,p)==0);
  int high=fcntl(p[0],F_DUPFD_CLOEXEC,1542);check(high>=1542);close(p[0]);
  {
    NPT_BsdSocketFd socket(high,NPT_SOCKET_FLAG_CANCELLABLE);
    check(socket.WaitForCondition(true,false,false,0)==NPT_ERROR_WOULD_BLOCK);
    check(socket.WaitForCondition(true,false,false,20)==NPT_ERROR_TIMEOUT);
    check(socket.WaitForCondition(false,true,false,100)==NPT_SUCCESS);
    check(write(p[1],"x",1)==1);
    check(socket.WaitForCondition(true,false,false,100)==NPT_SUCCESS);
    char b;check(read(high,&b,1)==1);
    // Preserve cancellation with its own high descriptor.
    int cancelHigh=fcntl(socket.m_CancelFds[1],F_DUPFD_CLOEXEC,1600);check(cancelHigh>=1600);
    close(socket.m_CancelFds[1]);socket.m_CancelFds[1]=cancelHigh;
    std::thread cancel([&]{std::this_thread::sleep_for(std::chrono::milliseconds(10));socket.Cancel(false);});
    check(socket.WaitForCondition(true,false,false,NPT_TIMEOUT_INFINITE)==NPT_ERROR_CANCELLED);
    cancel.join();
  }
  close(p[1]);
  check(socketpair(AF_UNIX,SOCK_STREAM,0,p)==0);high=fcntl(p[0],F_DUPFD_CLOEXEC,1219);check(high>=1219);close(p[0]);
  {
    NPT_BsdSocketFd socket(high,0);close(p[1]);
    check(socket.WaitForCondition(true,false,false,100)==NPT_SUCCESS);
    char b;check(read(high,&b,1)==0);
  }
  std::puts("PASS real Neptune: high-FD readable/writable, timeout, would-block, cancellation and EOF");
}
