"""Evidence-bounded Android gesture/render ownership candidate.

No APK, signer, provider, settings, checkpoint, input mask rewrite or device operation.
Source restore is always from exact APK462 9411-file fingerprint.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'native-ownership-review'
BASE='92bb6ecbb21c14f62f40555ba2aaef198e3847e2'
MAP_SHA='8a4baedfa0f978a7eedfc332b935deef3572a9deb2d78d8cd488bf02ce7e740a'
KEYBOARD='xbmc/guilib/GUIKeyboardFactory.cpp'
GRAPHICS={
  'xbmc/windowing/GraphicContext.h':('c18eb52470514ebb8da9c59330005f80b5815120b006ff8d76861f170b082bea','24f27b66184979b05246cce7052ce0b013aad548b2a171d429b199820bf376c2'),
  'xbmc/guilib/GUIWindowManager.cpp':('f9aeddec883a4d1ac63303bfbb9b88cba2bcba5f01fcd799f68c444665d31c23','c36cf699f799f89b2ffde8900763837b1fb3436f74b05cca84226380cb9f4bde'),
  'xbmc/input/touch/generic/GenericTouchActionHandler.cpp':('43bb691c2fa01355125b54de845761aa35f3553902c9b593acc4bfde292fc509','7fdd605c3136b361408d4a24d0765c2c8769c717a9df748a7c23b8fb4b5d20a1'),
}
PATCH=HERE/'GRAPHICS-GESTURE-RENDER.patch'

def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def write(name,value):
    OUT.mkdir(exist_ok=True)
    (OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def original_map():
    target=ROOT/'previous-review/NATIVE-SOURCE-MAP.json'
    assert digest(target)==MAP_SHA
    rows=json.loads(target.read_text())
    assert len(rows)==9411
    return rows
def check_branch():
    assert os.environ.get('GITHUB_REF')=='refs/heads/work/infinity-graphics-gesture-render-462-candidate-20261107'
    names=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines())
    allowed={'.github/workflows/infinity-graphics-gesture-render-462-host.yml'}
    allowed|={str(p.relative_to(ROOT)) for p in HERE.iterdir() if p.is_file()}
    assert names and names <= allowed, ('Out-of-scope repository source modification',sorted(names-allowed))
def prepare():
    check_branch()
    base=original_map()
    actual=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text())
    assert set(actual)==set(base)
    assert {n for n in actual if base[n]!=actual[n]}=={KEYBOARD}
    for name,(before,after) in GRAPHICS.items():
        assert base[name]==before,(name,'original source map hash mismatch')
        assert digest(ROOT/'kodi'/name)==before,(name,'source not exact')
    assert PATCH.is_file()
    subprocess.run(['git','apply','--check',str(PATCH)],cwd=ROOT/'kodi',check=True)
    subprocess.run(['git','apply',str(PATCH)],cwd=ROOT/'kodi',check=True)
    for name,(before,after) in GRAPHICS.items():
        assert digest(ROOT/'kodi'/name)==after,('unexpected candidate content',name)
    staged=dict(actual)
    for name,(_,after) in GRAPHICS.items():staged[name]=after
    assert set(staged)==set(base)
    assert {n for n in staged if staged[n]!=base[n]}=={KEYBOARD,*GRAPHICS}
    # Verify the SOURCE-LEVEL original query/mask protocol was not replaced.
    newTouch=(ROOT/'kodi/xbmc/input/touch/generic/GenericTouchActionHandler.cpp').read_text()
    oldTouch=(ROOT/'previous-review/sources/xbmc/input/touch/generic/GenericTouchActionHandler.cpp').read_text()
    marker='  CGUIMessage msg(GUI_MSG_GESTURE_NOTIFY,'
    assert newTouch.count(marker)==oldTouch.count(marker)==1
    oldSuffix=oldTouch[oldTouch.index(marker):oldTouch.index('\n}\n',oldTouch.index(marker))+3]
    newSuffix=newTouch[newTouch.index(marker):newTouch.index('\n}\n',newTouch.index(marker))+3]
    assert oldSuffix==newSuffix, 'Must not change existing gesture mask or pointer lifetime'
    assert "if (msg.GetPointer())" in newSuffix and "delete p;" in newSuffix
    render=(ROOT/'kodi/xbmc/guilib/GUIWindowManager.cpp').read_text()
    r=render[render.index('bool CGUIWindowManager::Render()'):]
    t=newTouch[newTouch.index('int CGenericTouchActionHandler::QuerySupportedGestures('):]
    assert r.index('CSingleExit lock(')<r.index('gestureRenderOwner(')<r.index('CDirtyRegionList dirtyRegions')
    assert t.index('gestureRenderOwner(')<t.index('CGUIMessage msg(')<t.index('GetWindowManager().SendMessage(msg)')
    # Original application checkpoint/message dispatch untouched; no asynchronous waiting added.
    for n in ('xbmc/application/Application.cpp','xbmc/messaging/ApplicationMessenger.cpp',
              'xbmc/messaging/ApplicationMessenger.h','xbmc/platform/android/activity/InfinityAndroidCheckpoint.cpp'):
        assert digest(ROOT/'kodi'/n)==base[n],n
    write('NATIVE-SOURCE-MAP.json',staged)
    write('GRAPHICS-PRESERVATION.json',dict(status='PASS_EXACT_SOURCE_AND_SCOPED_CANDIDATE',
      native_sources=9411,changed_native_sources=sorted({KEYBOARD,*GRAPHICS}),
      protected_native_sources_unchanged=9407,
      original_graphics_sha256={name:before for name,(before,after) in GRAPHICS.items()},
      candidate_graphics_sha256={name:after for name,(before,after) in GRAPHICS.items()},
      original_gesture_mask_protocol='UNCHANGED',
      original_checkpoint_sources='UNCHANGED',original_messenger_sources='UNCHANGED',
      production_patch_proven=False,Android='NOT_RUN',APK=False,signing=False))
    print('PASS exact source-map restoration; original keyboard plus 3 Android graphics gesture/render changes; 9407 other native files unchanged')

def method(raw,marker):
    start=raw.index(marker)
    end=raw.index('\n}\n',start)+3
    return raw[start:end]

def host():
    # Directly compile the three exact current GraphicContext method bodies.
    # Platform locks and render/touch scheduling are explicit synthetic boundaries.
    raw=(ROOT/'kodi/xbmc/windowing/GraphicContext.cpp').read_text()
    original=original_map()
    assert digest(ROOT/'kodi/xbmc/windowing/GraphicContext.cpp')==original['xbmc/windowing/GraphicContext.cpp']
    methods='\n'.join(method(raw,m) for m in ('void CGraphicContext::SetOrigin(',
        'void CGraphicContext::RestoreOrigin(','void CGraphicContext::SetScalingResolution('))
    prefix=r"""
