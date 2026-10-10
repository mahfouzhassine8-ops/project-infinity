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
#include "utils/JobCheckpoint.h"
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
inline bool initialized=true, pvrStopped=true, pvrOwners=false, settingsOk=true, profilesOk=true;
inline bool skinOk=true, addonsOk=true, favouritesOk=true, peripheralsOk=true;
inline bool playbackOk=true, playbackPending=false, ownLease=true, oldRetired=true, audioOk=true, deferredOk=true;
inline bool unknownRunning=false,receiptMissing=false;
inline int residents=1, compatResidents=1, jobs=0, queueJobs=0, unknownJobs=0, optionalJobs=0, freezes=0, saves=0;
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
inline bool SaveCheckpointProtocol(const std::string& p,std::string_view bytes){
 auto saved=infinity::checkpoint::files::SaveProtocolRecord(p,bytes);if(!saved.ok)RecordFailure("xml_files","test_boundary_write_failed");return saved.ok;}
}
namespace jni { class CJNIMainActivity {public: static CJNIMainActivity*GetAppInstance(){static CJNIMainActivity a;return &a;}
 bool infinityCheckpointOwnsOwner(int,const std::string&)const{return Test::ownLease;}
 bool infinityCheckpointOwnerRetired(int,const std::string&)const{return Test::oldRetired;}};}
class CApplicationPlayer {};
class CApplicationPlayerCallback {};
class CApplication:public CApplicationPlayerCallback {public: bool IsInitialized()const{return Test::initialized;}
 template<class T>std::shared_ptr<T>GetComponent(){static auto p=std::make_shared<T>();return p;}};
class CScriptInvocationManager {public: static CScriptInvocationManager& GetInstance(){static CScriptInvocationManager m;return m;}
 void BeginShutdown(){}; void BeginAndroidCheckpoint(){};
 void PumpAndroidCheckpointRetirement(bool=false){}
 std::size_t AndroidCheckpointEscalationsActive()const{return 0;}
 std::size_t AndroidCheckpointForeignScripts()const{return Test::foreign.size();}
 std::size_t AndroidCheckpointResidentCount()const{return Test::residents;}
 std::size_t AndroidCheckpointCompatCount()const{return Test::compatResidents;}
 std::vector<std::string> AndroidCheckpointUnresolvedWriters()const{return Test::foreign;}};
class CJobQueue {public:static std::size_t AndroidCheckpointOutstandingQueues(){return Test::queueJobs;}};
class CJobManager {public:void UnPauseJobs(){}; std::size_t AndroidCheckpointOutstandingJobs()const{return Test::jobs;}
 static JobCheckpoint::Snapshot AndroidCheckpointSnapshot(){JobCheckpoint::Snapshot s;s.required=Test::jobs+Test::queueJobs+Test::unknownJobs;s.unknown=Test::receiptMissing?0:Test::unknownJobs;s.nonPersistent=Test::optionalJobs;
 if(s.required){JobCheckpoint::Entry e;e.owner="native_databases";e.type="test-peer-job";e.operation="test-operation";e.unknown=Test::unknownJobs!=0 && !Test::receiptMissing;e.phase=(e.unknown&&!Test::unknownRunning)||Test::receiptMissing?"completed_without_owner_receipt":"callback";s.blockers.push_back(e);}return s;}};
class CSettings {public:bool Save(){++Test::saves;return Test::settingsOk;}};
class CProfileManager {public:bool Save(){return Test::profilesOk;}};
class CSettingsComponent {public:std::shared_ptr<CSettings>GetSettings(){static auto s=std::make_shared<CSettings>();return s;}
 std::shared_ptr<CProfileManager>GetProfileManager(){static auto p=std::make_shared<CProfileManager>();return p;}};
