#!/usr/bin/env python3
"""Exercise actual archived startup functions through the compiled source guard."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import types

HERE=Path(__file__).resolve().parent
FILES={'plugin.video.pov':'resources/lib/service.py',
       'plugin.video.redlight':'resources/lib/service.py',
       'plugin.video.thecrew':'service.py',
       'plugin.video.themoviedb.helper':'resources/service.py'}
DIGEST=r'''
#pragma once
#include <openssl/evp.h>
#include <string>
namespace KODI { namespace UTILITY {
struct CDigest {
enum class Type {SHA256};
static std::string Calculate(Type,const std::string& value) {
  unsigned char bytes[EVP_MAX_MD_SIZE];unsigned int count=0;
  if(!EVP_Digest(value.data(),value.size(),bytes,&count,EVP_sha256(),nullptr)) throw 1;
  const char* hex="0123456789abcdef";std::string result;
  for(unsigned int i=0;i<count;i++){result+=hex[bytes[i]>>4];result+=hex[bytes[i]&15];}
  return result;
}
};
}}
'''
RUNNER=r'''
#include <Python.h>
#include "InfinityServiceStartupWait.h"
#include <fstream>
#include <iterator>
#include <iostream>
int main(int argc,char** argv) {
  if(argc!=3)return 4;
  std::ifstream file(argv[2],std::ios::binary);
  std::string source((std::istreambuf_iterator<char>(file)),std::istreambuf_iterator<char>()),output;
  if(!InfinityServiceStartupWait::Transform(argv[1],source,output))return 2;
  std::cout<<output;
}
'''

def function(source):
    tree=ast.parse(source)
    found=[node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='wait_for_am_trakt']
    assert len(found)==1
    return ast.Module(body=[found[0]],type_ignores=[])

def run_wait(source,scenario):
    state={'waits':0,'reads':0}
    def aborted():return scenario=='abort_start' or (scenario=='abort_during' and state['waits']>=5)
    def wait(_):state['waits']+=1;return aborted()
    class Monitor:
        def abortRequested(self):return aborted()
        def waitForAbort(self,t):return wait(t)
    class Addon:
        def __init__(self,_):pass
        def getSetting(self,key):
            state['reads']+=1
            if scenario=='ready' or scenario=='ready_later' and state['waits']>=3:
                return 'true' if key=='am_trakt_ready' else '1000'
            return ''
    modules={'xbmc':types.SimpleNamespace(Monitor=Monitor,sleep=lambda _:wait(1),getCondVisibility=lambda _:True),
             'xbmcaddon':types.SimpleNamespace(Addon=Addon),
             'time':types.SimpleNamespace(time=lambda:1000)}
    old={name:sys.modules.get(name) for name in modules}
    try:
        sys.modules.update(modules)
        scope={};exec(compile(function(source),'<actual-startup-function>','exec'),scope)
        result=scope['wait_for_am_trakt']()
        return result,state
    finally:
        for name,value in old.items():
            if value is None:sys.modules.pop(name,None)
            else:sys.modules[name]=value

def verify(root,out):
    root,out=Path(root),Path(out)
    results={}
    with tempfile.TemporaryDirectory() as scratch:
        scratch=Path(scratch);(scratch/'utils').mkdir()
        (scratch/'utils/Digest.h').write_text(DIGEST)
        (scratch/'runner.cpp').write_text(RUNNER)
        includes=subprocess.check_output(['python3-config','--includes'],text=True).split()
        binary=scratch/'runner'
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-I'+str(HERE),'-I'+str(scratch),
                        *includes,str(scratch/'runner.cpp'),'-o',str(binary),'-lcrypto'],check=True)
        for addon,name in FILES.items():
            path=root/addon/name;source=path.read_bytes()
            run=subprocess.run([str(binary),addon,str(path)],capture_output=True,check=True)
            patched=run.stdout;compile(patched.decode(),name,'exec')
            tests={}
            for scenario in ['ready','ready_later','timeout','abort_start','abort_during']:
                original=run_wait(source.decode(),scenario);fixed=run_wait(patched.decode(),scenario)
                if scenario in ['ready','ready_later','timeout']:assert original==fixed,(addon,scenario,original,fixed)
                else:
                    assert original[1]['waits']==120,(addon,original)
                    assert fixed[0] is False and fixed[1]['waits']==(0 if scenario=='abort_start' else 5),(addon,fixed)
                tests[scenario]={'approved':original,'corrected':fixed}
            changed=scratch/'changed.py';changed.write_bytes(source+b'\n# source mismatch\n')
            assert subprocess.run([str(binary),addon,str(changed)],capture_output=True).returncode==2
            assert subprocess.run([str(binary),'plugin.video.playlistbrowser',str(path)],capture_output=True).returncode==2
            assert subprocess.run([str(binary),'unknown.addon',str(path)],capture_output=True).returncode==2
            # Execute the actual post-wait caller under an already-requested
            # abort. No provider service initialization may run after that wait.
            if addon!='plugin.video.redlight':
                tree=ast.parse(patched.decode())
                marker='_crew_addon' if addon=='plugin.video.thecrew' else 'ServiceMonitor' if addon=='plugin.video.themoviedb.helper' else 'entry'
                guards=[n for n in ast.walk(tree) if isinstance(n,ast.If) and '__import__' in ast.unparse(n.test)
                        and 'abortRequested' in ast.unparse(n.test) and marker in ast.unparse(n)]
                assert len(guards)==1,addon
                old=sys.modules.get('xbmc')
                try:
                    sys.modules['xbmc']=types.SimpleNamespace(Monitor=lambda:types.SimpleNamespace(abortRequested=lambda:True))
                    # The body contains original imports/initialization. With
                    # no peers supplied it would fail immediately if dispatched.
                    exec(compile(ast.Module(body=[guards[0]],type_ignores=[]),'<actual-caller>','exec'),{})
                finally:
                    if old is None:sys.modules.pop('xbmc',None)
                    else:sys.modules['xbmc']=old
            results[addon]={'input_sha256':hashlib.sha256(source).hexdigest(),
                            'output_sha256':hashlib.sha256(patched).hexdigest(),'scenarios':tests,
                            'changed_source_refused':True,'playlist_browser_refused':True,
                            'unknown_addon_refused':True,'post_abort_initialization_prevented':addon!='plugin.video.redlight'}
    report={'passed':True,'addons':results,'actual_function_scenarios':20,
            'abort_waits_reproduced':8,'known_caller_guards':3,
            'source_guard_rejections':12,'host_only':True,'complete_shutdown_proven':False,
            'scope':'Compiled exact-loaded-byte transformer, actual archived read-only wait functions and corrected caller bodies; current executed bytes must match before any application.'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PASS: 20 actual startup-function scenarios, 3 guarded callers, 12 unknown/mismatched source refusals; no writes or services discarded.')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--addons',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();verify(args.addons,args.out)
