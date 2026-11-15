#!/usr/bin/env python3
"""Execute publisher function code with inert external UI/network fixtures.

Only native caller classification is tested here, not Kodi GUI rendering.
No installed add-on or owner profile is read or changed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import types

HERE=Path(__file__).resolve().parent
PRODUCTION=HERE.parent/"native/overlay/xbmc/interfaces/legacy"
PINS={'plugin.py':'f197feaf23a5115e3d593a2cb7586b70706cd93701e107feb2c859be593f3ad0',
      'dialog.py':'ab3e19bd94f3575ba0a2b3ec957bfa69f1fe4a439d3f2a21cd4cc2e45cb56e97'}


def code(module,name):
    if module.co_qualname==name:return module
    for item in module.co_consts:
        if isinstance(item,types.CodeType):
            found=code(item,name)
            if found:return found
    return None


def child(root,extension):
    sys.path.insert(0,str(extension));import promotion_probe as probe
    source=root/'script.module.slyguy/resources/modules/slyguy'
    modules={name:compile((source/name).read_bytes(),str(source/name),'exec') for name in PINS}
    NS=types.SimpleNamespace
    dialog_scope={'make_heading':lambda heading:heading or 'Provider','QRCodeDialog':probe.Surface,
                  'xbmcgui':NS(Dialog=probe.Surface)}
    dialog=types.FunctionType(code(modules['dialog.py'],'ok'),dialog_scope,'ok',(None,None))
    settings=NS(LAST_SUPPORT_REMINDER=NS(value=1),getBool=lambda *args:False)
    plugin_scope={'require_update':lambda:None,'settings':settings,'_handle':lambda:1,
        'xbmcplugin':NS(setContent=lambda *a:None,setPluginCategory=lambda *a:None,
            addSortMethod=lambda *a:None,endOfDirectory=lambda *a,**k:None,setResolvedUrl=lambda *a:None),
        'is_donor':lambda:False,'time':NS(time=lambda:1000000),'SUPPORT_REMINDER':10,
        'gui':NS(ok=dialog),'_':NS(SHOW_SUPPORT=30331),'SUPPORT_URL':'https://donate.slyguy.uk',
        'process_news':lambda:None,'QUALITY_SKIP':-1,'set_kodi_string':lambda *a:None,
        'json':json,'xbmc':NS(getCondVisibility=lambda *a:False)}
    support=types.FunctionType(code(modules['plugin.py'],'process_support'),plugin_scope)
    plugin_scope['process_support']=support
    display=types.FunctionType(code(modules['plugin.py'],'Folder.display'),plugin_scope)
    play=types.FunctionType(code(modules['plugin.py'],'Item.play'),plugin_scope)
    folder=NS(show_news=True,items=[],no_items_label=None,art={},thumb=None,fanart=None,
        content=None,title=None,sort_methods=[1],updateListing=False,cacheToDisc=False)
    movie=NS(playable=False,proxy_data={},resume_from=None,play_skips=[],get_li=lambda **k:None,
        path='fixture://media',play_next={},callback={},manifest='fixture://media',windowed=False)
    rows=[]
    def invoke(name,action,matched,pending=False):
        settings.LAST_SUPPORT_REMINDER.value=1;probe.reset(pending);action()
        observed=probe.results()
        assert observed['events']==[('qr',matched),('ok',matched)],(name,observed)
        assert observed['closed']==1,(name,observed)
        rows.append({'case':name,'matched':matched,'qr_closed':True,'pending_error_preserved':pending})
    invoke('automatic_folder',lambda:display(folder),True)
    invoke('automatic_player',lambda:play(movie),True)
    invoke('manual_donation',lambda:dialog('Support',qr='fixture://qr'),False)
    invoke('error_security_dialog',lambda:dialog('Important error',qr='fixture://qr'),False)
    invoke('pending_exception',lambda:display(folder),True,pending=True)
    original=dialog.__code__;dialog.__code__=original.replace(co_consts=original.co_consts+('modified-loaded-code',))
    invoke('loaded_code_differs_from_disk',lambda:display(folder),False);dialog.__code__=original
    original=display.__code__;display.__code__=original.replace(co_consts=original.co_consts+('modified-caller',))
    invoke('automatic_caller_modified',lambda:display(folder),False);display.__code__=original
    raw=(source/'dialog.py').read_bytes();(source/'dialog.py').write_bytes(raw+b'\n# changed source\n')
    invoke('unknown_source',lambda:display(folder),False);(source/'dialog.py').write_bytes(raw)
    (source/'dialog.py').rename(source/'real-dialog.py');(source/'dialog.py').symlink_to(source/'real-dialog.py')
    invoke('source_symlink',lambda:display(folder),False)
    (source/'dialog.py').unlink();(source/'real-dialog.py').rename(source/'dialog.py')
    import os
    (source/'dialog.py').rename(source/'real-dialog.py');os.mkfifo(source/'dialog.py')
    invoke('source_fifo',lambda:display(folder),False)
    (source/'dialog.py').unlink();(source/'real-dialog.py').rename(source/'dialog.py')
    def audit(event,args):
        if event in ('compile','marshal.dumps'):probe.reenter()
    sys.addaudithook(audit)
    invoke('audit_reentrancy',lambda:display(folder),True)
    return dict(optimization=sys.flags.optimize,cases=rows,GUI='NOT_TESTED',installed_provider='NOT_TESTED')


def main():
    p=argparse.ArgumentParser();p.add_argument('publisher',type=Path);p.add_argument('--out',type=Path);p.add_argument('--child',type=Path)
    a=p.parse_args()
    assert sys.version_info[:3]==(3,11,7),'Pinned actual CPython required'
    if a.child:
        print(json.dumps(child(a.publisher,a.child)));return
    assert a.out
    for name,digest in PINS.items():assert hashlib.sha256((a.publisher/name).read_bytes()).hexdigest()==digest
    with tempfile.TemporaryDirectory(prefix='infinity500-promotion-') as temporary:
        work=Path(temporary);extension=work/('promotion_probe'+sysconfig.get_config_var('EXT_SUFFIX'))
        subprocess.run(['g++','-std=c++17','-shared','-fPIC','-O1','-Wall','-Wextra','-Werror','-Wno-missing-field-initializers',
            '-I'+sysconfig.get_path('include'),'-I'+str(PRODUCTION),str(HERE/'probe.cpp'),'-lcrypto','-o',str(extension)],check=True)
        rows=[]
        for optimize in (0,1,2):
            root=work/str(optimize);target=root/'script.module.slyguy/resources/modules/slyguy';target.mkdir(parents=True)
            for name in PINS:shutil.copyfile(a.publisher/name,target/name)
            result=subprocess.run([sys.executable,*(['-'+'O'*optimize] if optimize else []),__file__,str(root),'--child',str(work)],text=True,capture_output=True,timeout=30)
            if result.returncode:print(result.stdout,result.stderr,file=sys.stderr);raise RuntimeError('Native classifier case failed')
            rows.append(json.loads(result.stdout))
        a.out.write_text(json.dumps({'status':'PASS_NATIVE_CALLER_CLASSIFIER_HOST_ONLY','Python':list(sys.version_info[:3]),
            'source_pins':PINS,'header_sha256':hashlib.sha256((PRODUCTION/'InfinityPromotionalDialog.h').read_bytes()).hexdigest(),
            'results':rows,'Android':'NOT_RUN','GUI_rendering':'NOT_RUN','owner_popup_coverage':'INSTALLED_SOURCE_UNVERIFIED'},indent=2)+'\n')


if __name__=='__main__':main()