#include <mutex>
#include <stack>
#include <thread>
#include <atomic>
#include <iostream>
#include <cassert>
struct CPoint {
 float x,y;
 CPoint(float a=0,float b=0):x(a),y(b){}
 CPoint operator+(const CPoint&o)const{return {x+o.x,y+o.y};}
};
struct RESOLUTION_INFO{};
struct TransformMatrix{static TransformMatrix CreateTranslation(float,float){return {};}};
struct Transform{
 float scaleX=1,scaleY=1;
 TransformMatrix matrix;
 void Reset(){scaleX=scaleY=1;}
};
constexpr int RES_INVALID=-1;
class CGraphicContext {
public:
 std::recursive_mutex graphicsSection,gestureRenderMutex;
 std::stack<CPoint>m_origins,m_cameras;
 std::stack<float>m_stereoFactors;
 RESOLUTION_INFO m_windowResolution;
 int m_Resolution=0,m_iScreenWidth=100,m_iScreenHeight=100;
 Transform m_guiTransform,m_finalTransform;
 void GetGUIScaling(const RESOLUTION_INFO&,float&,float&,TransformMatrix*){}
 void AddTransform(const TransformMatrix&){}
 void RemoveTransform(){}
 void SetOrigin(float,float);
 void RestoreOrigin();
 void SetScalingResolution(const RESOLUTION_INFO&,bool);
};
"""
    suffix=r"""
