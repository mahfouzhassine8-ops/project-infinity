#!/usr/bin/env python3
"""Compile the production coordinator and CVariant against controlled peer adapters.

Exercises the actual manager/JNI-independent protocol, file reads, session fences,
and status encoder. Kodi service/player/settings adapters and JSON parser are test
boundaries; this is not an Android ABI build or proof of those adapters' behavior.
The SAFE fixture is emitted by production EncodeStatusLocked for the Java parser.
"""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile


STUBS = r'''
#pragma once
#include "utils/Variant.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include "platform/android/activity/InfinityCheckpointFile.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <vector>
#include <unistd.h>
namespace Test {
inline std::string root;
inline bool initialized=true, pvrStopped=true, settingsOk=true, profilesOk=true;
inline bool skinOk=true, addonsOk=true, favouritesOk=true, peripheralsOk=true;
inline bool playbackOk=true, playbackPending=false;
inline int residents=1, jobs=0, queueJobs=0, freezes=0, saves=0;
inline std::vector<std::string> foreign;
inline std::map<std::string,CVariant> parsed;
inline std::string Escape(const std::string& s) {
 std::string out="\""; for(char c:s) { if(c=='\\'||c=='\"')out+='\\'; out+=c; } return out+'\"';
}
inline std::string Encode(const CVariant& v) {
 if(v.isNull())return "null";
 if(v.isBoolean())return v.asBoolean()?"true":"false";
 if(v.isSignedInteger())return std::to_string(v.asInteger());
 if(v.isUnsignedInteger())return std::to_string(v.asUnsignedInteger());
 if(v.isString())return Escape(v.asString());
 std::string r=v.isArray()?"[":"{";bool first=true;
 if(v.isArray())for(auto it=v.begin_array();it!=v.end_array();++it){if(!first)r+=',';first=false;r+=Encode(*it);}
 else for(auto it=v.begin_map();it!=v.end_map();++it){if(!first)r+=',';first=false;r+=Escape(it->first)+':'+Encode(it->second);}
 return r+(v.isArray()?"]":"}");
}
}
class CJSONVariantWriter {public: static bool Write(const CVariant& v,std::string& out,bool){out=Test::Encode(v);Test::parsed[out]=v;return true;}};
class CJSONVariantParser {public: static bool Parse(const std::string& in,CVariant& out){auto i=Test::parsed.find(in);if(i==Test::parsed.end())return false;out=i->second;return true;}};
class CSpecialProtocol {public: static std::string TranslatePath(const std::string& p){
 const std::string prefix="special://profile";return p.rfind(prefix,0)==0?Test::root+p.substr(prefix.size()):p;}};
namespace XFILE {class CDirectory {public: static bool Create(const std::string& p){std::filesystem::create_directories(p);return true;}};}
namespace InfinityAndroidCheckpoint {
inline bool LocalCheckpointPath(const std::string& p,std::string& out){out=CSpecialProtocol::TranslatePath(p);return !out.empty()&&out[0]=='/';}
inline bool CheckpointCreatedDirectory(const std::string&){return true;}
inline bool SaveCheckpointXml(const std::string& p,std::string_view bytes){
 auto saved=infinity::checkpoint::files::SaveDirty(p,bytes);if(!saved.ok)RecordFailure("xml_files","test_boundary_write_failed");return saved.ok;}
}
class CApplicationPlayer {};
class CApplicationPlayerCallback {};
class CApplication:public CApplicationPlayerCallback {public: bool IsInitialized()const{return Test::initialized;}
 template<class T>std::shared_ptr<T>GetComponent(){static auto p=std::make_shared<T>();return p;}};
class CScriptInvocationManager {public: static CScriptInvocationManager& GetInstance(){static CScriptInvocationManager m;return m;}
 void BeginShutdown(){}; void BeginAndroidCheckpoint(){};
 std::size_t AndroidCheckpointForeignScripts()const{return Test::foreign.size();}
 std::size_t AndroidCheckpointResidentCount()const{return Test::residents;}
 std::vector<std::string> AndroidCheckpointUnresolvedWriters()const{return Test::foreign;}};
class CJobQueue {public:static std::size_t AndroidCheckpointOutstandingQueues(){return Test::queueJobs;}};
class CJobManager {public:void UnPauseJobs(){}; std::size_t AndroidCheckpointOutstandingJobs()const{return Test::jobs;}};
class CSettings {public:bool Save(){++Test::saves;return Test::settingsOk;}};
class CProfileManager {public:bool Save(){return Test::profilesOk;}};
class CSettingsComponent {public:std::shared_ptr<CSettings>GetSettings(){static auto s=std::make_shared<CSettings>();return s;}
 std::shared_ptr<CProfileManager>GetProfileManager(){static auto p=std::make_shared<CProfileManager>();return p;}};
class CFavouritesService {public:bool CheckpointForAndroidExit(){return Test::favouritesOk;}};
namespace PERIPHERALS {class CPeripherals {public:bool CheckpointForAndroidExit(){return Test::peripheralsOk;}};}
namespace PVR {class CPVRManager {public:bool IsStopped(){return Test::pvrStopped;}};}
namespace ANNOUNCEMENT {enum AnnouncementFlag {Other=1};class CAnnouncementManager {public:void Announce(AnnouncementFlag,const std::string&,const std::string&,const CVariant&){} };}
class CServiceBroker {public:
 static std::shared_ptr<CJobManager>GetJobManager(){static auto p=std::make_shared<CJobManager>();return p;}
 static PVR::CPVRManager&GetPVRManager(){static PVR::CPVRManager p;return p;}
 static std::shared_ptr<CSettingsComponent>GetSettingsComponent(){static auto p=std::make_shared<CSettingsComponent>();return p;}
 static CFavouritesService&GetFavouritesService(){static CFavouritesService s;return s;}
 static PERIPHERALS::CPeripherals&GetPeripherals(){static PERIPHERALS::CPeripherals p;return p;}
 static std::shared_ptr<ANNOUNCEMENT::CAnnouncementManager>GetAnnouncementManager(){static auto p=std::make_shared<ANNOUNCEMENT::CAnnouncementManager>();return p;}
};
namespace InfinityPlaybackCheckpoint {enum class PollResult{Pending,Complete,Failed};
inline PollResult Poll(CApplicationPlayer&,CApplicationPlayerCallback&,const std::string&,std::string&failure){
 ++Test::freezes;if(!Test::playbackOk){failure="unsupported_player";return PollResult::Failed;}
 return Test::playbackPending?PollResult::Pending:PollResult::Complete;}}
namespace InfinityAndroidCheckpoint {
bool CheckpointLoadedAddonSettings(){return Test::addonsOk;}
bool CheckpointSkinSettings(){return Test::skinOk;}
void MarkAddonSettingsManagerDirty(const void*){}
}
'''

