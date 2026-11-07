
"""Bound graphics ownership source and a host race probe; no speculative native patch."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys
def method(raw,s):
 start=raw.index(s);end=raw.index('\n}\n',start)+3
 return raw[start:end]
def run(root,out):
 prior=root/'previous-review'
 map_path=prior/'NATIVE-SOURCE-MAP.json'
 assert hashlib.sha256(map_path.read_bytes()).hexdigest()=='8a4baedfa0f978a7eedfc332b935deef3572a9deb2d78d8cd488bf02ce7e740a'
 expected=json.loads(map_path.read_text())
 p=root/'repairs/infinity-2103460-nine-corrections-20261106/downloads-native/build_native.py'
 spec=importlib.util.spec_from_file_location('exact462_graphics_sources',p);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
 r.OUT=out;r.restore.OUT=out;r.restore_sources()
 assert r.restore.hashes(root/'kodi')==expected
 # This restoration is required for the previously unavailable modified Application source.
 # It is not another behavioral test, new engine, or repetition of symbolication.
 wanted=['xbmc/application/Application.cpp','xbmc/messaging/ApplicationMessenger.cpp','xbmc/messaging/ApplicationMessenger.h',
 'xbmc/guilib/GUIWindowManager.cpp','xbmc/windowing/GraphicContext.cpp',
 'xbmc/guilib/GUIControlGroup.cpp','xbmc/platform/android/activity/android_main.cpp']
 matches=[]
 for p in sorted((root/'kodi/xbmc/platform/android').rglob('*')):
  if p.suffix not in ('.cpp','.c','.h'):continue
  raw=p.read_text(errors='replace')
  if any(m in raw for m in ('AInputQueue_getEvent(','AInputQueue_attachLooper(','onInputEvent(','m_touch.onTouch','m_androidTouch.onTouch')):
   n=p.relative_to(root/'kodi').as_posix();wanted.append(n)
 wanted=sorted(set(wanted))
 for n in wanted:
  p=root/'kodi'/n;assert r.sha(p)==expected[n]
  raw=p.read_text();t=out/'sources'/n;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(p.read_bytes())
  lines=raw.splitlines();selected=set()
  markers=('::OnEvent(', '::SendGUIMessage(', '::SendMsg(', '::SendMessage(', 'TMSG_GUI_MESSAGE',
   'QuerySupportedGestures(', 'AInputQueue_getEvent(', 'AInputQueue_attachLooper(', 'onInputEvent(',
   'm_touch.onTouch','m_androidTouch.onTouch','::handle_input(','m_processThreadId','m_guiMessages')
  if len(lines)<140:selected=set(range(len(lines)))
  for i,line in enumerate(lines):
   if any(m in line for m in markers):
    for j in range(max(0,i-5),min(len(lines),i+110)):selected.add(j)
  print('BOUND_GRAPHICS_DISPATCH_BEGIN '+n+' sha256='+expected[n])
  for i in sorted(selected):print(f'{i+1:04d}: {lines[i]}')
  print('BOUND_GRAPHICS_DISPATCH_END '+n)
 graphics=(root/'kodi/xbmc/windowing/GraphicContext.cpp').read_text()
 methods=[method(graphics,m)for m in (
  'void CGraphicContext::SetOrigin(', 'void CGraphicContext::RestoreOrigin(',
  'void CGraphicContext::SetScalingResolution(')]
 work=out/'host-graphics-before';work.mkdir()
 prefix=r"""
#include <stack>
#include <mutex>
#include <thread>
#include <atomic>
#include <iostream>
struct CPoint{float x,y;CPoint(float a=0,float b=0):x(a),y(b){}CPoint operator+(const CPoint&o)const{return {x+o.x,y+o.y};}};
struct RESOLUTION_INFO{};
struct TransformMatrix{static TransformMatrix CreateTranslation(float,float){return {};}};
struct Transform{float scaleX=1,scaleY=1;TransformMatrix matrix;void Reset(){scaleX=scaleY=1;}};
constexpr int RES_INVALID=-1;
class CGraphicContext:public std::recursive_mutex{
public:
 std::stack<CPoint>m_origins,m_cameras;std::stack<float>m_stereoFactors;
 RESOLUTION_INFO m_windowResolution;int m_Resolution=0,m_iScreenWidth=100,m_iScreenHeight=100;
 Transform m_guiTransform,m_finalTransform;
 void GetGUIScaling(const RESOLUTION_INFO&,float&,float&,TransformMatrix*){}
 void AddTransform(const TransformMatrix&){}void RemoveTransform(){}
 void SetOrigin(float,float);void RestoreOrigin();void SetScalingResolution(const RESOLUTION_INFO&,bool);
};
"""
 main=r"""
int main(){
 CGraphicContext graphics;RESOLUTION_INFO res;graphics.SetScalingResolution(res,true);
 std::atomic<int>ready{0};std::atomic<bool>go{false};
 std::thread render([&]{++ready;while(!go.load())std::this_thread::yield();
  for(int i=0;i<20000;++i){graphics.SetOrigin(1,2);graphics.RestoreOrigin();}});
 std::thread input([&]{++ready;while(!go.load())std::this_thread::yield();
  for(int i=0;i<20000;++i){std::unique_lock<std::recursive_mutex>lock(graphics);graphics.SetScalingResolution(res,true);}});
 while(ready.load()!=2)std::this_thread::yield();go=true;render.join();input.join();
 std::cout<<"completed host scheduling\n";
}
"""
 source=work/'actual_graphics_origin.cpp';source.write_text(prefix+'\n'+'\n'.join(methods)+'\n'+main)
 binary=work/'graphics-before'
 c=subprocess.run(['g++','-std=c++17','-fsanitize=thread','-g','-O1','-pthread',str(source),'-o',str(binary)],capture_output=True,text=True)
 (work/'COMPILE.txt').write_text(c.stdout+c.stderr);assert c.returncode==0,c.stderr
 p=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20,env=dict(os.environ,TSAN_OPTIONS='halt_on_error=1:exitcode=77'))
 text=p.stdout+p.stderr;(work/'BEFORE.txt').write_text(text)
 if 'WARNING: ThreadSanitizer: data race' in text:
  status='CONFIRMED_HOST_RACE_IN_ACTUAL_GRAPHICS_METHODS'
 elif 'unexpected memory mapping' in text:
  status='BLOCKED_HOST_TSAN_ADDRESS_MAPPING'
 else:status='NO_RELIABLE_RACE_OBSERVATION'
 (out/'GRAPHICS-OWNERSHIP-PROBE.json').write_text(json.dumps(dict(status=status,source=os.environ['GITHUB_SHA'],returncode=p.returncode,
   methods_sha256=[hashlib.sha256(m.encode()).hexdigest()for m in methods],
   exact_sources={n:expected[n]for n in wanted},host_platform_boundaries=['render/input thread scheduling','transform math stubs','recursive critical section type'],
   Android='NOT_RUN',historical_abort_cause='NOT_EXCLUSIVELY_PROVEN',production_graphics_patch=False),indent=2)+'\n')
 print('GRAPHICS_HOST_RESULT '+status)
 print(text[:16000])