int main() {
 CGraphicContext gfx; RESOLUTION_INFO resolution;
 gfx.SetScalingResolution(resolution,true);
 std::atomic<int> ready{0}; std::atomic<bool> start{false};
 std::thread render([&] {
  ++ready; while (!start.load()) std::this_thread::yield();
  for (int i=0;i<20000;++i) {
   std::unique_lock<std::recursive_mutex> oldGraphics(gfx.graphicsSection);
   oldGraphics.unlock(); // existing Render CSingleExit before new gate
   {
     std::unique_lock<std::recursive_mutex> renderOwner(gfx.gestureRenderMutex);
     gfx.SetOrigin(1,2);
     gfx.RestoreOrigin();
   }
   oldGraphics.lock(); // existing CSingleExit restores after gate ends
  }
 });
 std::thread touch([&] {
  ++ready; while (!start.load()) std::this_thread::yield();
  for (int i=0;i<20000;++i) {
    std::unique_lock<std::recursive_mutex> gestureOwner(gfx.gestureRenderMutex);
    std::unique_lock<std::recursive_mutex> oldGraphics(gfx.graphicsSection);
    gfx.SetScalingResolution(resolution,true);
  }
 });
 while (ready.load()!=2) std::this_thread::yield();
 start=true; render.join(); touch.join();
 assert(gfx.m_origins.size()>=1);
 std::cout<<"PASS_TSAN_SERIALIZED_ORIGIN_STACK 20000 render/touch cycles\n";
}
"""
    work=OUT/'host-graphics-gesture';work.mkdir(parents=True,exist_ok=True)
    path=work/'exact-graphiccontext-host.cpp';path.write_text(prefix+'\n'+methods+'\n'+suffix)
    executable=work/'test-touched-render'
    cmd=['g++','-std=c++17','-g','-O1','-pthread','-fsanitize=thread',
         str(path),'-o',str(executable)]
    c=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    (work/'COMPILE.txt').write_text(c.stdout+c.stderr)
    assert c.returncode==0,c.stderr[:8000]
    run=subprocess.run([str(executable)],capture_output=True,text=True,
                       env=dict(os.environ,TSAN_OPTIONS='halt_on_error=1:exitcode=77'),timeout=45)
    output=run.stdout+run.stderr
    (work/'RESULTS.txt').write_text(output)
    assert run.returncode==0 and 'WARNING: ThreadSanitizer' not in output and 'PASS_TSAN_SERIALIZED_ORIGIN_STACK' in output,(run.returncode,output[:10000])
    write('GRAPHICS-GATE-HOST-RESULTS.json',dict(status='PASS_TSAN_HOST_FRAME_GATE',
      iterations_per_side=20000,actual_GraphicContext_methods=True,
      renderer_and_touch_scheduling='HOST_MODEL',
      no_new_GUIImage_message_queue=True,
      Android_compilation='NOT_RUN',APK=False,signing=False,
      native_lifetime_and_all_other_inputs='NOT_FULLY_VALIDATED'))
    print(output.strip())

def link():
    import sys
    sys.path.insert(0,str(ROOT/'repairs/universal-persistence-2103401'))
    build=load(ROOT/'repairs/universal-persistence-2103401/build.py','original_native_engine')
    build.OUT=OUT
    proof=build.compile_engine()
    native=OUT/'libkodi.so'
    assert proof['complete_native_engine_compiled'] and proof['reviewed_file_count']==9411
    assert native.stat().st_size>50000000
    tool=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    header=subprocess.check_output([str(tool),'-h',str(native)],text=True)
    assert 'ELF64' in header and 'AArch64' in header and 'DYN' in header
    (OUT/'GRAPHICS-ARM64-ABI.txt').write_text(header)
    m=json.loads((OUT/'NATIVE-SOURCE-MAP.json').read_text())
    baseline=original_map()
    assert {n for n in m if m[n]!=baseline[n]}=={KEYBOARD,*GRAPHICS}
    write('GRAPHICS-ENGINE-INTERNAL.json',dict(status='PASS_FULL_ARM64_LINK_GESTURE_RENDER_CANDIDATE',
      source_commit=os.environ['GITHUB_SHA'],native_sha256=digest(native),
      native_bytes=native.stat().st_size,protected_native_sources_unchanged=9407,
      gestures_response_logic='UNCHANGED',checkpoint_sources='UNCHANGED',
      source_gesture_render_candidate_only=True,
      complete_graphics_correctness='NOT_PROVEN',
      search_settings='UNRESOLVED',Android='NOT_RUN',APK=False,signed=False))
    print('PASS FULL ARM64 engine link graphics/render candidate; NOT AN APK OR DEVICE REPAIR')

if __name__=='__main__':
    {'prepare':prepare,'host':host,'link':link}[sys.argv[1]]()
