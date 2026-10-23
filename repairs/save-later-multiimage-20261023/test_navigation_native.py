"""Failure correlation, cancellation, stale callbacks and original-body preservation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import navigation_native
import test_lookup_native

MAIN=r'''
#include "InfinitySavedNavigationState.h"
#include <cassert>
using namespace InfinitySavedNavigation;
Ticket ticket(std::string token="one",std::string path="plugin://one/?id=1"){
 Ticket t;t.token=token;t.key=std::string(64,'a');t.originalPath=t.path=path;t.folder=true;t.attempted={"one"};return t;
}
int main(){
 Correlation s;
 s.Begin(ticket());assert(!s.Finish("one","plugin://one/?id=1",true,"failed"));assert(!s.Read());
 s.Begin(ticket());s.Cancelled("one");assert(!s.Finish("one","plugin://one/?id=1",false,"failed"));assert(!s.Read());
 s.Begin(ticket());assert(!s.Finish("wrong","plugin://one/?id=1",false,"failed"));assert(!s.Read()->failed);
 assert(!s.Finish("one","plugin://different/?id=1",false,"failed"));assert(!s.Read()->failed);
 auto failed=s.Finish("one","plugin://one/?id=1",false,"provider_directory_failed");assert(failed&&failed->failed);
 assert(!s.Finish("one","plugin://one/?id=1",false,"duplicate"));
 assert(!s.Next("wrong","plugin://two/?id=1","two"));
 assert(!s.Next("one","plugin://one/?id=2","one"));
 assert(s.Next("one","plugin://two/?id=1","two"));assert(!s.Read()->failed);
 assert(!s.Finish("one","plugin://one/?id=1",false,"late"));
 s.Begin(ticket("new","plugin://new/?id=2"));
 assert(!s.Finish("one","plugin://two/?id=1",false,"late"));assert(s.Read()->token=="new");
 s.Clear("one");assert(s.Read());s.Clear("new");assert(!s.Read());
 s.Begin(ticket());
 for(int i=2;i<=8;++i){
  auto t=s.Read();assert(s.Finish(t->token,t->path,false,"provider_directory_failed"));
  auto p=std::to_string(i);assert(s.Next("one","plugin://"+p+"/?id=1",p));
 }
 auto t=s.Read();assert(s.Finish(t->token,t->path,false,"provider_directory_failed"));
 assert(!s.Next("one","plugin://ninth/?id=1","ninth"));
}
'''


def run(source,overlay,out):
    # The original callback body is an exact substring, including all returns.
    pairs=(('xbmc/windows/GUIMediaWindow.cpp',
        'bool CGUIMediaWindow::Update(const std::string &strDirectory, bool updateFilterPath /* = true */)\n{',
        'bool CGUIMediaWindow::Refresh('),
        ('xbmc/filesystem/PluginDirectory.cpp',
        'bool CPluginDirectory::GetResolvedPluginResult(CFileItem& resultItem)\n{',
        'bool CPluginDirectory::GetPluginResult('))
    preserved=[]
    for name,start,end in pairs:
        original=(source/name).read_text();changed=(overlay/name).read_text()
        body=original.split(start,1)[1].split(end,1)[0][:-3]
        assert changed.count(body)==1,'Original operation body differs: '+name
        preserved.append(dict(path=name,original_body_sha256=hashlib.sha256(body.encode()).hexdigest()))
    # No original Search lease/lifecycle statement is removed or replaced.
    name='xbmc/interfaces/generic/ScriptRunner.cpp'
    original=(source/name).read_text();changed=(overlay/name).read_text()
    for assignment in ('false','cancelled'):
        addition='#if defined(TARGET_ANDROID)\n  m_infinityResultCancelled = '+assignment+';\n#endif\n'
        assert changed.count(addition)==1;changed=changed.replace(addition,'')
    for addition in (navigation_native.LOOKUP_DEADLINE, navigation_native.LOOKUP_PROTOCOL):
        assert changed.count(addition)==1;changed=changed.replace(addition,'')
    assert changed==original
    lookup = test_lookup_native.run(overlay/name)
    with tempfile.TemporaryDirectory(prefix='saved-correlation-') as directory:
        work=Path(directory);(work/'main.cpp').write_text(MAIN)
        exe=work/'test'
        r=subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread',
            '-I',str(navigation_native.HERE),str(work/'main.cpp'),'-o',str(exe)],capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    out.write_text(json.dumps(dict(passed=True,scope=__doc__,original_bodies=preserved,
        search_lifecycle_unchanged=True,saved_lookup=lookup,
        actual_android=False,actual_gui_execution=False),indent=2)+'\n')
    print('PASS failure correlation and exact original navigation body preservation')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','overlay','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.source,a.overlay,a.out)
