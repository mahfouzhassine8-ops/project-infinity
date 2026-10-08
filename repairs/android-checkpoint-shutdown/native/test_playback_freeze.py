#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import subprocess,tempfile
import argparse
parser=argparse.ArgumentParser(description='Compile actual native playback checkpoint source against host boundary fixtures.')
parser.add_argument('--source-root', type=Path, required=True)
root=parser.parse_args().source_root.resolve()
s=(root/'xbmc/cores/VideoPlayer/VideoPlayer.cpp').read_text()
start=s.index('bool CVideoPlayer::FreezeForInfinityCheckpoint()')
pos=s.index('{',start);depth=1;i=pos+1
while depth:
 depth += (s[i]=='{')-(s[i]=='}');i+=1
method=s[start:i]
with tempfile.TemporaryDirectory(prefix='infinity-player-freeze-') as t:
 p=Path(t)
 files={
 'FileItem.h':'#pragma once\nclass CFileItem {public: bool live=false,pvr=false;bool IsLiveTV()const{return live;}bool IsPVRChannel()const{return pvr;}};\n',
 'cores/VideoSettings.h':'#pragma once\nclass CVideoSettings {public:int token=123;};\n',
 'video/Bookmark.h':'#pragma once\n#include <string>\nclass CBookmark {public: double timeInSeconds=0,totalTimeInSeconds=0;std::string player,playerState;};\n',
 'harness.cpp':'''#include "platform/android/activity/InfinityPlaybackCheckpoint.h"
#include <atomic>
#include <cmath>
#include <stdexcept>
#include <cassert>
#include <iostream>
#define DVD_PLAYSPEED_PAUSE 0
struct Clock {int speed=1;void SetSpeed(int s){speed=s;}};
struct Info {float speed=1;bool frame=true;void SetSpeed(float s){speed=s;}void SetFrameAdvance(bool b){frame=b;}CVideoSettings GetVideoSettings(){return {};}};
class CVideoPlayer {
public:
 std::mutex m_infinityCheckpointMutex;std::shared_ptr<InfinityPlaybackCheckpoint::Request>m_infinityCheckpointRequest;
 std::atomic<bool>m_infinityCheckpointFrozen{false};int m_playSpeed=1,m_streamPlayerSpeed=1;
 std::shared_ptr<Info>m_processInfo=std::make_shared<Info>();Clock m_clock;
 std::shared_ptr<Clock>m_VideoPlayerAudio=std::make_shared<Clock>(),m_VideoPlayerVideo=std::make_shared<Clock>();
 CFileItem m_item;std::string m_name="VideoPlayer";bool m_bAbortRequest=false;
 struct State {bool streamsReady=true;int startTime=0;double time=417125,timeMax=900000,timeMin=0;}m_State;
 void UpdatePlayState(int){}void UpdateFileItemStreamDetails(CFileItem&){}std::string GetPlayerState(){return "native-disc-state";}
 bool FreezeForInfinityCheckpoint();
};
'''+method+'''
int main(){
 CVideoPlayer p;assert(!p.FreezeForInfinityCheckpoint());assert(!p.m_infinityCheckpointFrozen);
 p.m_infinityCheckpointRequest=std::make_shared<InfinityPlaybackCheckpoint::Request>("s");
 assert(p.FreezeForInfinityCheckpoint());auto&r=*p.m_infinityCheckpointRequest;assert(r.frozen&&r.failure.empty());
 assert(r.snapshot.bookmark.timeInSeconds==417.125&&r.snapshot.bookmark.totalTimeInSeconds==900.0);
 assert(r.snapshot.bookmark.playerState=="native-disc-state");assert(p.m_clock.speed==0&&p.m_VideoPlayerAudio->speed==0&&p.m_VideoPlayerVideo->speed==0);
 assert(p.m_infinityCheckpointFrozen&&p.m_playSpeed==0&&p.m_streamPlayerSpeed==0&&!p.m_processInfo->frame);
 CVideoPlayer invalid;invalid.m_State.timeMax=0;invalid.m_infinityCheckpointRequest=std::make_shared<InfinityPlaybackCheckpoint::Request>("s");
 assert(invalid.FreezeForInfinityCheckpoint());assert(invalid.m_infinityCheckpointFrozen);assert(!invalid.m_infinityCheckpointRequest->frozen&&!invalid.m_infinityCheckpointRequest->failure.empty());
 CVideoPlayer live;live.m_item.live=true;live.m_State.timeMax=0;live.m_infinityCheckpointRequest=std::make_shared<InfinityPlaybackCheckpoint::Request>("s");
 assert(live.FreezeForInfinityCheckpoint());assert(live.m_infinityCheckpointRequest->frozen);assert(live.m_infinityCheckpointRequest->snapshot.bookmark.timeInSeconds==0);
 CVideoPlayer ended;ended.m_bAbortRequest=true;ended.m_infinityCheckpointRequest=std::make_shared<InfinityPlaybackCheckpoint::Request>("s");
 assert(ended.FreezeForInfinityCheckpoint());assert(!ended.m_infinityCheckpointRequest->frozen&&!ended.m_infinityCheckpointRequest->failure.empty());
 std::cout<<"PASS actual freeze method: idle, exact snapshot, parked clocks, unknown duration, live no resume, abort rejection\\n";
}
'''}
 for n,b in files.items():
  f=p/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(b)
 exe=p/'freeze-test'
 subprocess.run(['c++','-std=c++17','-Wall','-Wextra','-Werror','-pthread','-I'+str(p),'-I'+str(root/'xbmc'),str(p/'harness.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True,timeout=5)
