"""Selected non-shutdown P0 checks against the exact shipped source, host only."""
import ast, hashlib, importlib.util, json, os, re, subprocess, sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET
import patch_p0_finish as fix
import manifest

BASE=Path(os.environ['INFINITY_P0_PARENT_SOURCES']).resolve()

def files(aid):return {p.relative_to(BASE/aid).as_posix():p.read_bytes() for p in (BASE/aid).rglob('*') if p.is_file()}

def module(raw,name):
    m=types.ModuleType(name);exec(compile(raw,name,'exec',dont_inherit=True),m.__dict__);return m

class P0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original={aid+'/'+n:b for aid in (fix.CC,'script.infinity.uirepair','script.infinity.watchedbridge','script.infinity.rails') for n,b in files(aid).items()}
        cls.first=fix.firstparty(cls.original)

    def test_latest_movie_and_show_exact_selection_and_wrong_identity_rejected(self):
        raw=self.first[fix.CC+'/context.py'];tree=ast.parse(raw)
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='title_popup')
        decoder=module((BASE/fix.CC/'infinity_modules/uirepair/latest_identity.py').read_bytes(),'decoder')
        for kind in ('movie','tvshow'):
            route='plugin://plugin.video.umbrella/?action='+('play' if kind=='movie' else 'seasons')+'&tmdb=330430'
            wrapped=decoder.encode(route,kind,{'tmdb':'330430'});seen=[];notices=[]
            class Tag:
                def getMediaType(self):return kind
                def getUniqueID(self,name):return '330430' if name=='tmdb' else ''
                def getPlayCount(self):return 0
            class Item:
                def getProperty(self,name):return ''
                def getPath(self):return wrapped
                def getVideoInfoTag(self):return Tag()
                def isFolder(self):return kind=='tvshow'
            track=types.ModuleType('infinity_trakt');track._bridge=lambda:(None,None)
            track.selected=lambda item,*unused: seen.append((item.getPath(),item.getVideoInfoTag().getUniqueID('tmdb'))) or {'key':'selected'}
            track.notice=lambda *args:notices.append(args)
            selection=types.ModuleType('selection_contract');selection.read=lambda item:None
            metadata=types.ModuleType('title_metadata');metadata.capture=lambda item:{'title':'Exact original'}
            contract=types.SimpleNamespace(files={fix.CC+'/infinity_modules/uirepair/latest_identity.py':hashlib.sha256((BASE/fix.CC/'infinity_modules/uirepair/latest_identity.py').read_bytes()).hexdigest()})
            loader=types.ModuleType('module_contract');loader.source_module=lambda *args:decoder
            fake={n:types.ModuleType(n) for n in ('xbmcaddon','xbmcvfs')}
            fake.update(infinity_trakt=track,selection_contract=selection,title_metadata=metadata,module_contract=loader)
            env=dict(xbmc=types.SimpleNamespace(getSkinDir=lambda:'skin.infinity.diggz'),
                hub=types.SimpleNamespace(verified_ids=lambda value:{k:str(v) for k,v in value.items() if v}),
                _infinity_contract=contract,_popup_module=lambda:types.SimpleNamespace(show_item_menu=lambda *a,**kw:True))
            with patch.dict(sys.modules,fake):
                exec(compile(ast.Module(body=[function],type_ignores=[]),'actual-title-popup','exec'),env)
                self.assertTrue(env['title_popup'](Item()));self.assertEqual(seen,[(route,'330430')])
                # A live wrong-title tag must never authorize the original route.
                original=Tag.getUniqueID;Tag.getUniqueID=lambda self,name:'777' if name=='tmdb' else ''
                self.assertFalse(env['title_popup'](Item()));self.assertEqual(len(seen),1)
                Tag.getUniqueID=original
                contract.files[next(iter(contract.files))]='0'*64
                self.assertFalse(env['title_popup'](Item()));self.assertEqual(len(seen),1)

    def test_home_feed_paths_geometry_existing_power_actions_and_parent_pins_preserved(self):
        old=files(fix.SKIN);new,proof=fix.skin(old)
        self.assertEqual(len(proof['gated_feeds_per_profile']),14)
        for name in old:
            if name.endswith('/Home.xml'):
                original=ET.fromstring(old[name]);updated=ET.fromstring(new[name])
                original_feeds=original.findall('.//content[@target]');updated_feeds=updated.findall('.//content[@target]')
                includes=str(Path(name).parent)+'/Includes_InfinityHomeUnified.xml'
                if includes not in new:includes='16x9/Includes_InfinityHomeUnified.xml'
                definitions={n.get('name'):n for n in ET.fromstring(new[includes]).findall('variable')}
                self.assertEqual(len(updated_feeds),53)
                for a,b in zip(original_feeds,updated_feeds):
                    self.assertEqual(a.attrib,b.attrib)
                    variable=definitions[b.text[5:-1]]
                    self.assertEqual(variable[0].text,a.text)
                    self.assertIn('Control.IsVisible(',variable[0].get('condition'))
                    self.assertIsNone(variable[-1].text)
            if name.endswith('/DialogButtonMenu.xml'):
                root=ET.fromstring(new[name]);row=root.find(".//control[@id='16000']")
                self.assertIsNotNone(row)
                click=row.find("control[@id='1600']/onclick").text
                self.assertIn('InfinityAskEveryTimeActivity',click)
                self.assertNotIn('dialog.close',click)
        protected=json.loads(new['Infinity-Protected-Manifest.json'])['protected_files']
        self.assertTrue(all(hashlib.sha256(new[n]).hexdigest()==pin for n,pin in protected.items()))
        # An unexpected signed source must fail, never silently rebase.
        bad=dict(old);bad['unified/Home.xml']+=b'\n'
        with self.assertRaises(ValueError):fix.skin(bad)

    def test_continue_real_cards_batched20_and_same_touch_identity(self):
        name='p0_ui';runtime=types.ModuleType(name+'.runtime')
        runtime.addons=lambda:[];runtime.hidden=lambda aid:False;runtime.destination=lambda aid:None
        saved=[{'key':'movie:'+str(i),'synthetic_next':False} for i in range(100)]
        seen=[];calls=[];properties=[];home_properties=[];directory_results=[]
        class Item:
            def setProperty(self,key,value):properties.append((key,value))
        plugin=types.SimpleNamespace(PROFILE='per-profile',setting_bool=lambda *a:True,
            hub=types.SimpleNamespace(load_view=lambda p:{'revision':9},KEY_RE=re.compile(r'movie:[0-9]+')),
            _values_for=lambda *a:saved,prepare_render=lambda *a:a[-1],
            _list_item=lambda e,*a,**k:(seen.append(e['key']) or 'verified:'+e['key'],Item()))
        access=types.ModuleType(name+'.controller_access');access.load=lambda:plugin
        xb=types.ModuleType('xbmc');xb.log=lambda *a:None;xb.LOGWARNING=2
        gui=types.ModuleType('xbmcgui');gui.Window=lambda id:types.SimpleNamespace(getProperty=lambda key:'standard',setProperty=lambda k,v:home_properties.append((k,v)))
        native=types.ModuleType('xbmcplugin');native.setContent=lambda *a:None
        native.addDirectoryItems=lambda h,rows,**kw:calls.append((h,rows,kw))
        native.endOfDirectory=lambda *a,**kw:directory_results.append(kw)
        fake={name:types.ModuleType(name),name+'.runtime':runtime,name+'.controller_access':access,'xbmc':xb,'xbmcgui':gui,'xbmcplugin':native}
        fake[name].__path__=[]
        with patch.dict(sys.modules,fake),patch.object(sys,'argv',['plugin://uirepair','1','?action=continue&media=movie']):
            m=types.ModuleType(name+'.plugin');m.__package__=name
            exec(compile(self.first[fix.CC+'/infinity_modules/uirepair/plugin.py'],'actual-ui-plugin','exec'),m.__dict__)
            m.main()
        self.assertEqual(seen,[e['key'] for e in saved[:20]])
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][2],{'totalItems':20})
        self.assertEqual([value for key,value in properties if key=='Infinity.UI.Token'],seen)
        self.assertEqual(home_properties,[('Infinity.Home.FirstViewportReady','true')])
        self.assertEqual(directory_results,[{'succeeded':True,'cacheToDisc':False}])

    def test_health_resolves_signed_consolidated_code_and_real_extension_shims(self):
        raw=(Path(__file__).parent/'infinity_runtime_identity.py').read_bytes()
        class Addon:
            def __init__(self,aid):self.aid=aid
            def getAddonInfo(self,key):
                if key=='path':return str(BASE/self.aid)
                if key=='version':return ET.parse(BASE/self.aid/'addon.xml').getroot().get('version')
                return ''
            def getSetting(self,key):return ''
        xb=types.ModuleType('xbmc');xb.getCondVisibility=lambda key:True
        xa=types.ModuleType('xbmcaddon');xa.Addon=Addon
        xv=types.ModuleType('xbmcvfs');xv.translatePath=lambda p:p
        xg=types.ModuleType('xbmcgui');xg.Window=lambda id:types.SimpleNamespace(getProperty=lambda key:'')
        contract=types.SimpleNamespace(files={n:hashlib.sha256(b).hexdigest() for n,b in self.original.items()},
            identity=types.SimpleNamespace(manifest_sha256='host-fixture-only',package_version='0.3.5.48',protocol_api=1))
        with patch.dict(sys.modules,dict(xbmc=xb,xbmcaddon=xa,xbmcvfs=xv,xbmcgui=xg)):
            m=module(raw,'inventory');m._signed_inventory=lambda:contract;result=m.collect()
        for aid,(family,members) in m.MIGRATED.items():
            row=next(r for r in result['addons'] if r['id']==aid)
            for leaf in members:
                self.assertEqual(row['files']['infinity_modules/'+family+'/'+leaf]['state'],'AUTHENTICATED')
            self.assertNotIn('latest_identity.py',row['files'])
            self.assertNotEqual(row['files']['addon.xml'].get('state'),'MISSING_OR_UNVERIFIED')

    def test_single_tap_existing_preference_commit_and_truthful_failure_java(self):
        # Compile and execute the actual new Activity against a minimal Android
        # transport. No native app, shutdown class, exit protocol or data fixture.
        sources={
        'android/os/Bundle.java':'package android.os; public class Bundle {}',
        'android/content/Context.java':'package android.content; public class Context { public static final int MODE_PRIVATE=0; }',
        'android/content/Intent.java':'package android.content; public class Intent { public String getAction(){return "com.projectinfinity.kodi.action.ASK_EVERY_TIME";} }',
        'android/content/SharedPreferences.java':'package android.content; public interface SharedPreferences { Editor edit(); boolean contains(String key); interface Editor { Editor remove(String key); boolean commit(); } }',
        'android/app/Activity.java':'package android.app; public class Activity extends android.content.Context { public boolean finished; public void onCreate(android.os.Bundle b){} public android.content.Intent getIntent(){return new android.content.Intent();} public void finish(){finished=true;} }',
        'android/widget/Toast.java':'package android.widget; public class Toast { public static final int LENGTH_SHORT=0; public static String last; public static Toast makeText(android.content.Context c, String t,int d){last=t;return new Toast();} public void show(){} }',
        'com/projectinfinity/kodi/InfinityJavaPersistence.java':'''package com.projectinfinity.kodi;
        final class InfinityJavaPersistence {
          static final Pref prefs=new Pref(); static String store; static int mode;
          public static android.content.SharedPreferences preferences(android.content.Context c,String n,int m){store=n;mode=m;return prefs;}
          static class Pref implements android.content.SharedPreferences,android.content.SharedPreferences.Editor {
            boolean present=true,success=true;String removed="";int commits;
            public android.content.SharedPreferences.Editor edit(){return this;}
            public android.content.SharedPreferences.Editor remove(String k){removed=k;return this;}
            public boolean commit(){commits++;if(success)present=false;return success;}
            public boolean contains(String k){if(!"default".equals(k))throw new AssertionError();return present;}
          }
        }''',
        'com/projectinfinity/kodi/PreferenceCheck.java':'''package com.projectinfinity.kodi;
        public class PreferenceCheck {public static void main(String[] args){
          InfinityAskEveryTimeActivity a=new InfinityAskEveryTimeActivity();a.onCreate(null);
          if(!a.finished||!"infinity_experience".equals(InfinityJavaPersistence.store)||InfinityJavaPersistence.mode!=0||!"default".equals(InfinityJavaPersistence.prefs.removed)||InfinityJavaPersistence.prefs.present||InfinityJavaPersistence.prefs.commits!=1||!"Ask every time enabled".equals(android.widget.Toast.last))throw new AssertionError();
          InfinityJavaPersistence.prefs.present=true;InfinityJavaPersistence.prefs.success=false;
          InfinityAskEveryTimeActivity b=new InfinityAskEveryTimeActivity();b.onCreate(null);
          if(!b.finished||!InfinityJavaPersistence.prefs.present||!"Ask every time could not be saved".equals(android.widget.Toast.last))throw new AssertionError();
          System.out.println("PASS actual preference helper existing store/key, one commit, failed-save feedback, no session operation");
        }}'''}
        with tempfile.TemporaryDirectory(prefix='p0-preference-host-') as temp:
            root=Path(temp);paths=[]
            for n,text in sources.items():
                p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);paths.append(str(p))
            paths.append(str(Path(__file__).parent/'InfinityAskEveryTimeActivity.java'))
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','--release','8','-d',str(root/'classes'),*paths],check=True,capture_output=True)
            result=subprocess.run(['java','-cp',str(root/'classes'),'com.projectinfinity.kodi.PreferenceCheck'],check=True,capture_output=True,text=True)
            self.assertIn('PASS actual preference helper',result.stdout)

if __name__=='__main__':unittest.main(verbosity=2)
