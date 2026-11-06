"""Compile actual candidate helpers/dialog functions with bounded UI/file stubs.
Uses actual Kodi CVariant/JSON codecs and pinned RapidJSON1.1.0; no APK/device.
"""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;NATIVE=Path('/tmp/kodi451-restored-native');OUT=Path('/dev/shm/infinity-downloads-native-host');OUT.mkdir(exist_ok=True)
cpp=(HERE/'native/xbmc/video/windows/GUIWindowVideoNav.cpp').read_text();dialog=(HERE/'native/xbmc/dialogs/GUIDialogMediaSource.cpp').read_text()
helpers=cpp[cpp.index('std::string DownloadsSourceKey'):cpp.index('\n}\n#endif',cpp.index('std::string DownloadsSourceKey'))]
functions=dialog[dialog.index('bool CGUIDialogMediaSource::ShowAndAddMediaSourceWithResult'):dialog.index('bool CGUIDialogMediaSource::ShowAndAddMediaSource(',dialog.index('bool CGUIDialogMediaSource::ShowAndAddMediaSourceWithResult'))]
start=cpp.index('    if (m_infinityDownloads && g_SkinInfo &&');end=cpp.index('\n#endif',start);filtercode=cpp[start:end]
setup=r'''
#include <cassert>
#include <functional>
#include <iomanip>
#include <iostream>
#include <memory>
#include <set>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <openssl/evp.h>
#include "utils/Variant.h"
#include "utils/JSONVariantParser.h"
#include "utils/JSONVariantWriter.h"
// Exact called SHA256 API declaration; transport implementation below uses OpenSSL.
namespace KODI{namespace UTILITY{class CDigest{public: enum class Type{MD5,SHA1,SHA256,SHA512,INVALID};static std::string Calculate(Type,const std::string&);};}}
using namespace std;
static bool metaAllowed=true,sourceAllowed=true,metaSave=true,sourceSave=true,confirmed=true,exists=true;
static int depth=0,sourceCalls=0,metaCalls=0,contentCalls=0,failures=0,checks=0;
static bool dirty=false;static string profile="a",chosenName="Download";static vector<string> chosenPaths;
static map<string,string> memoryPrefs,diskPrefs;static vector<string> events;
struct CMediaSource{string strName,strPath,m_strThumbnailImage;void FromNameAndPaths(const string&,const string&n,const vector<string>&p){strName=n;strPath=p.empty()?"":p[0];}};
static vector<CMediaSource> sources,persistedSources;
struct CFileItem{string label,path;bool parent=false;CFileItem()=default;CFileItem(const CMediaSource&s):label(s.strName),path(s.strPath){}string GetLabel()const{return label;}string GetPath()const{return path;}bool IsParentFolder()const{return parent;}string GetArt(const string&)const{return "";}};
struct Items{vector<shared_ptr<CFileItem>> rows;string path="sources://video/";int Size()const{return (int)rows.size();}auto Get(int i){return rows.at(i);}void Remove(int i){rows.erase(rows.begin()+i);}void Clear(){rows.clear();}string GetPath()const{return path;}};
struct Skin{string ID(){return "skin.infinity.diggz";}bool SaveSettings(){assert(depth==0);events.push_back("preferences");++metaCalls;if(!metaSave)return false;diskPrefs[profile]=memoryPrefs[profile];return true;}};
static shared_ptr<Skin> g_SkinInfo=make_shared<Skin>();
struct CSkinSettings{static CSkinSettings& GetInstance(){static CSkinSettings x;return x;}int TranslateString(const string&){return metaAllowed?0:-1;}const string& GetString(int){return memoryPrefs[profile];}void SetString(int,const string&s){if(metaAllowed){dirty=true;memoryPrefs[profile]=s;}}};
namespace KODI{namespace UTILITY{string CDigest::Calculate(Type t,const string&value){assert(t==Type::SHA256);unsigned char out[EVP_MAX_MD_SIZE];unsigned n=0;assert(EVP_Digest(value.data(),value.size(),out,&n,EVP_sha256(),nullptr)==1);ostringstream s;for(unsigned i=0;i<n;++i)s<<hex<<setw(2)<<setfill('0')<<(unsigned)out[i];return s.str();}}}
namespace InfinityAndroidCheckpoint{struct CheckpointWriteGuard{bool admitted;explicit CheckpointWriteGuard(const char*n):admitted(sourceAllowed){assert(string(n)=="xml_files");if(admitted)++depth;}~CheckpointWriteGuard(){if(admitted)--depth;}explicit operator bool()const{return admitted;}};void RecordFailure(const char*,const char*){++failures;}}
namespace CUtil{string TranslateSpecialSource(const string&p){return p.empty()||p[0]!='$'?p:"/translated/"+p.substr(1);}}
namespace StringUtils{bool EqualsNoCase(string a,string b){transform(a.begin(),a.end(),a.begin(),::tolower);transform(b.begin(),b.end(),b.begin(),::tolower);return a==b;}}
struct CMediaSourceSettings{static CMediaSourceSettings& GetInstance(){static CMediaSourceSettings x;return x;}bool AddShare(const string&,CMediaSource s){assert(depth>0);events.push_back("source");++sourceCalls;s.strPath=CUtil::TranslateSpecialSource(s.strPath);sources.push_back(s);if(sourceSave)persistedSources=sources;return sourceSave;}bool UpdateShare(const string&,const string&old,CMediaSource s){assert(depth>0);events.push_back("source");++sourceCalls;for(auto&v:sources)if(v.strName==old){v=s;break;}if(sourceSave)persistedSources=sources;return sourceSave;}};
struct CGUIDialogMediaSource{Items storage;Items*m_paths=&storage;string m_name;bool m_confirmed=false;void Initialize(){m_confirmed=false;}void SetShare(const CMediaSource&s){m_name=s.strName;storage.rows.clear();}void SetTypeOfMedia(const string&,bool=false){}void Open(){assert(depth==0);events.push_back("dialog");m_confirmed=confirmed;m_name=chosenName;for(auto&p:chosenPaths){auto x=make_shared<CFileItem>();x->path=p;storage.rows.push_back(x);}}bool IsConfirmed()const{return m_confirmed;}vector<string>GetPaths()const{vector<string>r;for(auto&p:storage.rows)r.push_back(p->path);return r;}string GetUniqueMediaSourceName(){string n=m_name;while(any_of(sources.begin(),sources.end(),[&](const auto&s){return s.strName==n;}))n+=" (2)";return n;}static void OnMediaSourceChanged(const string&,const string&,const CMediaSource&){assert(depth==0);++contentCalls;events.push_back("content");}static bool ShowAndAddMediaSourceWithResult(const string&,CMediaSource&,bool&,const function<bool(const CMediaSource&)>&);static bool ShowAndEditMediaSourceWithResult(const string&,const CMediaSource&,CMediaSource&,bool&,const function<bool(const CMediaSource&)>&);};
static CGUIDialogMediaSource dlg;constexpr int WINDOW_DIALOG_MEDIA_SOURCE=10129;
struct WM{template<class T>T*GetWindow(int){return exists?&dlg:nullptr;}};struct GUI{WM&GetWindowManager(){static WM w;return w;}};
struct CServiceBroker{static GUI*GetGUI(){static GUI g;return &g;}};
namespace URIUtils{bool PathEquals(const string&a,const string&b){return a==b;}}
namespace HELPERS{void ShowOKDialogText(const CVariant&,const CVariant&){};}
constexpr const char*DOWNLOADS_SETTING="Infinity.DownloadsSources.v1";
'''
tests=r'''
static bool mode=true;
static bool filter(Items&items){bool m_infinityDownloads=mode;
FILTER
return true;}
static Items listing(){Items i;for(auto&s:sources)i.rows.push_back(make_shared<CFileItem>(s));return i;}
static void reset(){metaAllowed=sourceAllowed=metaSave=sourceSave=confirmed=exists=true;depth=sourceCalls=metaCalls=contentCalls=failures=0;dirty=false;profile="a";chosenName="Download";chosenPaths={"/storage/user/Download/"};memoryPrefs.clear();diskPrefs.clear();sources.clear();persistedSources.clear();events.clear();mode=true;}
static void check(bool v){assert(v);++checks;}
int main(){CMediaSource result;bool failed=false;
reset();sources={{"Download","plugin://old-provider/",""},{"Media","/other-folder/",""}};auto before=sources;auto rows=listing();check(filter(rows)&&rows.Size()==0);check(sources.size()==before.size());
check(CGUIDialogMediaSource::ShowAndAddMediaSourceWithResult("video",result,failed,RememberDownloadsSource));check(!failed&&sourceCalls==1&&metaCalls==1&&contentCalls==1);check(result.strName=="Download (2)");check(events==vector<string>({"dialog","preferences","source","content"}));rows=listing();check(filter(rows)&&rows.Size()==1&&rows.Get(0)->GetPath()=="/storage/user/Download/");check(sources.size()==3&&sources[0].strPath==before[0].strPath);
std::cerr<<"CHECK ordinary_source_rename_keeps_added_folder\n";auto originalName=sources.back().strName;sources.back().strName="Renamed outside Downloads";rows=listing();check(filter(rows)&&rows.Size()==1);sources.back().strName=originalName;
memoryPrefs[profile]=diskPrefs[profile];rows=listing();check(filter(rows)&&rows.Size()==1); // cold data reload fixture
profile="b";rows=listing();check(filter(rows)&&rows.Size()==0);profile="a";mode=false;rows=listing();check(filter(rows)&&rows.Size()==3);mode=true;rows=listing();rows.path="/storage/user/Download/";check(filter(rows)&&rows.Size()==3); // child folders unfiltered
reset();confirmed=false;result.strName="unchanged";check(!CGUIDialogMediaSource::ShowAndAddMediaSourceWithResult("video",result,failed,RememberDownloadsSource));check(!failed&&sourceCalls==0&&metaCalls==0&&result.strName=="unchanged");
reset();metaSave=false;check(!CGUIDialogMediaSource::ShowAndAddMediaSourceWithResult("video",result,failed,RememberDownloadsSource));check(failed&&sourceCalls==0&&contentCalls==0&&dirty&&diskPrefs.empty());metaSave=true;check(CGUIDialogMediaSource::ShowAndAddMediaSourceWithResult("video",result,failed,RememberDownloadsSource));check(metaCalls==2&&sourceCalls==1); // same in-memory preference must retry its real save
reset();metaAllowed=false;check(!CGUIDialogMediaSource::ShowAndAddMediaSourceWithResult("video",result,failed,RememberDownloadsSource));check(failed&&sourceCalls==0&&metaCalls==0);
reset();sourceAllowed=false;check(!CGUIDialogMediaSource::ShowAndAddMediaSourceWithResult("video",result,failed,RememberDownloadsSource));check(failed&&sourceCalls==0&&metaCalls==1&&sources.empty());
reset();sourceSave=false;check(!CGUIDialogMediaSource::ShowAndAddMediaSourceWithResult("video",result,failed,RememberDownloadsSource));check(failed&&sourceCalls==1&&contentCalls==0&&failures==1&&dirty);rows=listing();check(filter(rows)&&rows.Size()==1);check(persistedSources.empty()); // no false source durability success
reset();chosenPaths={"$SPECIAL"};check(CGUIDialogMediaSource::ShowAndAddMediaSourceWithResult("video",result,failed,RememberDownloadsSource));rows=listing();check(filter(rows)&&rows.Size()==1&&rows.Get(0)->GetPath()=="/translated/SPECIAL");
reset();CMediaSource old;old.FromNameAndPaths("video","Saved",{"/old/"});sources.push_back(old);check(RememberDownloadsSource(old));chosenName="Renamed";chosenPaths={"/new/"};check(CGUIDialogMediaSource::ShowAndEditMediaSourceWithResult("video",old,result,failed,RememberDownloadsSource));rows=listing();check(filter(rows)&&rows.Size()==1&&rows.Get(0)->GetLabel()=="Renamed");
reset();old.FromNameAndPaths("video","Saved",{"/old/"});sources.push_back(old);check(RememberDownloadsSource(old));chosenName="Renamed";chosenPaths={"/new/"};sourceSave=false;check(!CGUIDialogMediaSource::ShowAndEditMediaSourceWithResult("video",old,result,failed,RememberDownloadsSource));check(failed&&failures==1);rows=listing();check(filter(rows)&&rows.Size()==1);sources={old};rows=listing();check(filter(rows)&&rows.Size()==1); // failed disk save retains old source membership too
reset();memoryPrefs[profile]="{bad";check(!RememberDownloadsSource(old));check(memoryPrefs[profile]=="{bad"&&metaCalls==0&&sourceCalls==0);rows=listing();check(!filter(rows));
reset();memoryPrefs[profile]="{\"schema\":2,\"sources\":[]}";check(!RememberDownloadsSource(old));check(metaCalls==0);
reset();memoryPrefs[profile]="{\"schema\":1,\"sources\":[\"not-a-fingerprint\"]}";check(!RememberDownloadsSource(old));check(metaCalls==0);
cout<<"PASS_ACTUAL_CANDIDATE_CPP_CONTRACT checks="<<checks<<" Android=NOT_RUN\n";
}
'''.replace('FILTER',filtercode)
source=OUT/'contract.cpp';source.write_text(setup+helpers+'\n'+functions+'\n'+tests)
rapid=Path('/dev/shm/infinity-rapidjson-host/rapidjson-1.1.0/include')
args=['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror','-Wno-deprecated-declarations','-Wno-unused-parameter','-DTARGET_ANDROID','-I'+str(NATIVE/'xbmc'),'-I'+str(rapid),str(source),str(NATIVE/'xbmc/utils/Variant.cpp'),str(NATIVE/'xbmc/utils/JSONVariantParser.cpp'),str(NATIVE/'xbmc/utils/JSONVariantWriter.cpp'),'-lcrypto','-o',str(OUT/'contract')]
p=subprocess.run(args,text=True,capture_output=True);(OUT/'compile.txt').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-5000:]
p=subprocess.run([str(OUT/'contract')],text=True,capture_output=True);(OUT/'result.txt').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stdout+p.stderr
# Remove exactly added blocks to prove original dialog overloads untouched.
original=(NATIVE/'xbmc/dialogs/GUIDialogMediaSource.cpp').read_text();added=dialog[dialog.index('// Downloads-only result APIs.'):dialog.index('bool CGUIDialogMediaSource::ShowAndAddMediaSource(',dialog.index('// Downloads-only result APIs.'))];restored=dialog.replace(added,'',1).replace('\n#if defined(TARGET_ANDROID)\n#include "platform/android/activity/InfinityAndroidCheckpoint.h"\n#endif','',1);assert restored==original
report={'status':'PASS_ACTUAL_CPP_CONTRACT_HOST_BOUNDARIES','result':p.stdout.strip(),'old_source_dialog_overloads_preserved_byte_for_byte':True,'codecs':'real frozen Kodi CVariant, JSON parser/writer; pinned RapidJSON1.1.0','SHA256':'real OpenSSL transport adapter','UI_file_admission_and_profile':'controlled host fixtures; not real Android','compiled_candidate_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'Android':'NOT_RUN','shutdown_test_executed':False}
(HERE/'HOST-CONTRACT-RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
