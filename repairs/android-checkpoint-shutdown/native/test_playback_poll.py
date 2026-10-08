#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import subprocess, tempfile, textwrap
import argparse
parser=argparse.ArgumentParser(description='Compile actual native playback checkpoint source against host boundary fixtures.')
parser.add_argument('--source-root', type=Path, required=True)
root=parser.parse_args().source_root.resolve()
with tempfile.TemporaryDirectory(prefix='infinity-playback-poll-') as t:
 p=Path(t)
 files={
 'FileItem.h': '#pragma once\nclass CFileItem { public: bool video=true; bool IsVideo() const {return video;} };\n',
 'cores/VideoSettings.h': '#pragma once\nclass CVideoSettings {};\n',
 'video/Bookmark.h': '#pragma once\nclass CBookmark {};\n',
 'application/ApplicationPlayer.h': '''#pragma once
#include "platform/android/activity/InfinityPlaybackCheckpoint.h"
class CApplicationPlayer {
public:
 bool supported=true, drained=true, freeze=false, playback=true;
 std::shared_ptr<InfinityPlaybackCheckpoint::Request> request;
 bool RequestInfinityCheckpoint(const std::shared_ptr<InfinityPlaybackCheckpoint::Request>& r) {
 request=r;r->frozen=freeze;r->snapshot.hasPlayback=playback;return supported;
 }
 bool InfinityCheckpointCallbacksDrained() const{return drained;}
};
''',
 'application/ApplicationPlayerCallback.h': '''#pragma once
#include "platform/android/activity/InfinityPlaybackCheckpoint.h"
class CApplicationPlayerCallback {
public:
 int saves=0,settings=0; bool succeeds=true;
 bool CheckpointPlayerState(const CFileItem&,const CBookmark&){++saves;return succeeds;}
 bool CheckpointVideoSettings(const CFileItem&,const CVideoSettings&){++settings;return succeeds;}
};
''',
 'harness.cpp': '''#include "platform/android/activity/InfinityPlaybackCheckpoint.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include "application/ApplicationPlayer.h"
#include "application/ApplicationPlayerCallback.h"
#include <cassert>
#include <string>
#include <iostream>
namespace InfinityAndroidCheckpoint {
unsigned long long failures=0;
bool IsActive(){return true;}
std::uint64_t ErrorGeneration(){return failures;}
bool HasFailureSince(std::uint64_t g){return failures !=g;}
void RecordPersistenceFailure(const char*,const char*){++failures;}
}
int main(int argc,char**argv){
 assert(argc==2);std::string scenario=argv[1],error;CApplicationPlayer p;CApplicationPlayerCallback cb;
 using namespace InfinityPlaybackCheckpoint;
 if(scenario=="idle") {p.freeze=true;p.playback=false;assert(Poll(p,cb,"s",error)==PollResult::Complete);assert(cb.saves==0&&cb.settings==0);}
 else if(scenario=="drain") {
 assert(Poll(p,cb,"s",error)==PollResult::Pending);assert(cb.saves==0);
 p.request->frozen=true;p.drained=false;assert(Poll(p,cb,"s",error)==PollResult::Pending);assert(cb.saves==0);
 p.drained=true;assert(Poll(p,cb,"s",error)==PollResult::Complete);assert(cb.saves==1&&cb.settings==1);
 assert(Poll(p,cb,"s",error)==PollResult::Complete);assert(cb.saves==1&&cb.settings==1);
 }
 else if(scenario=="failed_save") {
 p.freeze=true;cb.succeeds=false;assert(Poll(p,cb,"s",error)==PollResult::Failed);assert(cb.saves==1);
 cb.succeeds=true;assert(Poll(p,cb,"s",error)==PollResult::Failed);assert(cb.saves==1);
 }
 else if(scenario=="callback_failure") {
 assert(Poll(p,cb,"s",error)==PollResult::Pending);p.request->frozen=true;InfinityAndroidCheckpoint::failures++;
 assert(Poll(p,cb,"s",error)==PollResult::Failed);assert(cb.saves==0);
 }
 else if(scenario=="unsupported") {p.supported=false;assert(Poll(p,cb,"s",error)==PollResult::Failed);assert(cb.saves==0);}
 else if(scenario=="wrong_session") {assert(Poll(p,cb,"a",error)==PollResult::Pending);assert(Poll(p,cb,"b",error)==PollResult::Failed);assert(cb.saves==0);}
 else if(scenario=="freeze_failed") {assert(Poll(p,cb,"s",error)==PollResult::Pending);p.request->failure="not frozen";assert(Poll(p,cb,"s",error)==PollResult::Failed);assert(cb.saves==0);}
 else assert(false);
 std::cout<<"PASS "<<scenario<<"\\n";
}
'''
 }
 for name,body in files.items():
  f=p/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(body)
 executable=p/'poll-test'
 subprocess.run(['c++','-std=c++17','-DTARGET_ANDROID','-Wall','-Wextra','-Werror','-pthread','-I'+str(p),'-I'+str(root/'xbmc'),str(p/'harness.cpp'),str(root/'xbmc/platform/android/activity/InfinityPlaybackCheckpoint.cpp'),'-o',str(executable)],check=True)
 for case in ['idle','drain','failed_save','callback_failure','unsupported','wrong_session','freeze_failed']:
  subprocess.run([str(executable),case],check=True,timeout=5)
