#include "InfinityBridgeState.h"
#include <cassert>
#include <iostream>
#include <limits>
#include <thread>

int main()
{
  CInfinityBridgeState s;
  assert(CInfinityBridgeState::VERSION == 3);
  assert(!s.HasActiveVideo() && !s.CanEnterPictureInPicture());
  assert(s.WindowWidth()==-1 && s.WindowHeight()==-1);
  s.SetPlayback(true,true,false,1.777f);
  assert(s.HasActiveVideo() && s.CanEnterPictureInPicture());
  s.SetPlayback(true,false,false,1.777f); // paused video stays a video, but no auto-entry
  assert(s.HasActiveVideo() && !s.CanEnterPictureInPicture());
  s.SetPlayback(true,true,true,1.777f); // external players own their own Android window
  assert(s.HasActiveVideo() && !s.CanEnterPictureInPicture());
  s.SetPlayback(false,true,false,0.f); // audio/idle cannot auto-enter
  assert(!s.HasActiveVideo() && !s.CanEnterPictureInPicture());
  s.SetPlayback(false,false,false,std::numeric_limits<float>::quiet_NaN());
  assert(std::isfinite(s.VideoAspectRatio()) && s.VideoAspectRatio()>1.7f);
  int w=0,h=0;
  s.QueueGeometry(2208,1840);
  assert(!s.TakeGeometry(w,h)); // no window: defer, don't touch a renderer
  s.SetSurfaceReady(true);
  assert(s.TakeGeometry(w,h) && w==2208 && h==1840);
  assert(!s.TakeGeometry(w,h));
  assert(s.WindowWidth()==-1); // requested != committed
  s.CommitGeometry(2208,1840);
  assert(s.WindowWidth()==2208 && s.WindowHeight()==1840);
  s.QueueGeometry(900,1800);s.QueueGeometry(384,216);s.QueueGeometry(1840,2208);
  assert(s.TakeGeometry(w,h) && w==1840 && h==2208); // last event wins
  s.CommitGeometry(w,h);
  s.QueueGeometry(0,0);s.QueueGeometry(-1,100);s.QueueGeometry(999999,100);
  assert(!s.TakeGeometry(w,h));
  s.SetSurfaceReady(false);assert(s.WindowWidth()==-1);
  s.SetSurfaceReady(true);assert(s.TakeGeometry(w,h) && w==1840 && h==2208);
  s.RetryGeometry();assert(s.TakeGeometry(w,h));
  s.QueueDisplayModes();assert(s.TakeDisplayModes());assert(!s.TakeDisplayModes());
  std::atomic<bool> done{false};
  std::thread writer([&]{for(int i=1;i<=20000;++i)s.QueueGeometry(i,i+1);done=true;});
  while(!done.load()) if(s.TakeGeometry(w,h)) assert(h==w+1);
  writer.join();
  if(s.TakeGeometry(w,h))assert(w==20000 && h==20001);
  std::cout<<"PASS: playback policy, unknown/committed geometry, zero-size rejection, surface recreation, coalescing, and 20,000 concurrent resize events\n";
}