class CFavouritesService {public:bool CheckpointForAndroidExit(){return Test::favouritesOk;}};
namespace PERIPHERALS {class CPeripherals {public:bool CheckpointForAndroidExit(){return Test::peripheralsOk;}};}
namespace PVR {class CPVRClients {public:bool HasAndroidCheckpointOwners()const{return Test::pvrOwners;}};class CPVRManager {public:bool IsStoppedForAndroidCheckpoint()const{return IsStopped();} std::shared_ptr<CPVRClients>Clients()const{static auto c=std::make_shared<CPVRClients>();return c;} private:bool IsStopped()const{return Test::pvrStopped;}};}
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
bool CheckpointAudioPolicyFile(){return Test::audioOk;}
bool CheckpointDeferredDialogState(){return Test::deferredOk;}
void MarkAddonSettingsManagerDirty(const void*){}
}
'''

HARNESS = r'''
#include "platform/android/activity/InfinityAndroidCheckpoint.cpp"
#include <iostream>
using namespace InfinityAndroidCheckpoint;
static const std::string SESSION="11111111-1111-4111-8111-111111111111", OWNER="22222222-2222-4222-8222-222222222222";
static bool WritePeerJson(const std::string& p,const CVariant& v){std::string bytes;return CJSONVariantWriter::Write(v,bytes,true)&&SaveCheckpointXml(p,bytes);}
static CVariant identity(){CVariant v(CVariant::VariantTypeObject);v["schema"]=1;v["session"]=SESSION;v["owner"]=OWNER;v["pid"]=static_cast<int>(getpid());return v;}
static CVariant compat(){auto v=identity();v["status"]="ACTIVE";v["participant"]="infinity-compat";v["participant_api"]=1;v["addon_version"]="0.7.2";v["global_safe_to_terminate"]=false;return v;}
static void active(bool malformed=false){auto v=identity();v["status"]="ACTIVE";v["participant_api"]=1;v["addon_version"]="0.3.5.19";if(malformed)v["pid"]=true;assert(WritePeerJson(Get().directory+"/active.json",v));assert(WritePeerJson(Get().directory+"/compat-active.json",compat()));}
static void compatResponse(const std::string& status="PARTICIPANT_COMPLETE",bool malformed=false){auto v=compat();v["status"]=status;v["guard_frozen"]=!malformed;v["operations"]=CVariant(CVariant::VariantTypeArray);for(const char*name:{"critical_files","clean_marker"}){CVariant op(CVariant::VariantTypeObject);op["name"]=name;op["ok"]=true;v["operations"].push_back(op);}assert(WritePeerJson(Get().directory+"/compat-response.json",v));}
static void response(const std::string& status,bool malformed=false){auto v=identity();v["status"]=status;v["participant"]="command-center-json";if(!malformed)v["global_safe_to_terminate"]=false;assert(WritePeerJson(Get().directory+"/response.json",v));}
static void ready(CApplication& app){Pump(app);active();Pump(app);assert(Test::freezes==1);response("PLAYBACK_CHECKPOINTED");Pump(app);response("PARTICIPANT_COMPLETE");compatResponse();}
int main(int argc,char**argv){
 assert(argc==3);std::string mode=argv[1];Test::root=argv[2];CApplication app;
 if(mode=="foreign" || mode=="generic-save")Test::foreign={"service.unknown:service.py"};
 if(mode=="generic-save"){InfinityScriptPersistence::Admit(123,"service.unknown:service.py");InfinityScriptPersistence::Observed(123);}
 if(mode=="pvr")Test::pvrStopped=false;
 if(mode=="pvr-retained")Test::pvrOwners=true;
 if(mode=="init")Test::initialized=false;
 assert(!Request(SESSION,OWNER,getpid()));
 assert(Status(SESSION,OWNER,getpid()).find("startup_engine_owner_not_registered")!=std::string::npos);
 assert(!AuthorizeTermination(SESSION,OWNER,getpid()));
 assert(RegisterStartupOwner(OWNER,getpid(),Test::root));
 assert(!RegisterStartupOwner("33333333-3333-4333-8333-333333333333",getpid(),Test::root));
 assert(!Request(SESSION,OWNER,getpid()));
 assert(Status(SESSION,OWNER,getpid()).find("startup_owner_publication_pending")!=std::string::npos);
 const std::string dir=Test::root+"/addon_data/script.infinity.commandcenter/.android-checkpoint";
 std::filesystem::create_directories(dir);
 if(mode.rfind("startup-",0)==0){
   auto old=identity();old["owner"]="44444444-4444-4444-8444-444444444444";old["native_api"]=1;
   assert(WriteJson(dir+"/engine.json",old));
   auto journal=CVariant(CVariant::VariantTypeObject);journal["owner"]["pid"]=static_cast<int>(getpid());
   journal["owner"]["token"]="55555555-5555-4555-8555-555555555555";
   assert(WritePeerJson(dir+"/participant.json",journal));
   if(mode=="startup-old-live")Test::oldRetired=false;
   if(mode=="startup-own-lost")Test::ownLease=false;
   if(mode=="startup-malformed"){std::ofstream f(dir+"/engine.json");f<<"malformed";}
   if(mode!="startup-cas"){assert(!PublishStartupOwner());assert(!Request(SESSION,OWNER,getpid()));return 0;}
   assert(PublishStartupOwner());CVariant published;assert(ReadJson(dir+"/engine.json",published));
   assert(published["previous_owner"]["token"].asString()==journal["owner"]["token"].asString());
   assert(published["owner"].asString()==OWNER);assert(PublishStartupOwner());
   CVariant again;assert(ReadJson(dir+"/engine.json",again));assert(Test::Encode(again)==Test::Encode(published));return 0;
 }
 assert(PublishStartupOwner());assert(!IsActive());
 assert(!Request("bad",OWNER,getpid()));assert(Request(SESSION,OWNER,getpid()));
 assert(Status(SESSION,OWNER,getpid()).find("QUIESCE")!=std::string::npos);
 assert(!Request("session-0000000000000002",OWNER,getpid()));
 assert(!AuthorizeTermination(SESSION,OWNER,getpid()));
 if(mode=="init"||mode=="pvr"||mode=="pvr-retained"){Pump(app);assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 if(mode=="prewrite"){
   // Already-admitted command guard delays freeze; new commands are refused.
   Pump(app);active();{AcceptedPlaybackWorkScope old;CheckpointWriteGuard command("playback-command");CheckpointWriteGuard pvr("pvr-start");assert(!command);assert(!pvr);Pump(app);assert(Test::freezes==0);}
   Pump(app);assert(Test::freezes==1);return 0;
 }
 if(mode=="malformed-active"){Pump(app);active(true);Pump(app);assert(Test::freezes==0);return 0;}
 if(mode=="playback-fail"){Test::playbackOk=false;Pump(app);active();Pump(app);assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 ready(app);
 if(mode=="compat-fail"){compatResponse("CHECKPOINT_FAILED");Pump(app);assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 if(mode=="compat-malformed"){compatResponse("PARTICIPANT_COMPLETE",true);Pump(app);assert(Get().phase=="QUIESCE");assert(!AuthorizeTermination(SESSION,OWNER,getpid()));return 0;}
 if(mode=="source-drift"){Test::compatResidents=0;Pump(app);assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 if(mode=="cc-fail"){response("CHECKPOINT_FAILED");Pump(app);assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 if(mode=="malformed-response"){response("PARTICIPANT_COMPLETE",true);Pump(app);assert(Get().phase=="QUIESCE");return 0;}
 if(mode=="busy"){Test::jobs=1;Pump(app);assert(Get().phase=="QUIESCE");assert(!AuthorizeTermination(SESSION,OWNER,getpid()));Test::jobs=0;}
 if(mode=="settings-fail")Test::settingsOk=false;
 if(mode=="audio-fail")Test::audioOk=false;
 if(mode=="deferred-fail")Test::deferredOk=false;
 if(mode=="multi-owner-fail"){Test::skinOk=false;Test::settingsOk=false;Test::profilesOk=false;}
 if(mode=="unknown-job"||mode=="unknown-running"||mode=="receipt-missing")Test::unknownJobs=1;
 if(mode=="receipt-missing")Test::receiptMissing=true;
 if(mode=="unknown-running"){Test::unknownRunning=true;Pump(app);assert(!Get().owners["kodi_settings"].complete);assert(!AuthorizeTermination(SESSION,OWNER,getpid()));Test::unknownRunning=false;}
 if(mode=="optional-job")Test::optionalJobs=1;
 if(mode=="generic-save"){const auto path=Test::root+"/provider.json";std::ofstream(path)<<"saved";InfinityScriptPersistence::Touch(123,path);InfinityScriptPersistence::Retired(123);Test::foreign.clear();}
 if(mode=="foreign"){Test::foreign.clear();Get().expires=Clock::now();} // A disappeared thread still has no durability receipt.
 for(int attempt=0;attempt<100 && Get().phase=="QUIESCE";++attempt){Pump(app);std::this_thread::sleep_for(std::chrono::milliseconds(1));}
 if(mode=="settings-fail"||mode=="audio-fail"||mode=="deferred-fail"||mode=="unknown-job"||mode=="unknown-running"||mode=="receipt-missing"||mode=="foreign"){
   assert(Get().phase=="CHECKPOINT_FAILED");assert(!AuthorizeTermination(SESSION,OWNER,getpid()));
   const auto status=Status(SESSION,OWNER,getpid());
   if(mode=="unknown-job"){assert(Get().owners["kodi_settings"].complete);assert(Get().owners["profiles"].complete);assert(Get().owners["native_databases"].complete);}
   assert(status.find("\"blockers\"")!=std::string::npos);
   return 0;
 }
 if(mode=="multi-owner-fail"){
   assert(Get().phase=="CHECKPOINT_FAILED");assert(Get().inventoryComplete);assert(!AuthorizeTermination(SESSION,OWNER,getpid()));
   const auto status=Status(SESSION,OWNER,getpid());
   assert(status.find("skin_settings_save_failed")!=std::string::npos);
   assert(status.find("settings_save_failed")!=std::string::npos);
   assert(status.find("profiles_save_failed")!=std::string::npos);
   assert(Get().owners["favourites"].complete);
   assert(Get().owners["peripherals"].complete);
   assert(Get().owners["audio_policy"].complete);
   return 0;
 }
 assert(Get().phase=="SAFE_TO_TERMINATE");const auto safe=Status(SESSION,OWNER,getpid());assert(safe==Status(SESSION,OWNER,getpid()));
 if(mode=="generic-late"){InfinityScriptPersistence::Admit(124,"late:service.py");assert(!AuthorizeTermination(SESSION,OWNER,getpid()));assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 if(mode=="latewrite"){
   CheckpointWriteGuard refused("kodi_settings");assert(!refused);
   RecordFailure("xml_files","late_required_save");assert(!AuthorizeTermination(SESSION,OWNER,getpid()));return 0;
 }
 if(mode=="deadline"){Get().expires=Clock::now();assert(!AuthorizeTermination(SESSION,OWNER,getpid()));assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 if(mode=="pvr-late"){Test::pvrOwners=true;assert(!AuthorizeTermination(SESSION,OWNER,getpid()));assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
 if(mode=="own-lease-lost"){Test::ownLease=false;assert(!AuthorizeTermination(SESSION,OWNER,getpid()));assert(Get().phase=="CHECKPOINT_FAILED");return 0;}
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
    parser.add_argument("--installed-versions", action="store_true")
    args = parser.parse_args()
    source = args.runtime / "xbmc"
    with tempfile.TemporaryDirectory(prefix="native-coordinator-host-") as temp:
        temp = Path(temp)
        for rel in ["platform/android/activity/InfinityAndroidCheckpoint.cpp",
                    "platform/android/activity/InfinityAndroidCheckpoint.h",
                    "platform/android/activity/InfinityCheckpointFile.h",
                    "platform/android/activity/InfinityScriptPersistence.h",
                    "dbwrappers/InfinityDatabaseBarrier.h", "utils/JobCheckpoint.h", "utils/Variant.h", "utils/Variant.cpp"]:
            target = temp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / rel, target)
        (temp / "stubs.h").write_text(STUBS)
        boundaries = ["InfinityCheckpointXml.h", "InfinityPlaybackCheckpoint.h", "JNIMainActivity.h"]
        for name in boundaries:
            (temp / "platform/android/activity" / name).write_text('#pragma once\n#include "stubs.h"\n')
        for rel in ["ServiceBroker.h", "addons/Skin.h", "application/Application.h", "application/ApplicationPlayer.h",
                    "favourites/FavouritesService.h", "filesystem/Directory.h", "filesystem/SpecialProtocol.h",
                    "interfaces/AnnouncementManager.h", "interfaces/generic/ScriptInvocationManager.h",
                    "peripherals/Peripherals.h", "profiles/ProfileManager.h", "pvr/PVRManager.h", "pvr/addons/PVRClients.h",
                    "settings/Settings.h", "settings/SettingsComponent.h", "utils/JSONVariantParser.h",
                    "utils/JSONVariantWriter.h", "utils/JobManager.h"]:
            target = temp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('#pragma once\n#include "stubs.h"\n')
        (temp / "harness.cpp").write_text(HARNESS.replace("0.3.5.19", "0.3.5.20").replace("0.7.2", "0.8.2") if args.installed_versions else HARNESS)
        binary = temp / "test"
        subprocess.run(["g++", "-std=c++17", "-DTARGET_ANDROID", "-Wno-unused-parameter",
                        "-I", str(temp), "-c", str(temp / "utils/Variant.cpp"),
                        "-o", str(temp / "variant.o")], check=True)
        subprocess.run(["g++", "-std=c++17", "-DTARGET_ANDROID", "-Wall", "-Wextra", "-Werror", "-pthread",
                        "-I", str(temp), str(temp / "harness.cpp"), str(temp / "variant.o"),
                        "-o", str(binary)], check=True)
        modes = ["fixture", "init", "pvr", "prewrite", "malformed-active", "playback-fail", "cc-fail",
                 "malformed-response", "busy", "settings-fail", "foreign", "latewrite", "deadline", "lifecycle",
                 "compat-fail", "compat-malformed", "source-drift", "audio-fail",
                 "startup-cas", "startup-old-live", "startup-own-lost", "startup-malformed",
                 "pvr-retained", "pvr-late", "own-lease-lost", "deferred-fail", "unknown-job", "unknown-running", "receipt-missing", "optional-job", "generic-save", "generic-late", "multi-owner-fail"]
        for mode in modes:
            output = subprocess.check_output([str(binary), mode, str(temp / mode)], text=True, timeout=10)
            if mode == "fixture" and args.fixture:
                args.fixture.parent.mkdir(parents=True, exist_ok=True)
                args.fixture.write_text(output)
        print(f"PASS: actual native coordinator + CVariant, {len(modes)} controlled-boundary scenarios")


if __name__ == "__main__":
    main()
