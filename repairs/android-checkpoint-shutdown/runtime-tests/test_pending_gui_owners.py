#!/usr/bin/env python3
"""Compile actual pending-GUI checkpoint methods and production slider assignment."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "native"))
from test_checked_sqlite import extract_function


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    xbmc = args.source_root / "xbmc"
    settings = (xbmc / "settings/dialogs/GUIDialogSettingsBase.cpp").read_text()
    games = (xbmc / "games/dialogs/osd/DialogGameVideoSelect.cpp").read_text()
    controls = (xbmc / "settings/windows/GUIControlSettings.cpp").read_text()
    methods = []
    for source, registry, signatures in [
        (settings, "PendingSettingsOwners", [
            "bool InfinityAndroidCheckpoint::CheckpointPendingSettingsDialogs()",
            "bool CGUIDialogSettingsBase::CheckpointPendingForAndroidExit()",
        ]),
        (games, "PendingGameOwners", [
            "bool InfinityAndroidCheckpoint::CheckpointPendingGameDialogs()",
            "bool CDialogGameVideoSelect::CheckpointPendingForAndroidExit()",
            "bool CDialogGameVideoSelect::SaveSettingsChecked(bool captureCurrent)",
        ]),
    ]:
        begin = source.index("struct " + registry)
        end = source.index("} // namespace", begin)
        methods.append(source[begin:end])
        methods.extend(extract_function(source, signature) for signature in signatures)
    methods.append(extract_function(controls, "bool CGUIControlSliderSetting::OnClick()"))
    # Validate that real lifecycle paths wire the tested registry/helpers.
    assert "owners.dialogs.insert(this);" in settings and "owners.dialogs.erase(this);" in settings
    assert "owners.abandonedPendingValue = true;" in settings
    assert "owners.dialogs.insert(this);" in games and "owners.dialogs.erase(this);" in games
    assert "owners.abandonedSettings = true;" in games
    for signature in ["bool CGUIDialogSettingsBase::OnMessage(",
                      "void CGUIDialogSettingsBase::OnTimeout()",
                      "void CGUIDialogSettingsBase::OnClick("]:
        assert 'CheckpointWriteGuard write("deferred_dialog_state")' in extract_function(settings, signature)
    for signature in ["bool CDialogGameVideoSelect::OnMessage(",
                      "void CDialogGameVideoSelect::FrameMove()",
                      "void CDialogGameVideoSelect::SaveSettings()"]:
        assert 'CheckpointWriteGuard write("deferred_dialog_state")' in extract_function(games, signature)
    code = r'''
#define TARGET_ANDROID 1
#include <cstdint>
#include <functional>
#include <iostream>
#include <memory>
#include <mutex>
#include <set>
#include <stdexcept>
#include <string>
#include <typeinfo>

namespace InfinityAndroidCheckpoint {
bool permitted=true, persisting=true;
uint64_t errors=0;
struct CheckpointWriteGuard {
  explicit CheckpointWriteGuard(const char*){}
  explicit operator bool() const{return permitted;}
};
bool IsPersistingOnThisThread(){return persisting;}
uint64_t ErrorGeneration(){return errors;}
bool HasFailureSince(uint64_t before){return errors!=before;}
void RecordFailure(const char*,const char*){++errors;}
bool CheckpointPendingSettingsDialogs();
bool CheckpointPendingGameDialogs();
}
enum class SettingType { Integer,Number,String,Boolean,List };
struct CSetting { virtual ~CSetting()=default; virtual SettingType GetType() const=0; };
struct CSettingInt:CSetting {
  int value=0,calls=0; bool fail=false; std::function<void()> callback;
  SettingType GetType() const override{return SettingType::Integer;}
  bool SetValue(int input){++calls;if(fail)return false;value=input;if(callback)callback();return true;}
};
struct CSettingNumber:CSetting {
  double value=0; SettingType GetType() const override{return SettingType::Number;}
  bool SetValue(double input){value=input;return true;}
};
struct CGUISettingsSliderControl {int value=0; int GetIntValue() const{return value;} float GetFloatValue() const{return static_cast<float>(value);}};
class CGUIControlBaseSetting {
public:
  virtual ~CGUIControlBaseSetting()=default;
  virtual bool OnClick(){++clicks;return true;}
  int clicks=0; bool valid=true;
  void SetValid(bool v){valid=v;} bool IsValid()const{return valid;}
};
class CGUIControlSpinExSetting:public CGUIControlBaseSetting {};
class CGUIControlEditSetting:public CGUIControlBaseSetting {};
class CGUIControlRangeSetting:public CGUIControlBaseSetting {};
class CGUIControlRadioButtonSetting:public CGUIControlBaseSetting {};
class CGUIControlSliderSetting:public CGUIControlBaseSetting {
public:
  std::shared_ptr<CSetting> m_pSetting;
  CGUISettingsSliderControl* m_pSlider=nullptr;
  bool OnClick() override;
};
class CGUIDialogSettingsBase {
public:
  std::shared_ptr<CGUIControlBaseSetting> m_delayedSetting;
  bool CheckpointPendingForAndroidExit();
};
struct CGameSettings {
  int value=0;
  bool operator!=(const CGameSettings& other) const{return value!=other.value;}
};
struct CMediaSettings {
  CGameSettings defaults,current;
  static CMediaSettings& GetInstance(){static CMediaSettings instance;return instance;}
  CGameSettings& GetDefaultGameSettings(){return defaults;}
  CGameSettings& GetCurrentGameSettings(){return current;}
};
struct Settings {
  bool fail=false;int saves=0;
  bool Save(){++saves;return !fail;}
};
struct SettingsComponent {
  Settings settings;
  Settings* GetSettings(){return &settings;}
};
struct CServiceBroker {
  static SettingsComponent* GetSettingsComponent(){static SettingsComponent component;return &component;}
};
class CDialogGameVideoSelect {
public:
  bool running=false,m_checkpointSettingsDirty=false;
  bool IsDialogRunning()const{return running;}
  bool CheckpointPendingForAndroidExit();
  bool SaveSettingsChecked(bool captureCurrent);
};
// @PRODUCTION@
void require(bool ok,const char* text){if(!ok)throw std::runtime_error(text);}
int main(){
  using namespace InfinityAndroidCheckpoint;
  CGUIDialogSettingsBase dialog;PendingSettings().dialogs.insert(&dialog);
  require(CheckpointPendingSettingsDialogs(),"clean dialog failed");
  auto value=std::make_shared<CSettingInt>();CGUISettingsSliderControl slider;slider.value=7;
  auto control=std::make_shared<CGUIControlSliderSetting>();control->m_pSetting=value;control->m_pSlider=&slider;
  dialog.m_delayedSetting=control;
  require(CheckpointPendingSettingsDialogs(),"accepted slider assignment failed");
  require(value->value==7 && value->calls==1 && !dialog.m_delayedSetting,"accepted value not applied once");
  require(CheckpointPendingSettingsDialogs() && value->calls==1,"second poll replayed assignment");
  dialog.m_delayedSetting=control;value->fail=true;slider.value=9;
  require(!CheckpointPendingSettingsDialogs(),"setter failure reported success");
  require(dialog.m_delayedSetting==control && value->value==7,"failed accepted value discarded");
  value->fail=false;
  require(CheckpointPendingSettingsDialogs() && value->value==9,"retained assignment could not retry");
  auto toggle=std::make_shared<CGUIControlRadioButtonSetting>();dialog.m_delayedSetting=toggle;
  require(!CheckpointPendingSettingsDialogs() && toggle->clicks==0 && dialog.m_delayedSetting==toggle,"toggle/interactive action replayed");
  dialog.m_delayedSetting=control;permitted=false;
  const int before=value->calls;require(!CheckpointPendingSettingsDialogs() && value->calls==before,"unauthorized pending mutation");
  permitted=true;value->callback=[] {RecordFailure("test","side_effect_failed");};
  require(!CheckpointPendingSettingsDialogs() && dialog.m_delayedSetting==control,"side-effect failure lost obligation");
  value->callback={};dialog.m_delayedSetting.reset();PendingSettings().dialogs.erase(&dialog);
  PendingSettings().abandonedPendingValue=true;
  require(!CheckpointPendingSettingsDialogs(),"destroyed pending owner accepted");
  PendingSettings().abandonedPendingValue=false;
  std::cout<<"PASS pending_settings_exact_assignment_no_replay_and_failure_retention\n";

  CDialogGameVideoSelect game;PendingGames().dialogs.insert(&game);
  auto& media=CMediaSettings::GetInstance();auto& saved=CServiceBroker::GetSettingsComponent()->settings;
  media.defaults.value=1;media.current.value=2;
  require(CheckpointPendingGameDialogs() && media.defaults.value==1 && saved.saves==0,"inactive dialog copied unrelated game");
  game.running=true;
  require(CheckpointPendingGameDialogs() && media.defaults.value==2 && saved.saves==1,"active accepted game defaults not saved");
  require(CheckpointPendingGameDialogs() && saved.saves==1,"clean game defaults saved again");
  media.current.value=3;saved.fail=true;
  require(!CheckpointPendingGameDialogs() && game.m_checkpointSettingsDirty,"failed defaults save lost obligation");
  game.running=false;media.current.value=99;saved.fail=false;
  require(CheckpointPendingGameDialogs() && media.defaults.value==3 && !game.m_checkpointSettingsDirty,"closed failed owner copied unrelated current state or could not retry");
  PendingGames().dialogs.erase(&game);PendingGames().abandonedSettings=true;
  require(!CheckpointPendingGameDialogs(),"destroyed failed game owner accepted");
  std::cout<<"PASS game_defaults_dirty_only_save_and_closed_owner_failure_retry\n";
}
'''
    with tempfile.TemporaryDirectory(prefix="infinity-pending-gui-") as temp:
        cpp, binary = Path(temp) / "test.cpp", Path(temp) / "test"
        cpp.write_text(code.replace("// @PRODUCTION@", "\n".join(methods)))
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread",
                        str(cpp), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)


if __name__ == "__main__":
    main()