HARNESS = r'''
#include "platform/android/activity/InfinityAndroidCheckpoint.cpp"
#include <iostream>
using namespace InfinityAndroidCheckpoint;
static const std::string SESSION="11111111-1111-4111-8111-111111111111", OWNER="22222222-2222-4222-8222-222222222222";
static CVariant identity(){CVariant v(CVariant::VariantTypeObject);v["schema"]=1;v["session"]=SESSION;v["owner"]=OWNER;v["pid"]=static_cast<int>(getpid());return v;}
static void active(bool malformed=false){auto v=identity();v["status"]="ACTIVE";v["participant_api"]=1;v["addon_version"]="0.3.5.19";if(malformed)v["pid"]=true;assert(WriteJson(Get().directory+"/active.json",v));}
static void response(const std::string& status,bool malformed=false){auto v=identity();v["status"]=status;v["participant"]="command-center-json";if(!malformed)v["global_safe_to_terminate"]=false;assert(WriteJson(Get().directory+"/response.json",v));}
static void ready(CApplication& app){Pump(app);active();Pump(app);assert(Test::freezes==1);response("PLAYBACK_CHECKPOINTED");Pump(app);response("PARTICIPANT_COMPLETE");}
int main(int argc,char**argv){
 assert(argc==3);std::string mode=argv[1];Test::root=argv[2];CApplication app;
 if(mode=="foreign")Test::foreign={"service.unknown:service.py"};
 if(mode=="pvr")Test::pvrStopped=false;
 if(mode=="init")Test::initialized=false;
 assert(!Request("bad",OWNER,getpid()));assert(Request(SESSION,OWNER,getpid()));
 assert(Status(SESSION,OWNER,getpid()).find("QUIESCE")!=std::string::npos);
 assert(!Request("session-0000000000000002",OWNER,getpid()));
 assert(!AuthorizeTermination(SESSION,OWNER,getpid()));
 if(mode=="init"||mode=="pvr"){Pump(app);assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 if(mode=="prewrite"){
   // Already-admitted command guard delays freeze; new commands are refused.
   Pump(app);active();{AcceptedPlaybackWorkScope old;CheckpointWriteGuard command("playback-command");assert(!command);Pump(app);assert(Test::freezes==0);}
   Pump(app);assert(Test::freezes==1);return 0;
 }
 if(mode=="malformed-active"){Pump(app);active(true);Pump(app);assert(Test::freezes==0);return 0;}
 if(mode=="playback-fail"){Test::playbackOk=false;Pump(app);active();Pump(app);assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 ready(app);
 if(mode=="cc-fail"){response("CHECKPOINT_FAILED");Pump(app);assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 if(mode=="malformed-response"){response("PARTICIPANT_COMPLETE",true);Pump(app);assert(Get().phase=="QUIESCE");return 0;}
 if(mode=="busy"){Test::jobs=1;Pump(app);assert(Get().phase=="QUIESCE");assert(!AuthorizeTermination(SESSION,OWNER,getpid()));Test::jobs=0;}
 if(mode=="settings-fail")Test::settingsOk=false;
 if(mode=="foreign")Test::foreign.clear(); // Finished thread cannot erase retained writer obligations.
 Pump(app);
 if(mode=="settings-fail"||mode=="foreign"){assert(Get().phase=="CHECKPOINT_FAILED");assert(!AuthorizeTermination(SESSION,OWNER,getpid()));return 0;}
 assert(Get().phase=="SAFE_TO_TERMINATE");const auto safe=Status(SESSION,OWNER,getpid());assert(safe==Status(SESSION,OWNER,getpid()));
 if(mode=="latewrite"){
   CheckpointWriteGuard refused("kodi_settings");assert(!refused);
   RecordFailure("xml_files","late_required_save");assert(!AuthorizeTermination(SESSION,OWNER,getpid()));return 0;
 }
 if(mode=="deadline"){Get().expires=Clock::now();assert(!AuthorizeTermination(SESSION,OWNER,getpid()));assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 if(mode=="lifecycle"){NotifyLegacyTeardown("activity_destroy");assert(!AuthorizeTermination(SESSION,OWNER,getpid()));assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 assert(!AuthorizeTermination(SESSION,"foreign-00000000000000",getpid()));
 assert(AuthorizeTermination(SESSION,OWNER,getpid()));assert(!AuthorizeTermination(SESSION,OWNER,getpid()));
 CheckpointWriteGuard refused("kodi_settings");assert(!refused);
 if(mode=="fixture")std::cout<<safe<<'\n';
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    source = args.runtime / "xbmc"
    with tempfile.TemporaryDirectory(prefix="native-coordinator-host-") as temp:
        temp = Path(temp)
        for rel in ["platform/android/activity/InfinityAndroidCheckpoint.cpp",
                    "platform/android/activity/InfinityAndroidCheckpoint.h",
                    "platform/android/activity/InfinityCheckpointFile.h",
                    "dbwrappers/InfinityDatabaseBarrier.h", "utils/Variant.h", "utils/Variant.cpp"]:
            target = temp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / rel, target)
        (temp / "stubs.h").write_text(STUBS)
        boundaries = ["InfinityCheckpointXml.h", "InfinityPlaybackCheckpoint.h"]
        for name in boundaries:
            (temp / "platform/android/activity" / name).write_text('#pragma once\n#include "stubs.h"\n')
        for rel in ["ServiceBroker.h", "addons/Skin.h", "application/Application.h", "application/ApplicationPlayer.h",
                    "favourites/FavouritesService.h", "filesystem/Directory.h", "filesystem/SpecialProtocol.h",
                    "interfaces/AnnouncementManager.h", "interfaces/generic/ScriptInvocationManager.h",
                    "peripherals/Peripherals.h", "profiles/ProfileManager.h", "pvr/PVRManager.h",
                    "settings/Settings.h", "settings/SettingsComponent.h", "utils/JSONVariantParser.h",
                    "utils/JSONVariantWriter.h", "utils/JobManager.h"]:
            target = temp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('#pragma once\n#include "stubs.h"\n')
        (temp / "harness.cpp").write_text(HARNESS)
        binary = temp / "test"
        subprocess.run(["g++", "-std=c++17", "-DTARGET_ANDROID", "-Wno-unused-parameter",
                        "-I", str(temp), "-c", str(temp / "utils/Variant.cpp"),
                        "-o", str(temp / "variant.o")], check=True)
        subprocess.run(["g++", "-std=c++17", "-DTARGET_ANDROID", "-Wall", "-Wextra", "-Werror", "-pthread",
                        "-I", str(temp), str(temp / "harness.cpp"), str(temp / "variant.o"),
                        "-o", str(binary)], check=True)
        modes = ["fixture", "init", "pvr", "prewrite", "malformed-active", "playback-fail", "cc-fail",
                 "malformed-response", "busy", "settings-fail", "foreign", "latewrite", "deadline", "lifecycle"]
        for mode in modes:
            output = subprocess.check_output([str(binary), mode, str(temp / mode)], text=True, timeout=10)
            if mode == "fixture" and args.fixture:
                args.fixture.parent.mkdir(parents=True, exist_ok=True)
                args.fixture.write_text(output)
        print(f"PASS: actual native coordinator + CVariant, {len(modes)} controlled-boundary scenarios")


if __name__ == "__main__":
    main()
