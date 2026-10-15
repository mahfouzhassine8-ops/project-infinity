/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "InfinityBridgeState.h"
#include <cassert>
#include <iostream>
#include <limits>
#include <thread>

int main()
{
  using State = CInfinityBridgeState;
  State s; State::Geometry r;
  assert(s.Snapshot()[0] == 4 && !s.Snapshot()[3]);
  s.SetConfiguration(1, 4);
  s.SetPlayback(true, true, false, 2.35f);
  assert(!s.CanEnterPictureInPicture()); // version is not readiness
  s.QueueGeometry(2208,1840);
  assert(!s.TakeGeometry(r));
  s.SetSurfaceReady(true); s.SetEngineReady(true);
  assert(s.CanEnterPictureInPicture());
  assert(s.TakeGeometry(r) && r.Width()==2208 && r.Height()==1840);
  assert(s.WindowWidth()==-1 && s.CommitGeometry(r));
  assert(s.WindowWidth()==2208 && s.WindowHeight()==1840);
  const auto first=s.Snapshot();
  s.QueueGeometry(2208,1840); s.SetConfiguration(2,4);
  assert(!s.TakeGeometry(r) && s.Snapshot()[6]==first[6]); // theme does not resize
  int theme=0,mode=0;uint64_t revision=0;
  assert(s.TakeTheme(theme,mode,revision) && theme==2 && mode==4);
  assert(!s.TakeTheme(theme,mode,revision));
  s.QueueGeometry(900,1800);s.QueueGeometry(384,216);s.QueueGeometry(1840,2208);
  assert(s.TakeGeometry(r) && r.Width()==1840 && r.Height()==2208);
  s.QueueGeometry(1080,1920);
  assert(!s.IsCurrent(r) && !s.CommitGeometry(r)); // superseded work cannot claim success
  assert(s.TakeGeometry(r) && r.Width()==1080 && s.CommitGeometry(r));
  s.QueueGeometry(0,0);s.QueueGeometry(-1,100);s.QueueGeometry(999999,100);
  assert(!s.TakeGeometry(r));
  s.RetryGeometry(); assert(s.TakeGeometry(r));
  const auto stale=r;
  s.SetSurfaceReady(false); assert(s.WindowWidth()==-1 && !s.CommitGeometry(stale));
  s.SetSurfaceReady(true); s.SetEngineReady(true);
  assert(!s.TakeGeometry(r)); // a recreated surface never replays a dead request
  s.QueueGeometry(1840,2208);assert(s.TakeGeometry(r));
  assert(r.generation!=stale.generation && s.CommitGeometry(r));
  s.SetConfiguration(2,8); // TV fullscreen: relinquish managed geometry
  assert(!s.CommitGeometry(r) && s.WindowWidth()==-1);
  s.QueueGeometry(200,100);assert(!s.TakeGeometry(r));
  s.SetConfiguration(2,4);s.QueueGeometry(1000,1600);assert(s.TakeGeometry(r));
  s.SetPlayback(true,false,false,1.0f);assert(!s.CanEnterPictureInPicture());
  s.SetPlayback(true,true,true,1.0f);assert(!s.CanEnterPictureInPicture());
  s.SetPlayback(false,true,false,1.0f);assert(!s.CanEnterPictureInPicture());
  s.SetPlayback(true,true,false,std::numeric_limits<float>::quiet_NaN());
  assert(std::isfinite(s.VideoAspectRatio()) && s.VideoAspectRatio()>1.7f);
  s.QueueDisplayModes();assert(s.TakeDisplayModes());assert(!s.TakeDisplayModes());
  std::atomic<bool> done{false};
  std::thread writer([&]{for(int i=1;i<=20000;++i)s.QueueGeometry(i,i+1);done=true;});
  while(!done.load()) if(s.TakeGeometry(r)) { assert(r.Height()==r.Width()+1); s.CommitGeometry(r); }
  writer.join();
  if(s.TakeGeometry(r)){assert(r.Width()==20000 && r.Height()==20001);assert(s.CommitGeometry(r));}
  const auto snapshot=s.Snapshot();
  assert(snapshot[7]==20000 && snapshot[8]==20001);
  s.Shutdown();s.SetSurfaceReady(true);s.SetEngineReady(true);s.QueueGeometry(500,600);
  assert(!s.TakeGeometry(r) && !s.CanEnterPictureInPicture() && s.WindowWidth()==-1);
  assert(s.Snapshot()[2]==0 && s.Snapshot()[3]==0 && s.Snapshot()[4]==0);
  std::cout << "PASS: v4 readiness, paired snapshots, latest-wins coalescing, stale sequence rejection, surface generation rejection, no dead-request replay, theme/resize isolation, unmanaged handoff, playback policy, shutdown and 20,000 concurrent publications\n";
}
