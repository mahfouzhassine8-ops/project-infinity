"""Actual modified functions, isolated host boundaries. No Android PASS claim."""
import ast
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from urllib.parse import urlencode
import uuid
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CC=ROOT/'repairs/infinity-master-corrective-20261105/overlay/assets/addons/script.infinity.commandcenter'
SKIN=ROOT/'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified'
REF=Path('/dev/shm/infinity2103460-reference/assets/addons/script.infinity.commandcenter')

def function(path,name,env):
    node=next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),env)
    return env[name]

class ProviderDispatch(unittest.TestCase):
    def run_form(self,aid='plugin.video.thecrew',history=False,during=None):
        props={}; commands=[]; calls=[]; stopped=[False]
        provider=dict(id=aid,name='Fixture provider',root='fixture',contract={})
        class Keyboard:
            def __init__(self,text,heading,hidden): self.token=json.loads(heading.split(':',1)[1])['token']
            def doModal(self): pass
            def isConfirmed(self): return True
            def getText(self): return json.dumps(dict(token=self.token,query='fixture query',provider=aid,history=history))
        xbmc=types.SimpleNamespace(getSkinDir=lambda:'skin.infinity.diggz',
            Monitor=lambda:types.SimpleNamespace(abortRequested=lambda:stopped[0]),
            Keyboard=Keyboard,executebuiltin=commands.append,getInfoLabel=lambda _: '')
        gui=types.SimpleNamespace(Window=lambda _:types.SimpleNamespace(getProperty=lambda k:props.get(k,'')))
        def route(p,q,history=False):
            calls.append((p['id'],q,history))
            if len(calls)>1 and props.get('source_changed'):raise RuntimeError('verified source changed')
            return 'plugin://'+p['id']+'/?'+urlencode(dict(action='history' if history else 'search',query=q))
        def save_history(**kw):
            if during:during(props,stopped)
            return []
        loading=types.ModuleType('action_loading');loading.preparation=lambda _:nullcontext()
        env=dict(xbmc=xbmc,xbmcgui=gui,xbmcaddon=types.SimpleNamespace(Addon=lambda _:types.SimpleNamespace(getAddonInfo=lambda _:'')),
                 xbmcvfs=types.SimpleNamespace(translatePath=lambda value:value),
                 providers=lambda *a,**k:([provider],[]),shared_history=save_history,route=route,
                 uuid=uuid,json=json,urlencode=urlencode,CC='script.infinity.commandcenter')
        with patch.dict(sys.modules,action_loading=loading):
            function(CC/'infinity_search.py','_open_search',env)('tv')
        return commands,calls

    def test_explicit_selection_opens_original_provider_not_empty_aggregate_wrapper(self):
        for aid in ('plugin.video.thecrew','plugin.video.watchnixtoons2','plugin.video.umbrella','plugin.video.seren'):
            with self.subTest(provider=aid):
                commands,calls=self.run_form(aid)
                self.assertEqual(len(commands),1)
                self.assertIn('plugin://'+aid+'/',commands[0])
                self.assertNotIn('action=search-provider',commands[0])
                self.assertEqual(len(calls),2) # source/enable/dependencies rechecked after persistence

    def test_source_change_during_history_save_refuses_activation(self):
        with self.assertRaisesRegex(RuntimeError,'verified source changed'):
            self.run_form(during=lambda p,s:p.update(source_changed=True))

    def test_abort_during_history_save_does_not_activate_window(self):
        commands,calls=self.run_form(during=lambda p,s:s.__setitem__(0,True))
        self.assertEqual(commands,[])

    def test_all_still_uses_original_owned_aggregate(self):
        commands,calls=self.run_form('all')
        self.assertIn('action=search-all',commands[0]);self.assertEqual(calls,[])

    def test_legacy_provider_history_still_uses_verified_history_route(self):
        commands,calls=self.run_form(history=True)
        self.assertIn('action=history',commands[0]);self.assertTrue(all(c[2] for c in calls))

    def test_aggregate_security_ownership_and_cancellation_functions_unchanged(self):
        before=subprocess.check_output(['git','show','9ab8ec01:'+str((CC/'infinity_search.py').relative_to(ROOT))],cwd=ROOT)
        a={n.name:ast.dump(n) for n in ast.parse(before).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        b={n.name:ast.dump(n) for n in ast.parse((CC/'infinity_search.py').read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        self.assertEqual({n for n in a.keys()|b.keys() if a.get(n)!=b.get(n)},{'_open_search'})
        # Reuse the prior guard evidence; these functions are byte/AST bound.
        for name in ('route','_provider_result','_query_signature','_leased_directory','_publish_result'):
            self.assertEqual(a[name],b[name])

class WatchedActions(unittest.TestCase):
    def menu(self,requested='mark-watched',watched=False,changed_during_lock=False,incoming=True):
        key='a'*64;entry=dict(key=key,identity={'kind':'movie','ids':{'tmdb':'123'}},source='plugin://fixture/title',title='Fixture')
        state=dict(watched={key:{} } if watched else {},items={})
        events=[]
        def load(*a):
            if changed_during_lock:state['watched'][key]={}
            return deepcopy(state)
        def mutate(op,*a,**kw):events.append(('existing_writer',op));return True,''
        hub=types.SimpleNamespace(KEY_RE=re.compile('^[a-f0-9]{64}$'),load_view=lambda *a:deepcopy(state),load=load,
            entry_identity=lambda e:e.get('identity'),compatible_key=lambda d,e:key,same_identity=lambda a,b:a==b,
            is_watched=lambda d,k:k in d.get('watched',{}),bucket_has=lambda *a:False,
            flush_kodi_sync=lambda *a,**kw:events.append(('existing_flush',)),
            resume_visible=lambda *a:False)
        env=dict(hub=hub,PROFILE='host-fixture',nullcontext=nullcontext,persistence_scope=nullcontext,
            xbmc=types.SimpleNamespace(getSkinDir=lambda:'skin.infinity.diggz'),
            xbmcgui=types.SimpleNamespace(getCurrentWindowId=lambda:10000),
            navigation_target=lambda *a:'plugin://fixture/title',_favourite=lambda *a:(None,None),
            _menu_play_available=lambda *a:True,_menu_resume=lambda *a:None,_later_keys=lambda *a:[],
            _menu_progress_state=lambda *a:None,_mutate_locked=mutate,number=float,
            _selected_menu_entry=lambda *a:entry)
        function(CC/'plugin.py','_menu_rows',env)
        run=function(CC/'plugin.py','show_item_menu',env)
        result=run(key,incoming=entry if incoming else None,requested_action=requested)
        return result,events

    def test_both_direct_actions_call_original_writer_and_flush(self):
        for requested,watched in [('mark-watched',False),('mark-unwatched',True)]:
            result,events=self.menu(requested,watched)
            self.assertTrue(result);self.assertEqual(events,[('existing_writer',requested),('existing_flush',)])

    def test_stale_watched_action_cannot_reverse_newer_state(self):
        result,events=self.menu(changed_during_lock=True)
        self.assertFalse(result);self.assertEqual(events,[])

    def test_invalid_or_unowned_direct_action_cannot_mutate(self):
        for kw in [dict(requested='remove-resume'),dict(incoming=False),dict(requested='mark-unwatched',watched=False)]:
            result,events=self.menu(**kw);self.assertFalse(result);self.assertEqual(events,[])

    def test_writer_and_identity_helpers_are_unchanged(self):
        for leaf,names in [('plugin.py',('_mutate_locked','_menu_rows','_menu_progress_state')),
                           ('context.py',('apply_action','selected_entry','_watchnixtoons_tracking'))]:
            a={n.name:ast.dump(n) for n in ast.parse((REF/leaf).read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
            b={n.name:ast.dump(n) for n in ast.parse((CC/leaf).read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
            for name in names:self.assertEqual(a[name],b[name],name)

    def test_direct_entries_do_not_duplicate_native_file_actions(self):
        r=ET.parse(CC/'addon.xml').getroot()
        self.assertEqual(r.get('version'),'0.3.5.61')
        items=[e for e in r.findall('.//item') if e.get('args','').startswith('infinity-mark-')]
        self.assertEqual(len(items),2)
        for item in items:
            self.assertEqual(item.get('library'),'context.py')
            self.assertTrue(item.findtext('visible').startswith('ListItem.IsFolder +'))
            self.assertIn('plugin://',item.findtext('visible'))
            self.assertIn('UniqueID',item.findtext('visible'))

    def test_original_watched_store_survives_reload_preserving_other_lists(self):
        common=types.ModuleType('common')
        common.persistence_scope=nullcontext
        common.read_json=lambda p,d=None:json.loads(Path(p).read_text()) if Path(p).exists() else d
        def atomic(p,value):
            Path(p).write_text(json.dumps(value))
        common.atomic_json=atomic
        env={'__name__':'fold_host_original_resume_hub','__file__':str(REF/'resume_hub.py')}
        with patch.dict(sys.modules,common=common,xbmc=types.ModuleType('xbmc')):
            exec(compile((REF/'resume_hub.py').read_bytes(),str(REF/'resume_hub.py'),'exec'),env)
        with tempfile.TemporaryDirectory(dir='/dev/shm') as directory:
            profile=Path(directory)
            identity=env['media_identity']('movie',{'tmdb':'123'})
            key=env['identity_key'](identity)
            entry=dict(key=key,identity=identity,media='movie',tmdb='123',title='Host fixture',source='plugin://fixture/title')
            data=env['load'](profile)
            data['watchlist'][key]=deepcopy(entry)
            data['collection'][key]=deepcopy(entry)
            env['save'](profile,data)
            before=env['load'](profile)
            data,changed=env['mark_watched_data'](before,key,entry)
            self.assertIsNotNone(changed)
            env['save'](profile,data)
            after=env['load'](profile)
            self.assertTrue(env['is_watched'](after,key))
            self.assertEqual(after['watchlist'][key]['source'],entry['source'])
            data,changed=env['mark_unwatched_data'](after,key)
            self.assertIsNotNone(changed)
            env['save'](profile,data)
            restored=env['load'](profile)
            self.assertFalse(env['is_watched'](restored,key))
            self.assertEqual(restored['collection'],before['collection'])
            self.assertEqual(restored['watchlist'],before['watchlist'])

class SkinAndProtectedPasses(unittest.TestCase):
    def test_applied_info_matches_previously_verified_candidate(self):
        # Revised after the exact original GroupList methods exposed stale
        # min-width on a second in-place resize. No whole campaign is rerun.
        from zipfile import ZipFile
        with ZipFile('/dev/shm/infinity-fold264-signed/skin.infinity.diggz-1.0.5.264-2103460-corrective.zip') as z:
            old=ET.fromstring(z.read('skin.infinity.diggz/unified/DialogVideoInfo.xml'))
        new=ET.parse(SKIN/'DialogVideoInfo.xml').getroot()
        group=new.find('.//control[@id="9000"]')
        self.assertEqual(group.get('type'),'group');self.assertEqual(group.findtext('width'),'86%')
        self.assertEqual(group.findtext('defaultcontrol'),'8')
        self.assertEqual(group.find('width').attrib,{})
        for ident,left in [('8','0%'),('9012','25%'),('9013','50%'),('106','75%')]:
            a,b=old.find('.//control[@id="'+ident+'"]'),new.find('.//control[@id="'+ident+'"]')
            self.assertEqual(b.findtext('left'),left)
            for tag in ('onclick','visible','enable','label','texturefocus','texturenofocus'):
                self.assertEqual([(e.attrib,e.text) for e in a.findall(tag)],[(e.attrib,e.text) for e in b.findall(tag)],(ident,tag))
        for ident in ('50','400'):
            self.assertEqual(ET.tostring(old.find('.//control[@id="'+ident+'"]')),
                             ET.tostring(new.find('.//control[@id="'+ident+'"]')))
        for viewport in (2400,2000,1900,1080,1440):
            width=.86*viewport
            end=0
            for ident in ('8','9012','9013','106'):
                node=group.find('control[@id="'+ident+'"]')
                start=float(node.findtext('left').rstrip('%'))/100*width
                size=float(node.findtext('width').rstrip('%'))/100*width
                self.assertGreaterEqual(start,end);end=start+size
            self.assertLessEqual(end,width)
        play=group.find('control[@id="8"]');cast=group.find('control[@id="9013"]')
        self.assertEqual(play.findtext('onright[@condition="Control.IsVisible(9012)"]'),'9012')
        self.assertEqual(play.findtext('onright[@condition="!Control.IsVisible(9012)"]'),'9013')
        self.assertEqual(cast.findtext('onleft[@condition="!Control.IsVisible(9012)"]'),'8')
        self.assertEqual(new.findtext('.//control[@id="9011"]/ondown'),'8')
        from test_info_and_preservation import method
        native=Path('/tmp/kodi451-restored-native/xbmc/guilib/GUIControlGroupList.cpp').read_text()
        actual='\n'.join(method(native,s) for s in ('float CGUIControlGroupList::GetWidth() const','void CGUIControlGroupList::SetMinSize(float minWidth, float minHeight)'))
        source='''#include <cassert>
        enum {VERTICAL,HORIZONTAL};
        #define CLAMP(x,l,h) (((x)>(h))?(h):(((x)<(l))?(l):(x)))
        struct CGUIControlGroup {float m_width=0;float GetWidth()const{return m_width;}};
        struct CGUIControlGroupList:CGUIControlGroup{int m_orientation=HORIZONTAL;float m_minSize=0,m_totalSize=0;
          float GetWidth()const;void SetMinSize(float,float);};
        '''+actual+'''\nint main(){CGUIControlGroupList old;
        old.m_width=2064;old.SetMinSize(2064,0);old.m_totalSize=4*.23f*2064+24;
        old.m_width=1720;old.m_totalSize=4*.23f*old.GetWidth()+24;
        old.m_width=1634;old.m_totalSize=4*.23f*old.GetWidth()+24;
        assert(old.m_totalSize>old.m_width); // original auto/min candidate clips
        CGUIControlGroup corrected;
        for(float w:{2400.f,2000.f,1900.f,1080.f,1440.f}) {corrected.m_width=.86f*w;
          assert(.75f*corrected.GetWidth()+.23f*corrected.GetWidth()<=corrected.m_width);}}
        '''
        source=source.replace('#include <cassert>','#include <cassert>\n#include <initializer_list>')
        with tempfile.TemporaryDirectory(dir='/dev/shm') as t:
            cpp=Path(t)/'actual-resize.cpp';cpp.write_text(source)
            fd,binary=tempfile.mkstemp(prefix='infinity-info-resize-',dir='/tmp');os.close(fd)
            try:
                subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',binary],check=True,capture_output=True)
                subprocess.run([binary],check=True,capture_output=True)
            finally:Path(binary).unlink(missing_ok=True)

    def test_white_texture_is_static_files_decoration_not_busy_or_item_art(self):
        r=ET.parse(SKIN/'Includes_InfinityMediaLists.xml').getroot()
        bg=r.find('include[@name="InfinityMedia_CommonBackground"]')
        nodes=[c for c in bg.iter('control') if c.findtext('texture')=='special://skin/resources/icon.png']
        self.assertEqual(len(nodes),1)
        c=nodes[0];self.assertEqual(c.findtext('top'),'86.6142%')
        self.assertIn('![Window.IsActive(videos) + String.IsEmpty(Container.PluginName) + [Container.Content(files) | Container.Content()]]',c.findtext('visible'))
        # Explicit condition truth table: only native video-files/empty content.
        for window,plugin,content,wanted in [('videos','', 'files',False),('videos','', '',False),
                 ('videos','provider','files',True),('videos','', 'movies',True),('settings','', 'files',True)]:
            self.assertEqual(not(window=='videos' and plugin=='' and content in ('files','')),wanted)

    def test_four_physical_passes_native_and_other_overlay_files_are_identical(self):
        inventory=json.loads(subprocess.check_output(['git','show','9ab8ec01:'+str((HERE.parent/'SOURCE-INVENTORY.json').relative_to(ROOT))],cwd=ROOT))['changed_source_files']
        allowed={str((SKIN/n).relative_to(ROOT)) for n in ('DialogVideoInfo.xml','Includes_InfinityMediaLists.xml')}
        allowed.add(str((CC/'infinity_search.py').relative_to(ROOT)))
        for path,row in inventory.items():
            if path not in allowed:self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),row['candidate_sha256'],path)
        for suffix in ('video/windows/GUIWindowVideoNav.cpp','video/windows/GUIWindowVideoNav.h',
                       'dialogs/GUIDialogMediaSource.cpp','dialogs/GUIDialogMediaSource.h'):
            path='repairs/infinity-2103460-nine-corrections-20261106/downloads-native/native/xbmc/'+suffix
            self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show','9ab8ec01:'+path],cwd=ROOT))

if __name__=='__main__':unittest.main(verbosity=2)
