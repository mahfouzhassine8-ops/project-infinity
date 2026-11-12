#pragma once
// Test backends only. The production translation unit is included unchanged.
#include <map>
#include <memory>
#include <string>
#include <vector>
#include <cstdint>

#define JNIEXPORT
#define JNICALL
using jlong = int64_t;
using jsize = int;
using jbyte = int8_t;
using jboolean = unsigned char;
using jclass = void*;
using jstring = const std::string*;
using jbyteArray = std::vector<jbyte>*;
constexpr jboolean JNI_TRUE = 1, JNI_FALSE = 0;
struct JNIEnv {
  jsize GetStringUTFLength(jstring s) { return s->size(); }
  const char* GetStringUTFChars(jstring s, void*) { return s->c_str(); }
  void ReleaseStringUTFChars(jstring, const char*) {}
  jbyteArray NewByteArray(jsize n) { return new std::vector<jbyte>(n); }
  void SetByteArrayRegion(jbyteArray a, jsize start, jsize n, const jbyte* p)
  { std::copy(p, p+n, a->begin()+start); }
};
class CVariant {
public:
  enum Type { VariantTypeObject };
  CVariant() = default;
  explicit CVariant(Type) {}
  CVariant& operator[](const std::string& key) { return fields[key]; }
  CVariant& operator=(const std::string& s) { value='"'+s+'"'; return *this; }
  CVariant& operator=(const char* s) { return *this=std::string(s); }
  CVariant& operator=(int64_t n) { value=std::to_string(n); return *this; }
  CVariant& operator=(int n) { return *this=static_cast<int64_t>(n); }
  CVariant& operator=(bool b) { value=b?"true":"false"; return *this; }
  std::string value;
  std::map<std::string,CVariant> fields;
};
struct CJSONVariantWriter {
  static bool Write(const CVariant& x, std::string& result, bool) {
    result="{";bool first=true;
    for(const auto& entry:x.fields) {if(!first)result+=',';first=false;result+='"'+entry.first+'"'+':'+entry.second.value;}
    result+='}';return true;
  }
};
struct CVideoInfoTag { std::string m_type="movie",m_strTitle="Fixture"; int m_iSeason=-1,m_iEpisode=-1; };
struct Property { std::string value; std::string asString() const { return value; } };
struct CFileItem {
  std::string path="https://media.invalid/public.mp4", origin="provider-movie";
  CVideoInfoTag tag;
  std::string GetDynPath() const { return path; }
  Property GetProperty(const std::string&) const { return {origin}; }
  std::string GetLabel() const { return "Fixture"; }
  bool HasVideoInfoTag() const { return true; }
  const CVideoInfoTag* GetVideoInfoTag() const { return &tag; }
};
struct CApplicationPlayer {
  bool playing=true,paused=false,pauseable=true,seekable=true;
  int pauses=0,seeks=0;
  int64_t position=123000,duration=7200000;
  bool IsPlayingVideo() const { return playing; }
  int64_t GetTime() const { return position; }
  int64_t GetTotalTime() const { return duration; }
  bool IsPaused() const { return paused; }
  bool CanPause() const { return pauseable; }
  bool CanSeek() const { return seekable; }
  void Pause() { paused=!paused; ++pauses; }
  void SeekTime(int64_t p) { position=p; ++seeks; }
};
struct Application {
  bool stopping=false;
  std::shared_ptr<CFileItem> item=std::make_shared<CFileItem>();
  std::shared_ptr<CApplicationPlayer> player=std::make_shared<CApplicationPlayer>();
  bool IsStopping() const { return stopping; }
  template<class T> std::shared_ptr<T> GetComponent() { return player; }
  std::shared_ptr<CFileItem> CurrentFileItemPtr() { return item; }
};
inline Application g_application;
namespace KODI { namespace MESSAGING { struct ThreadMessageCallback { void(*callback)(void*);void* userptr; }; } }
constexpr int TMSG_CALLBACK=800;
struct Messenger {
  std::vector<KODI::MESSAGING::ThreadMessageCallback*> pending;
  void PostMsg(int,int,int,void* p) { pending.push_back(static_cast<KODI::MESSAGING::ThreadMessageCallback*>(p)); }
  void Drain() { auto queue=pending;pending.clear();for(auto* cb:queue) cb->callback(cb->userptr); }
};
inline Messenger messenger;
struct Settings {
  std::string skin="skin.infinity.diggz";
  std::string GetString(const std::string&) const { return skin; }
};
inline Settings settings;
struct SettingsComponent { Settings* GetSettings() { return &settings; } };
inline SettingsComponent settingsComponent;
struct CServiceBroker {
  static Messenger* GetAppMessenger() { return &messenger; }
  static SettingsComponent* GetSettingsComponent() { return &settingsComponent; }
};
namespace InfinityAndroidCheckpoint { inline bool active=false; inline bool IsActive() { return active; } }
namespace KODI { namespace UTILITY { struct CDigest {
  enum class Type { SHA256 };
  static std::string Calculate(Type,const std::string& s) { return "test-digest:"+s; }
}; } }
