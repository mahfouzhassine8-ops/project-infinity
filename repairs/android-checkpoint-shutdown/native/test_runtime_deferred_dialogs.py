#!/usr/bin/env python3
"""Exercise the production deferred-dialog checkpoint adapters with failure injection."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

RUNTIME = Path(os.environ.get("INFINITY_RUNTIME_NATIVE", "/workspace/scratch/a86210039ee8/runtime-native"))


def extract(source, signature):
    start = source.index(signature)
    return source[start:source.index("\n}\n", start) + 3]


class DeferredDialogTests(unittest.TestCase):
    def test_production_capture_and_failure_retention(self):
        files = {
            "song": "music/dialogs/GUIDialogSongInfo.cpp",
            "album": "music/dialogs/GUIDialogMusicInfo.cpp",
            "video": "video/dialogs/GUIDialogVideoInfo.cpp",
            "calibration": "settings/windows/GUIWindowSettingsScreenCalibration.cpp",
            "display": "settings/DisplaySettings.cpp",
        }
        sources = {key: (RUNTIME / "xbmc" / path).read_text() for key, path in files.items()}
        bodies = []
        for key, cls in [("song", "CGUIDialogSongInfo"), ("album", "CGUIDialogMusicInfo"),
                         ("video", "CGUIDialogVideoInfo"), ("calibration", "CGUIWindowSettingsScreenCalibration")]:
            bodies.append(extract(sources[key], f"bool {cls}::CheckpointPendingForAndroidExit()"))
        for sig in ["bool CDisplaySettings::Save(TiXmlNode *settings) const",
                    "void CDisplaySettings::UpdateCalibrations()",
                    "bool CDisplaySettings::CaptureCalibrationsForAndroidExit("]:
            bodies.append(extract(sources["display"], sig))
        bodies.append(extract(sources["song"], "bool InfinityAndroidCheckpoint::CheckpointDeferredDialogState()"))
        # Verify actual UI mutation points participate; no UI/deinit is synthesized by capture.
        for key, cls in [("song", "CGUIDialogSongInfo"), ("album", "CGUIDialogMusicInfo"),
                         ("video", "CGUIDialogVideoInfo")]:
            self.assertIn("CheckpointWriteGuard", extract(sources[key], f"void {cls}::SetUserrating("))
        self.assertIn("m_checkpointDirtyResolutions.insert", extract(sources["calibration"],
                      "bool CGUIWindowSettingsScreenCalibration::UpdateFromControl("))
        self.assertIn("m_checkpointDirtyResolutions.insert", extract(sources["calibration"],
                      "void CGUIWindowSettingsScreenCalibration::ResetCalibration()"))
        with tempfile.TemporaryDirectory(prefix="infinity-deferred-dialogs-") as directory:
            cpp = Path(directory) / "dialogs.cpp"
            cpp.write_text(PRELUDE + "\n".join(bodies) + TESTS)
            exe = Path(directory) / "dialogs"
            compiled = subprocess.run([shutil.which("c++") or "c++", "-std=c++17", "-DTARGET_ANDROID",
                                       "-Wall", "-Wextra", "-Werror", "-pedantic", "-O2", "-pthread",
                                       str(cpp), "-o", str(exe)], text=True, capture_output=True, timeout=60)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(exe)], text=True, capture_output=True, timeout=30)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertIn("PASS", tested.stdout)


PRELUDE = r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
#define CHECK(x) do { if (!(x)) throw std::runtime_error(std::string("line ") + std::to_string(__LINE__) + ": " #x); } while (false)
namespace InfinityAndroidCheckpoint {
bool persist=true, admit=true; uint64_t failures=0; int settingsCalls=0, gameCalls=0;
bool pendingSettings=true, pendingGame=true;
bool IsPersistingOnThisThread() { return persist; }
void RecordFailure(const char*, const char*) { ++failures; }
uint64_t ErrorGeneration() { return failures; }
bool HasFailureSince(uint64_t old) { return failures != old; }
struct CheckpointWriteGuard { explicit CheckpointWriteGuard(const char*) {} explicit operator bool() const { return admit; } };
bool CheckpointPendingSettingsDialogs() { ++settingsCalls; return pendingSettings; }
bool CheckpointPendingGameDialogs() { ++gameCalls; return pendingGame; }
bool CheckpointDeferredDialogState();
}
namespace InfinityDatabaseBarrier {
struct Snapshot { int failures=0, rejectedWrites=0, unsupportedOwners=0; } snapshot;
Snapshot GetSnapshot() { return snapshot; }
}
using MediaType = std::string;
const MediaType MediaTypeSong="song", MediaTypeMovie="movie", MediaTypeEpisode="episode",
 MediaTypeMusicVideo="musicvideo", MediaTypeTvShow="tvshow", MediaTypeSeason="season";
struct MusicTag {
 int rating=2, id=7, album=8; MediaType type=MediaTypeSong;
 int GetUserrating() const { return rating; } int GetDatabaseId() const { return id; }
 int GetAlbumId() const { return album; } const MediaType& GetType() const { return type; }
};
struct CVideoInfoTag { int m_iDbId=9, m_iUserRating=2; MediaType m_type=MediaTypeMovie; };
struct CFileItem {
 MusicTag music; CVideoInfoTag video; bool hasMusic=true, hasVideo=true, plugin=false;
 bool HasMusicInfoTag() const { return hasMusic; } bool HasVideoInfoTag() const { return hasVideo; }
 MusicTag* GetMusicInfoTag() { return &music; } CVideoInfoTag* GetVideoInfoTag() { return &video; }
 bool IsPlugin() const { return plugin; } std::string GetPath() const { return "song.flac"; }
};
struct CSong { int idSong=-1, userrating=0; };
struct CAlbum { int idAlbum=-1, iUserrating=0; };
struct DbState {
 bool open=true, write=true, read=true, corrupt=false, closeFail=false, pathKnown=true;
 int opens=0, writes=0, reads=0, closes=0; int song=2, album=2, video=2;
} db;
struct CMusicDatabase {
 bool Open() { ++db.opens; return db.open; }
 void Close() { ++db.closes; if(db.closeFail) ++InfinityDatabaseBarrier::snapshot.failures; }
 bool SetSongUserrating(int, int rating) { ++db.writes; if(db.write) db.song=rating; return db.write; }
 bool SetAlbumUserrating(int, int rating) { ++db.writes; if(db.write) db.album=rating; return db.write; }
 bool GetSong(int id, CSong& out) { ++db.reads; out.idSong=id; out.userrating=db.song+(db.corrupt?1:0); return db.read; }
 bool GetSongByFileName(const std::string&, CSong& out) { out.idSong=7; return db.pathKnown; }
 bool GetAlbum(int id, CAlbum& out, bool) { ++db.reads; out.idAlbum=id; out.iUserrating=db.album+(db.corrupt?1:0); return db.read; }
};
struct CVideoDatabase {
 bool Open() { ++db.opens; return db.open; }
 void Close() { ++db.closes; if(db.closeFail) ++InfinityDatabaseBarrier::snapshot.failures; }
 bool SetVideoUserRating(int, int rating, const MediaType&) { ++db.writes; if(db.write) db.video=rating; return db.write; }
 bool Read(CVideoInfoTag& out, int id) { ++db.reads; out.m_iDbId=id; out.m_iUserRating=db.video+(db.corrupt?1:0); return db.read; }
 bool GetMovieInfo(const std::string&, CVideoInfoTag& out, int id) { return Read(out,id); }
 bool GetEpisodeInfo(const std::string&, CVideoInfoTag& out, int id) { return Read(out,id); }
 bool GetMusicVideoInfo(const std::string&, CVideoInfoTag& out, int id) { return Read(out,id); }
 bool GetTvShowInfo(const std::string&, CVideoInfoTag& out, int id) { return Read(out,id); }
 bool GetSeasonInfo(int id, CVideoInfoTag& out, bool) { return Read(out,id); }
};
struct Window { virtual ~Window()=default; bool active=false; bool IsActive() const { return active; } bool IsDialogRunning() const { return active; } };
struct CGUIDialogSongInfo : Window {
 std::shared_ptr<CFileItem> m_song=std::make_shared<CFileItem>(); int m_startUserrating=2;
 bool m_hasUpdatedUserrating=false; bool CheckpointPendingForAndroidExit();
};
struct CGUIDialogMusicInfo : Window {
 std::shared_ptr<CFileItem> m_item=std::make_shared<CFileItem>(); int m_startUserrating=2;
 bool m_hasUpdatedUserrating=false, m_bArtistInfo=false; bool CheckpointPendingForAndroidExit();
};
struct CGUIDialogVideoInfo : Window {
 std::shared_ptr<CFileItem> m_movieItem=std::make_shared<CFileItem>(); int m_startUserrating=2;
 bool m_hasUpdatedUserrating=false; bool CheckpointPendingForAndroidExit();
};
enum RESOLUTION { RES_INVALID=-1, RES_WINDOW=15, RES_DESKTOP=16, RES_CUSTOM=17 };
struct TestOverscan { int left=0,top=0,right=100,bottom=100; }; // real OVERSCAN comparison is non-const
struct RESOLUTION_INFO { std::string strMode; TestOverscan Overscan; int iSubtitles=90; float fPixelRatio=1; };
struct TiXmlNode {
 std::vector<std::unique_ptr<TiXmlNode>> children;
 TiXmlNode* InsertEndChild(const TiXmlNode&) { children.emplace_back(std::make_unique<TiXmlNode>()); return children.back().get(); }
 const TiXmlNode* FirstChild() const { return children.empty()?nullptr:children.front().get(); }
};
struct TiXmlElement : TiXmlNode { explicit TiXmlElement(const char*) {} };
struct XMLUtils {
 static inline int fields=0, failedField=-1; static inline bool emptyField=false;
 static TiXmlNode* Field(TiXmlNode* parent) {
  ++fields; if(fields==failedField && !emptyField) return nullptr;
  TiXmlNode node; auto* result=parent->InsertEndChild(node);
  if(fields!=failedField || !emptyField) result->InsertEndChild(node);
  return result;
 }
 static TiXmlNode* SetString(TiXmlNode* node,const char*,const std::string&) { return Field(node); }
 static TiXmlNode* SetInt(TiXmlNode* node,const char*,int) { return Field(node); }
 static TiXmlNode* SetFloat(TiXmlNode* node,const char*,float) { return Field(node); }
};
using CCriticalSection=std::recursive_mutex;
struct StringUtils { static bool EqualsNoCase(const std::string& a,const std::string& b) { return a==b; } };
struct CDisplaySettings {
 using ResolutionInfos=std::vector<RESOLUTION_INFO>; ResolutionInfos m_resolutions, m_calibrations;
 mutable CCriticalSection m_critical;
 static CDisplaySettings& GetInstance() { static CDisplaySettings d; return d; }
 bool Save(TiXmlNode*) const; void UpdateCalibrations(); bool CaptureCalibrationsForAndroidExit(const std::set<RESOLUTION>&);
};
constexpr int CONTROL_TOP_LEFT=8, CONTROL_PIXEL_RATIO=11;
struct CGUIWindowSettingsScreenCalibration : Window {
 std::set<RESOLUTION> m_checkpointDirtyResolutions; unsigned m_iCurRes=0; std::vector<RESOLUTION> m_Res{RES_CUSTOM};
 int focused=-1; bool pendingControl=false;
 int GetFocusedControlID() const { return focused; }
 bool UpdateFromControl(int) { if(pendingControl) m_checkpointDirtyResolutions.insert(RES_CUSTOM); return false; }
 bool CheckpointPendingForAndroidExit();
};
constexpr int WINDOW_DIALOG_SONG_INFO=1, WINDOW_DIALOG_MUSIC_INFO=2, WINDOW_DIALOG_VIDEO_INFO=3, WINDOW_SCREEN_CALIBRATION=4;
struct WindowManager {
 std::map<int,Window*> windows;
 template<class T> T* GetWindow(int id) { const auto i=windows.find(id); return i==windows.end()?nullptr:dynamic_cast<T*>(i->second); }
};
struct Gui { WindowManager windows; WindowManager& GetWindowManager() { return windows; } } gui;
struct Settings {
 bool save=true, recordError=false; int saves=0;
 bool Save() { ++saves; if(recordError) InfinityAndroidCheckpoint::RecordFailure("settings","serialize"); return save; }
} settings;
struct SettingsComponent { Settings* GetSettings() { return &settings; } } settingsComponent;
struct CServiceBroker {
 static inline bool guiAvailable=true;
 static Gui* GetGUI() { return guiAvailable?&gui:nullptr; }
 static SettingsComponent* GetSettingsComponent() { return &settingsComponent; }
};
'''

TESTS = r'''
void Reset() {
 db={}; InfinityDatabaseBarrier::snapshot={}; InfinityAndroidCheckpoint::admit=true;
 InfinityAndroidCheckpoint::persist=true; InfinityAndroidCheckpoint::failures=0;
 settings={};
}
int main() {
 CGUIDialogSongInfo song; CGUIDialogMusicInfo album; CGUIDialogVideoInfo video;
 CHECK(song.CheckpointPendingForAndroidExit()); CHECK(db.opens==0);
 song.active=true; CHECK(song.CheckpointPendingForAndroidExit()); CHECK(db.opens==0);
 song.m_song->music.rating=6; CHECK(song.CheckpointPendingForAndroidExit());
 CHECK(db.song==6 && db.writes==1 && db.reads==1 && db.closes==1 && song.m_startUserrating==6);
 CHECK(song.CheckpointPendingForAndroidExit()); CHECK(db.writes==1);
 for (int fail=0; fail<5; ++fail) {
  Reset(); song.m_startUserrating=2; song.m_song->music.rating=7;
  if(fail==0) db.open=false;
  if(fail==1) db.write=false;
  if(fail==2) db.read=false;
  if(fail==3) db.corrupt=true;
  if(fail==4) db.closeFail=true;
  CHECK(!song.CheckpointPendingForAndroidExit()); CHECK(song.m_startUserrating==2);
  CHECK(InfinityAndroidCheckpoint::failures>0);
 }
 Reset(); song.m_song->music.id=-1; CHECK(song.CheckpointPendingForAndroidExit()); CHECK(db.song==7);
 Reset(); song.m_startUserrating=2; db.pathKnown=false;
 CHECK(!song.CheckpointPendingForAndroidExit()); CHECK(db.writes==0);
 Reset(); song.m_song->plugin=true; CHECK(!song.CheckpointPendingForAndroidExit()); CHECK(db.opens==0);
 Reset(); InfinityAndroidCheckpoint::admit=false; CHECK(!song.CheckpointPendingForAndroidExit());
 Reset(); InfinityAndroidCheckpoint::persist=false; CHECK(!song.CheckpointPendingForAndroidExit());
 Reset(); album.active=true; album.m_item->music.rating=8;
 CHECK(album.CheckpointPendingForAndroidExit()); CHECK(db.album==8 && album.m_startUserrating==8);
 Reset(); album.m_startUserrating=2; album.m_bArtistInfo=true;
 CHECK(album.CheckpointPendingForAndroidExit()); CHECK(db.opens==0);
 album.m_bArtistInfo=false; album.m_item->music.album=-1;
 CHECK(!album.CheckpointPendingForAndroidExit()); CHECK(db.writes==0);
 for(const auto& type : {MediaTypeMovie,MediaTypeEpisode,MediaTypeMusicVideo,MediaTypeTvShow,MediaTypeSeason}) {
  Reset(); video.active=true; video.m_startUserrating=2; video.m_movieItem->video.m_iUserRating=9;
  video.m_movieItem->video.m_type=type;
  CHECK(video.CheckpointPendingForAndroidExit()); CHECK(db.video==9 && db.reads==1 && video.m_startUserrating==9);
 }
 for(int fail=0; fail<4; ++fail) {
  Reset(); video.m_startUserrating=2;
  if(fail==0) db.write=false;
  if(fail==1) db.read=false;
  if(fail==2) db.corrupt=true;
  if(fail==3) db.closeFail=true;
  CHECK(!video.CheckpointPendingForAndroidExit()); CHECK(video.m_startUserrating==2);
 }
 Reset(); video.m_movieItem->video.m_type="set"; CHECK(!video.CheckpointPendingForAndroidExit()); CHECK(db.opens==0);
 Reset(); CGUIWindowSettingsScreenCalibration calibration;
 auto& display=CDisplaySettings::GetInstance(); display.m_resolutions.resize(18);
 display.m_resolutions[RES_CUSTOM].strMode="1080p"; display.m_resolutions[RES_CUSTOM].Overscan.left=12;
 CHECK(calibration.CheckpointPendingForAndroidExit()); CHECK(settings.saves==0);
 calibration.active=true; calibration.focused=CONTROL_TOP_LEFT; calibration.pendingControl=true;
 CHECK(calibration.CheckpointPendingForAndroidExit()); CHECK(settings.saves==1);
 CHECK(display.m_calibrations.size()==1 && display.m_calibrations[0].Overscan.left==12);
 { TiXmlNode xml; CHECK(display.Save(&xml)); CHECK(XMLUtils::fields==7); }
 for(int field=1; field<=7; ++field) {
  for(bool empty : {false,true}) {
   TiXmlNode xml; XMLUtils::fields=0; XMLUtils::failedField=field; XMLUtils::emptyField=empty;
   CHECK(!display.Save(&xml));
  }
 }
 XMLUtils::failedField=-1;
 { TiXmlNode xml; CHECK(display.Save(&xml)); }
 CHECK(calibration.m_checkpointDirtyResolutions.empty());
 calibration.pendingControl=false; CHECK(calibration.CheckpointPendingForAndroidExit()); CHECK(settings.saves==1);
 calibration.m_checkpointDirtyResolutions.insert(RES_CUSTOM); settings.save=false;
 CHECK(!calibration.CheckpointPendingForAndroidExit()); CHECK(!calibration.m_checkpointDirtyResolutions.empty());
 settings.save=true; settings.recordError=true;
 CHECK(!calibration.CheckpointPendingForAndroidExit()); CHECK(!calibration.m_checkpointDirtyResolutions.empty());
 settings.recordError=false; CHECK(calibration.CheckpointPendingForAndroidExit());
 calibration.m_checkpointDirtyResolutions.insert(RES_DESKTOP); display.m_resolutions[RES_DESKTOP].strMode="desktop";
 CHECK(!calibration.CheckpointPendingForAndroidExit()); CHECK(!calibration.m_checkpointDirtyResolutions.empty());
 calibration.m_checkpointDirtyResolutions.clear(); calibration.m_checkpointDirtyResolutions.insert(RES_WINDOW);
 CHECK(!calibration.CheckpointPendingForAndroidExit());
 Reset(); calibration.m_checkpointDirtyResolutions.clear(); calibration.active=false;
 song.active=false; album.active=false; video.active=false;
 gui.windows.windows={{1,&song},{2,&album},{3,&video},{4,&calibration}};
 CHECK(InfinityAndroidCheckpoint::CheckpointDeferredDialogState());
 CHECK(InfinityAndroidCheckpoint::settingsCalls==1 && InfinityAndroidCheckpoint::gameCalls==1);
 InfinityAndroidCheckpoint::pendingSettings=false;
 CHECK(!InfinityAndroidCheckpoint::CheckpointDeferredDialogState());
 CHECK(InfinityAndroidCheckpoint::gameCalls==1);
 CServiceBroker::guiAvailable=false;
 CHECK(!InfinityAndroidCheckpoint::CheckpointDeferredDialogState());
 std::cout << "PASS deferred dialog capture, readback, dirty-only saves and failure retention\n";
}
'''

if __name__ == "__main__":
    unittest.main()
