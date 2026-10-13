#!/usr/bin/env python3
"""Execute the real 376 file-picker creation methods against skin onload actions.

No Kodi/Android build. GUI rendering, filesystem browsing and modal queues are
narrow adapters. This intentionally exercises SetHeading -> Initialize before
the native ZIP-context assignment, which the previous dispatch harness omitted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
LAYOUTS = ('16x9', '20x9', '5x6', '6x5', 'fallback', 'portrait',
           'responsive/base', 'responsive/landscape', 'responsive/portrait',
           'responsive/square', 'responsive/tall', 'responsive/ultrawide',
           'responsive/wide', 'unified')

def method(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 0
    for i in range(opening, len(source)):
        if source[i] == '{': depth += 1
        if source[i] == '}': depth -= 1
        if not depth: return source[start:i + 1]
    raise AssertionError(signature)

def run(report, candidate_root, native_root=None, kodi_root=None):
    pinned = json.loads((HERE / 'fixtures/native376-lifecycle.json').read_text())
    for data in pinned['method_provenance']:
        assert hashlib.sha256(data['source'].encode()).hexdigest() == data['method_sha256']
    exact = [n['source'] for n in pinned['method_provenance']]
    assert len(exact)==8
    bodies = exact[:4] + [exact[4].replace('CGUIWindow::', 'CGUIDialogFileBrowser::'),
                         exact[5].replace('CGUIWindowManager::', 'WindowManager::'),
                         exact[6].replace('CGUIWindow *window', 'CGUIDialogFileBrowser *window'),
                         'bool CGUIDialogFileBrowser::InitMessage(CGUIMessage& message) ' + exact[7]]
    assert pinned['header_default'] == 'bool m_infinityZipInstallContext{false};'
    load = pinned['load_method']
    assert load.index('LoadXML(') < load.index('m_windowLoaded = true;') < load.index('OnWindowLoaded();')
    if native_root or kodi_root:
        assert native_root and kodi_root, '--native-root and --kodi-root must be supplied together'
        native = native_root / 'repairs/critical-preview-2103376/native'
        for data in pinned['method_provenance']:
            base = native if data['file'].startswith('xbmc/dialogs/') else kodi_root
            source = (base / data['file']).read_text()
            actual = (source.split('  case GUI_MSG_WINDOW_INIT:', 1)[1].split('    break;', 1)[0].strip()
                      if data.get('case') else method(source, data['signature']))
            assert actual == data['source'], 'Native method differs from pinned376: ' + data['file']
    validated = []
    for directory in LAYOUTS:
        file = candidate_root / directory / 'FileBrowser.xml'
        candidate = ET.fromstring(file.read_bytes()).findall('onload')
        arm = [n for n in candidate if n.text == 'SetProperty(Infinity.FilePreview.OptIn,v1)']
        assert len(arm) == 1 and not arm[0].get('condition'), 'Candidate must restore unconditional synchronous opt-in: ' + str(file)
        validated.append({'path': directory + '/FileBrowser.xml', 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    assert pinned['skin210_onload']['text'] == 'SetProperty(Infinity.FilePreview.OptIn,v1)'
    assert pinned['skin210_onload']['condition'] == '!String.IsEqual(Window.Property(Infinity.FilePreview.RouteRevision),2103376)'
    fixture = r'''
#include <cassert>
#include <iostream>
#include <map>
#include <string>
#include <vector>
#include "xbmc/dialogs/InfinityFilePreviewContracts.h"
constexpr int WINDOW_INVALID=9999, WINDOW_ID_MASK=0xffff, CONTROL_LIST=450, CONTROL_THUMBS=451, GUI_MSG_WINDOW_LOAD=1;
#define SET_CONTROL_LABEL(id,value) static_cast<void>(value)
struct CGUIMessage { CGUIMessage(int,int,int) {} };
struct Variant { std::string value; std::string asString() const { return value; } };
struct Source { std::string strPath; };
using VECSOURCES = std::vector<Source>;
struct Directory { std::string path; void SetMask(const std::string&) {} void SetPath(const std::string& p) { path=p; } const std::string& GetPath() const { return path; } };
struct View { void Reset() {} void SetParentWindow(int) {} void AddView(void*) {} void SetSelectedItem(const std::string&) {} };
struct URIUtils { static bool HasSlashAtEnd(const std::string&) { return false; } static bool PathEquals(const std::string& a,const std::string& b) { return a==b; } static std::string GetParentPath(const std::string&) { return "/Download/"; } };
struct CUtil { static int GetMatchingSource(const std::string&,const VECSOURCES&,bool&) { return -1; } };
struct CDirectory { static bool Exists(const std::string&) { return true; } };
struct CFile { static bool Exists(const std::string&) { return true; } };
struct Localize { std::string Get(int) { return "Install from zip file"; } } g_localizeStrings;
struct CWindowTranslator { static int TranslateWindow(const std::string& v) { return std::stoi(v); } };
struct CGUIDialog { virtual ~CGUIDialog()=default; virtual void OnWindowLoaded() {} virtual bool OnMessage(CGUIMessage&) { return true; } };
struct CGUIDialogFileBrowser : CGUIDialog {
  // Exact production default, unlike the old dispatch fixture's true default.
  bool m_infinityZipInstallContext{false}, m_windowLoaded{false}, m_useFileDirectories{false}, m_browsingForImages{false}, m_addNetworkShareEnabled{false}, m_bConfirmed{false}, m_bFlip{false};
  int m_browsingForFolders{0}, id{10126};
  std::string m_selectedPath; VECSOURCES m_shares; Directory m_rootDir, directory; Directory* m_Directory{&directory}; View m_viewControl;
  KODI::FILEPREVIEW::Request m_infinityPreviewRequest; std::map<std::string,std::string> props;
  void SetProperty(const std::string& k,const std::string& v) { props[k]=v; }
  Variant GetProperty(const std::string& k) const { auto i=props.find(k); return {i==props.end()?"":i->second}; }
  int GetID() const { return id; } void* GetControl(int) { return this; }
  void SetSources(const VECSOURCES& s) { m_shares=s; } void Update(const std::string&) {}
  bool IsConfirmed() const { return m_bConfirmed; }
  bool NeedLoad() const { return !m_windowLoaded; }
  void AllocResources(bool) { if (!m_windowLoaded) { m_windowLoaded=true; OnWindowLoaded(); } }
  bool Initialize(); void SetHeading(const std::string&); void OnWindowLoaded() override; void ClearInfinityFilePreview();
  bool InitMessage(CGUIMessage&); void Open();
  static bool ShowAndGetFile(const VECSOURCES&,const std::string&,const std::string&,std::string&,bool=false,bool=false);
};
struct WindowManager {
  std::map<int,CGUIDialogFileBrowser*> windows; int top{WINDOW_INVALID};
  bool Initialized() const { return true; }
  CGUIDialogFileBrowser* GetWindow(int id) { auto i=windows.find(id); return i==windows.end()?nullptr:i->second; }
  int GetTopmostModalDialog() const { return top; } int GetActiveWindow() const { return 10000; }
  int GetActiveWindowOrDialog() const;
  void AddUniqueInstance(CGUIDialogFileBrowser* b) { int instance=0; while(GetWindow(b->id)) b->id+=(++instance<<16); windows[b->id]=b; }
  void Remove(int id) { windows.erase(id); }
} manager;
struct GUI { WindowManager& GetWindowManager() { return manager; } } gui;
struct Messenger { bool IsProcessThread() { return true; } void SendGUIMessage(CGUIMessage&,int,bool) { assert(false); } } messenger;
struct CServiceBroker { static GUI* GetGUI() { return &gui; } static Messenger* GetAppMessenger() { return &messenger; } };
int skinVersion=210;
struct Outcome { std::string optin,nativeVersion,revision; bool canOpen; int owner; } outcome;
// @PRODUCTION@
void CGUIDialogFileBrowser::Open() {
  manager.top=id;
  CGUIMessage message(0,0,0);
  InitMessage(message);
  // Actual XML onload condition and builtin semantics. Conditions use the
  // full top-modal context; the builtin target independently masks the ID.
  if (skinVersion==209 || skinVersion==211 || GetProperty("Infinity.FilePreview.RouteRevision").asString()!="2103376")
    SetProperty({"Infinity.FilePreview.OptIn","v1"});
  outcome={GetProperty("Infinity.FilePreview.OptIn").asString(),GetProperty("Infinity.FilePreview.NativeVersion").asString(),GetProperty("Infinity.FilePreview.RouteRevision").asString(),false,id};
  outcome.canOpen=KODI::FILEPREVIEW::CanOpen(m_infinityZipInstallContext,outcome.optin=="v1",true,"/Download/selected.zip");
}
int main(int argc,char** argv) {
  assert(argc==4); skinVersion=std::stoi(argv[1]); bool cloned=std::stoi(argv[2]); bool zipContext=std::stoi(argv[3]);
  CGUIDialogFileBrowser existing;
  if(cloned) manager.windows[10126]=&existing;
  VECSOURCES shares; std::string path="/Download/selected.zip";
  for(int cycle=0;cycle<20;++cycle) {
    bool confirmed=CGUIDialogFileBrowser::ShowAndGetFile(shares,zipContext?"*.zip":"/",zipContext?"Install from zip file":"Browse source",path);
    assert(!confirmed && outcome.nativeVersion==(zipContext?"v1":"") && outcome.revision=="2103376");
    assert(outcome.owner==(cloned?75662:10126));
    bool expected=zipContext && (skinVersion==209 || skinVersion==211) && !cloned;
    assert(outcome.canOpen==expected);
  }
  std::cout << "{\"skin\":" << skinVersion << ",\"cloned\":" << cloned << ",\"zip_context\":" << zipContext << ",\"cycles\":20,\"owner\":" << outcome.owner << ",\"optin\":\"" << outcome.optin << "\",\"can_open_preview\":" << (outcome.canOpen?"true":"false") << "}" << std::endl;
}
'''
    # Explicit qualification distinguishes the real GUI builtin from the
    # object's member setter in the host Open adapter.
    fixture = fixture.replace('    SetProperty({"Infinity.FilePreview.OptIn","v1"});',
                              '    ::SetProperty({"Infinity.FilePreview.OptIn","v1"});')
    cases = []
    with tempfile.TemporaryDirectory(prefix='infinity-376-skin-lifecycle-') as td:
        td=Path(td); source=td/'lifecycle.cpp'; binary=td/'lifecycle'
        source.write_text(fixture.replace('// @PRODUCTION@','\n\n'.join(bodies)))
        contract=td/'xbmc/dialogs/InfinityFilePreviewContracts.h'; contract.parent.mkdir(parents=True)
        contract.write_text(pinned['contract_header'])
        assert hashlib.sha256(contract.read_bytes()).hexdigest()==pinned['contract_sha256']
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pedantic','-I',str(td),str(source),'-o',str(binary)],check=True)
        for skin, cloned, zip_context in [(209,0,1),(210,0,1),(211,0,1),(209,1,1),(210,1,1),(211,1,1),(211,0,0),(211,1,0)]:
            result=subprocess.run([str(binary),str(skin),str(cloned),str(zip_context)],check=True,capture_output=True,text=True)
            cases.append(json.loads(result.stdout))
    result={'cases':cases,'physical_device_test':False,'candidate_xml_validated':validated,
            'reproduction':'Actual ShowAndGetFile calls SetHeading/Initialize/OnWindowLoaded before assigning ZIP install context. Skin210 skips the required onload opt-in.',
            'production_methods': [s.split('{',1)[0].strip() for s in bodies],
            'source_hashes': pinned['source_hashes'],
            'fixture_sha256': hashlib.sha256((HERE/'fixtures/native376-lifecycle.json').read_bytes()).hexdigest(),
            'limitations':['No GUI renderer, Android event queue, or physical input.','Filesystem and graphics allocation adapters are stubbed; real initialization method executes.','Hypothetical overlapping/cloned File Browser remains unable to opt in because the unchanged Kodi builtin masks instance IDs. A single Install-from-ZIP dialog uses 10126.']}
    if report: report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path)
    p.add_argument('--candidate-root',type=Path,default=HERE.parent/'delta')
    p.add_argument('--native-root',type=Path);p.add_argument('--kodi-root',type=Path)
    args=p.parse_args();run(args.report,args.candidate_root,args.native_root,args.kodi_root)
