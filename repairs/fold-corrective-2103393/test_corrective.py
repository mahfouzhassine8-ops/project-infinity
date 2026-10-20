from __future__ import annotations
import ast
import copy
from contextlib import nullcontext
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from urllib.parse import urlencode,urlsplit
import xml.etree.ElementTree as ET
import corrective as c
import native93 as native
import dex93
import art93

def functions(raw,names,namespace):
    tree=ast.parse(raw)
    selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    exec(compile(ast.Module(body=selected,type_ignores=[]),'actual_component','exec'),namespace)
    return namespace

class Corrective(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apk=Path(os.environ.get('INFINITY_2103392_APK',str(c.ROOT.parent/'protected-2103392/Infinity-2103392-Coherent-Integration-EXPERIMENTAL.apk')))
        cls.before=c.read_parent(cls.apk)
        cls.after=c.components(cls.before)
        cls.delta=c.ledger(cls.before,cls.after)
        _,r,i=native.old_adapters()
        cls.classifier22=r.contracts(r.original_classifier(),cls.before)
        cls.coordinator22=r.coordinator(r.original_coordinator())
        cls.new_classifier=native.classifier(cls.classifier22,cls.before,cls.after)

    def target(self,raw=None):
        ns={'urlsplit':urlsplit,'re':re}
        functions(self.before[c.CC+'/experience.py'],{'stable_route','number'},ns)
        ns.update(setting_bool=lambda *a:True, time=types.SimpleNamespace(time=lambda:1000000),
                  _has_addon=lambda host,render:host!='missing',_has_tmdb_helper=lambda r:False,
                  hub=types.SimpleNamespace(entry_identity=lambda e:e.get('identity'),episode_number=lambda n:int(n) if str(n).isdigit() else -1))
        functions(raw or self.after[c.CC+'/plugin.py'],{'_target','_category','_values_for'},ns)
        return ns

    def test_exact_parent_and_reviewed_delta(self):
        self.assertEqual(self.delta,json.loads((c.HERE/'MEMBER-DELTA.json').read_text()))
        self.assertFalse(self.delta['removed_members'])
        self.assertFalse(any('cobra' in n.lower() for n in self.delta['changed_members']))
        for a,_,version in c.PACKAGES:
            self.assertEqual(ET.fromstring(self.after[a+'/addon.xml']).get('version'),version)

    def test_regression_stale_movie_preference_masked_good_capture(self):
        e={'key':'a'*64,'media':'movie','stable_source':'plugin://provider/?movie=1','updated':1}
        memory={e['key']:{'route':'https://expired.example/old','failures':0}}
        self.assertEqual(self.target(self.before[c.CC+'/plugin.py'])['_target'](e,memory),'')
        self.assertEqual(self.target()['_target'](e,memory),e['stable_source'])

    def test_saved_route_fallback_both_media_and_failed_preference(self):
        for media in ('movie','tv'):
            for failures in (0,2,10):
                e={'key':'a'*64,'media':media,'stable_source':'plugin://provider/?id=1','updated':1}
                self.assertEqual(self.target()['_target'](e,{e['key']:{'route':'https://expired.example/old','failures':failures}}),e['stable_source'])

    def test_successful_route_kept_and_identical_failed_route_not_retried(self):
        e={'key':'a'*64,'media':'movie','stable_source':'plugin://provider/?id=1','updated':1}
        for failures in (0,1):
            pref={e['key']:{'route':'plugin://preferred/?id=1','failures':failures}}
            self.assertEqual(self.target()['_target'](e,pref),'plugin://preferred/?id=1')
        self.assertEqual(self.target()['_target'](e,{e['key']:{'route':e['stable_source'],'failures':2}}),'')

    def test_missing_provider_or_expired_http_not_fabricated(self):
        for source in ('https://expired.example/stream','plugin://missing/?id=1',''):
            e={'key':'a'*64,'media':'tv','stable_source':source,'source':'https://expired.example/old','updated':1}
            self.assertEqual(self.target()['_target'](e,{}),'')

    def test_verified_episode_resolver_uses_show_and_episode(self):
        ns=self.target();ns['_has_tmdb_helper']=lambda _:True
        e={'media':'tv','tmdb':'wrong-episode-id','show_tmdb':'123','show_ids_verified':True,'season':2,'episode':8}
        route=ns['_target'](e,{})
        self.assertIn('tmdb_id=123&season=2&episode=8',route)
        e['show_ids_verified']=False;e.pop('show_tmdb')
        self.assertEqual(ns['_target'](e,{}),'')

    def test_contextual_movie_tv_headings(self):
        cat=self.target()['_category']
        self.assertEqual(cat('movie'),'Infinity Movies');self.assertEqual(cat('tv'),'Infinity TV Shows')
        for media,label in (('movie','Movies'),('tv','TV Shows')):
            for bucket in ('continue','next','watchlist','collection','history','progress','ratings','custom-lists'):
                self.assertTrue(cat(media,bucket).startswith(label+' — '))
        self.assertEqual(cat('tv','list','My shows'),'TV Shows — My shows')

    def test_skin_consumes_plugin_category_only_for_command_center(self):
        variables=0;headers=0;windows=0
        for name,body in self.after.items():
            if name.endswith('/Variables.xml'):
                variables+=1;root=ET.fromstring(body)
                var=root.find('variable[@name="InfinityResumeDirectoryTitle"]')
                values=var.findall('value');self.assertEqual(len(values),2)
                self.assertEqual(values[0].get('condition'),'String.IsEqual(Container.PluginName,script.infinity.commandcenter) + !String.IsEmpty(Container.PluginCategory)')
                self.assertEqual(values[0].text,'$INFO[Container.PluginCategory]')
                self.assertEqual(values[1].text,'$INFO[Container.FolderName]');self.assertFalse(values[1].attrib)
            elif name.endswith('/View_50_List.xml'):
                headers+=1
                self.assertEqual(body.count(b'$VAR[InfinityResumeDirectoryTitle]'),3)
                self.assertEqual(body.replace(b'$VAR[InfinityResumeDirectoryTitle]',b'$INFO[Container.FolderName]'),self.before[name])
            elif name.endswith('/MyVideoNav.xml'):
                windows+=1
                self.assertEqual(body.replace(b'<param name="Subtitle" value="$VAR[InfinityResumeDirectoryTitle]"',
                    b'<param name="Subtitle" value="$INFO[Container.FolderName]"'),self.before[name])
        self.assertEqual((variables,headers,windows),(10,10,10))
        profiles=lambda suffix:{n.rsplit('/',1)[0] for n in self.after if n.startswith(c.SKIN+'/') and n.endswith(suffix)}
        self.assertEqual(profiles('/Variables.xml'),profiles('/View_50_List.xml'))
        self.assertEqual(profiles('/Variables.xml'),profiles('/MyVideoNav.xml'))
        for profile in profiles('/Variables.xml'):
            self.assertIn(b'file="Variables.xml"',self.before[profile+'/Includes.xml'])

    def test_watchlist_history_owner_and_completed_filters_unchanged(self):
        for name in ('resume_hub.py','experience.py','context.py','common.py','persistence_participant.py'):
            self.assertEqual(self.before[c.CC+'/'+name],self.after[c.CC+'/'+name])
        self.assertEqual(self.target(self.before[c.CC+'/plugin.py'])['_values_for'].__code__.co_code,
                         self.target()['_values_for'].__code__.co_code)

    def context(self,entry):
        ns={};exec(compile(self.after[c.UI+'/controller_access.py'],'controller_access','exec'),ns)
        data={'items':{entry['key']:entry}}
        hub=types.SimpleNamespace(entry_identity=lambda e:e.get('identity'),load=lambda _:data,
                                 find_entry=lambda d,k:d['items'].get(k),same_identity=lambda a,b:bool(a and b and a==b),
                                 flush_kodi_sync=lambda _:None)
        calls=[]
        p=types.SimpleNamespace(hub=hub,PROFILE=Path('/unused'),persistence_scope=nullcontext,
          _context=lambda e,d,b:[('Reset Progress','RunPlugin(plugin://script.infinity.commandcenter/?'+urlencode({'key':e['key'],'op':'reset-progress'})+')'),
                                  ('Mark Watched','RunPlugin(plugin://script.infinity.commandcenter/?'+urlencode({'key':e['key'],'op':'mark-watched'})+')')],
          _mutate_locked=lambda *args:(calls.append(args) or True,''))
        return ns,p,data,calls

    def test_legacy_expired_record_menu_independent_of_playback(self):
        e={'key':'a'*64,'media':'movie','source':'https://expired.example','position':34}
        ns,p,data,calls=self.context(e)
        self.assertEqual(ns['_context_rows_data'](p,e['key'],data,e),[('Reset Progress','reset-progress')])
        self.assertTrue(ns['mutate'](p,e['key'],copy.deepcopy(e),'reset-progress',expected_label='Reset Progress'))
        self.assertEqual(len(calls),1)

    def test_legacy_record_change_and_watched_identity_fail_closed(self):
        for op in ('reset-progress','mark-watched'):
            e={'key':'a'*64,'media':'tv','source':'expired','position':34}
            ns,p,data,calls=self.context(e);old=copy.deepcopy(e)
            if op=='reset-progress':e['position']=35
            self.assertFalse(ns['mutate'](p,e['key'],old,op,expected_label='Reset Progress' if op=='reset-progress' else 'Mark Watched'))
            self.assertFalse(calls)

    def test_option_b_all_actual_layout_ids_and_no_other_panels(self):
        for name,body in self.before.items():
            if name.startswith(c.SKIN+'/') and name.endswith('/Home.xml'):
                root=ET.fromstring(body)
                for ident,section in c.POSTERS.items():
                    ctrl=root.find('.//control[@id="'+str(ident)+'"]')
                    self.assertIsNotNone(ctrl,name+' '+str(ident))
                    self.assertIn('plugin://plugin.video.umbrella/',ctrl.findtext('content',''))
                    self.assertIn(section,ctrl.findtext('visible',''))
                self.assertEqual(body,self.after[name].replace(b'>infinity_ui/header_dark_clock_safe.png</texture>',
                                 b'>infinity_ui/header_dark.png</texture>',1),'Home scrolling/normal tap changed')
        parsed=ast.parse(self.after[c.UI+'/home_option_b.py'])
        actual=next(ast.literal_eval(n.value) for n in parsed.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CONTROLS' for t in n.targets))
        self.assertEqual(actual,c.POSTERS)
        self.assertTrue(set(actual).isdisjoint({9200,8820,8720,19601,8830,8831}))

    def test_silent_only_existing_row_changed_health_dot_unchanged(self):
        count=0
        for name,body in self.before.items():
            if not name.endswith('/Custom_1191_InfinitySystemHub.xml'):continue
            count+=1;a,b=ET.fromstring(body),ET.fromstring(self.after[name])
            for ident in ('1191101','1191102','1191103','1191104','1191106','1191107'):
                self.assertEqual(ET.tostring(a.find('.//control[@id="'+ident+'"]')),
                                 ET.tostring(b.find('.//control[@id="'+ident+'"]')))
            health=lambda root:[ET.tostring(n) for n in root.iter('control') if n.findtext('texture')=='infinity_experience/health-orb.png' and n.findtext('visible')!='Skin.HasSetting(Infinity.SilentMode)']
            self.assertEqual(health(a),health(b))
            row=b.find('.//control[@id="1191108"]')
            self.assertEqual(row.get('type'),'button')
            self.assertEqual(row.findtext('onclick'),'Skin.ToggleSetting(Infinity.SilentMode)')
            dots=[n for n in b.iter('control') if n.findtext('texture')=='infinity_experience/health-orb.png' and n.findtext('visible')=='Skin.HasSetting(Infinity.SilentMode)']
            self.assertEqual(len(dots),1)
            self.assertEqual(dots[0].find('texture').get('colordiffuse'),'FF24A8FF')
            # The unified row has local coordinates; alternate layouts have
            # absolute pixel/percentage row coordinates. Match the relative
            # vertical offset rather than copying the red dot's global top.
            owner=next(n for n in a.iter() if a.find('.//control[@id="1191103"]') in list(n))
            red=next(n for n in owner.findall('control') if n.findtext('texture')=='infinity_experience/health-orb.png')
            from decimal import Decimal
            number=lambda node,tag:Decimal(node.findtext(tag).rstrip('%'))
            self.assertEqual(number(dots[0],'top')-number(row,'top'),number(red,'top')-number(a.find('.//control[@id="1191103"]'),'top'))
            self.assertFalse(row.findall('selected'))
        self.assertEqual(count,13)

    def test_browser_labels_bounded_with_arrow_gutter_and_matching_focus(self):
        count=0
        for name,body in self.after.items():
            if not name.endswith('/AddonBrowser.xml'):continue
            count+=1;r=ET.fromstring(body);panel=r.find('.//control[@id="50"]')
            for tag in ('itemlayout','focusedlayout'):
                labels=[n for n in panel.find(tag).iter('control') if n.findtext('label')=='$INFO[ListItem.Label]']
                self.assertEqual(len(labels),1)
                self.assertEqual(labels[0].get('type'),'label')
                self.assertEqual(labels[0].findtext('left'),'22%')
                self.assertEqual(labels[0].findtext('width'),'64%')
                self.assertEqual(labels[0].findtext('scroll'),'false')
            self.assertEqual(panel.find('itemlayout').attrib,panel.find('focusedlayout').attrib)
            self.assertEqual(r.find('.//control[@id="9096"]/onclick').text,'PreviousMenu')
        self.assertEqual(count,14)

    def test_player_settings_native_controls_kept_and_small_surface(self):
        parent=ET.fromstring(self.before[c.SKIN+'/unified/DialogSettings.xml'])
        for name,body in self.after.items():
            if name.endswith('/DialogSettings.xml') or name.endswith('/Custom_1195_InfinityAudioSubtitles.xml'):
                self.assertEqual(body,self.before[name])
            if name.endswith('/VideoOSD.xml'):
                # Contrast only; actions, transport geometry and the complete
                # working Playback group survive exactly.
                old=ET.fromstring(self.before[name]);new=ET.fromstring(body)
                for ident in ('202','263','291'):
                    a,b=old.find('.//control[@id="'+ident+'"]'),new.find('.//control[@id="'+ident+'"]')
                    if a is not None:self.assertEqual(ET.tostring(a),ET.tostring(b))
                for image in new.iter('control'):
                    tx=image.find('texture')
                    if tx is not None and tx.text in ('infinity_reference/play.png','infinity_reference/pause.png'):
                        self.assertEqual(tx.get('colordiffuse'),'FFFFFFFF')
                    if tx is not None and tx.text=='infinity_reference/rotate.png' and image.findtext('visible')=='Skin.HasSetting(Infinity.PlayerRotationUnlocked)':
                        self.assertEqual(tx.get('colordiffuse'),'FF00D9FF')
            if not name.endswith('/InfinityPlayerSettings.xml'):continue
            r=ET.fromstring(body);panel=r.find('.//control[@id="9900"]')
            self.assertEqual((panel.findtext('width'),panel.findtext('height')),('840','740'))
            self.assertEqual((panel.findtext('centerleft'),panel.findtext('centertop')),('50%','50%'))
            self.assertIsNotNone(r.find('.//control[@id="5"]'));self.assertIsNotNone(r.find('.//control[@id="60"]'))
            for ident in ('5','60','7','8','9','11','12','13','14','28','29','30','9002'):
                self.assertEqual(ET.tostring(parent.find('.//control[@id="'+ident+'"]')),
                                 ET.tostring(r.find('.//control[@id="'+ident+'"]')))

    def test_all_thirteen_pins_exact_and_legacy_classifiers_retained(self):
        _,r,_=native.old_adapters()
        pinmaps=[json.loads(self.after[a+'/CONTROLLER-PREIMAGES.json']) for a in (c.UI,c.WB)]
        self.assertEqual(pinmaps[0],pinmaps[1]);self.assertEqual(len(pinmaps[0]),13)
        for name,pin in pinmaps[0].items():self.assertEqual(pin,c.sha(self.after[c.CC+'/'+name]))
        old=r.coherence.contracts(self.classifier22.decode());new=r.coherence.contracts(self.new_classifier.decode())
        self.assertEqual(new[:len(old)],old)
        self.assertEqual(len(new)-len(old),3)
        for endpoint in r.coherence.ENDPOINTS:
            matches=r.coherence.matching_variants(self.new_classifier.decode(),c.CC,c.CC+'/'+endpoint,{n:c.sha(b) for n,b in self.after.items()})
            self.assertEqual(len(matches),1);self.assertEqual(len(matches[0]['pins']),13)

    def test_native_patch_exact_reversal_and_preservation(self):
        old=native.module('test93_option_b',c.ROOT/'repairs/2103390-bugfixes/group3/native_option_b_patch.py')
        window=b'HEAD\n'+b'''    std::string strFileNameLower = strFileName;
    StringUtils::ToLower(strFileNameLower);
    strLowerPath =  g_SkinInfo->GetSkinPath(strFileNameLower, &m_coordsRes);
    strPath = g_SkinInfo->GetSkinPath(strFileName, &m_coordsRes);'''+b'\nTAIL'
        before={native.CONTAINER:b'PREFIX\n'+old.METHOD.encode()+b'\nUNCHANGED RAILS COBRA TAPS',
                native.INPUT:b'UNCHANGED RAILS\nfor (const int mediaID : {8101, 8102})\nUNCHANGED TAPS',
                native.WINDOW:window,native.CONTRACT:self.classifier22,native.COORDINATOR:self.coordinator22}
        after=native.patches(before,self.before,self.after)
        self.assertEqual(set(after),native.PATHS)
        self.assertTrue(after[native.CONTAINER].endswith(b'UNCHANGED RAILS COBRA TAPS'))
        self.assertTrue(after[native.INPUT].startswith(b'UNCHANGED RAILS\n'))
        self.assertTrue(after[native.INPUT].endswith(b'\nUNCHANGED TAPS'))
        self.assertEqual(after[native.COORDINATOR].replace(b' && active["addon_version"].asString() != "0.3.5.23"',b'',1),self.coordinator22)
        for raw in (after[native.CONTAINER],after[native.WINDOW]):self.assertNotIn(b'KaiToast',raw)
        with self.assertRaises(ValueError):native.patches(after,self.before,self.after)
        # Compile and execute the actual modified method against the same
        # controlled Kodi peer ABI used by the passing predecessor tests.
        peers=native.module('corrective93_cpp_peer',c.ROOT/'repairs/2103390-bugfixes/group3/test_native_option_b_cpp.py')
        method=after[native.CONTAINER].removeprefix(b'PREFIX\n').removesuffix(b'\nUNCHANGED RAILS COBRA TAPS').decode()
        cases=peers.CASES.replace('  c.id=8101;\n  const auto count=',
            '''  for (int id : {8101,8102,8601,8602,8701,8702,8801,8802}) {
    c.id=id;
    c.m_waitForScrollEnd=true; // Android ACTION_DOWN capability query
    assert(c.OnInfinityOptionBLongPress(60,50));
    assert(!c.m_waitForScrollEnd);
    assert(gui.windows.home.focused==id);
    assert(messenger.calls.back().find("option-b,"+std::to_string(id)+",0,")!=std::string::npos);
  }
  for (int id : {9200,8820,8720,19601,8830,8831,50,9000}) {
    c.id=id;assert(!c.OnInfinityOptionBLongPress(60,50));
  }
  c.id=8101;
  const auto count=''')
        cases=cases.replace('  c.m_waitForScrollEnd=true;assert(!c.OnInfinityOptionBLongPress(160,50));\n',
                            '  c.m_waitForScrollEnd=true;\n')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'method.cpp';exe=root/'method'
            source.write_text(peers.PEERS+method+cases)
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS actual Group3 method',subprocess.check_output([str(exe)],text=True))
            routing=after[native.WINDOW].removeprefix(b'HEAD\n').removesuffix(b'\nTAIL').decode()
            code=r'''#include <cassert>
#include <algorithm>
#include <cctype>
#include <string>
constexpr int WINDOW_DIALOG_VIDEO_OSD_SETTINGS=10123, WINDOW_DIALOG_AUDIO_OSD_SETTINGS=10124,
              WINDOW_DIALOG_SUBTITLE_OSD_SETTINGS=10159;
struct Skin {std::string id;std::string ID()const{return id;}
 std::string GetSkinPath(const std::string& file,int*)const{return file;}};
Skin skin;Skin* g_SkinInfo=&skin;int activeId=0;int GetID(){return activeId;}
struct StringUtils {static void ToLower(std::string& s){std::transform(s.begin(),s.end(),s.begin(),[](unsigned char c){return std::tolower(c);});}
 static bool EqualsNoCase(std::string a,std::string b){ToLower(a);ToLower(b);return a==b;}};
std::string route(const std::string& strFileName,bool bContainsPath=false){
 if(bContainsPath)return strFileName;
 int m_coordsRes=0;std::string strLowerPath,strPath;
'''+routing+r'''
 return strPath;
}
int main(){
 for(const std::string id:{"skin.infinity.diggz","skin.estuary","skin.cobra","skin.infinity.diggz.other"}){
  skin.id=id;
  for(activeId=0;activeId<50000;++activeId){
   bool allowed=id=="skin.infinity.diggz"&&(activeId==10123||activeId==10124||activeId==10159);
   assert(route("DialogSettings.xml")== (allowed?"InfinityPlayerSettings.xml":"DialogSettings.xml"));
   assert(route("DialogSelect.xml")=="DialogSelect.xml");
   assert(route("DialogSettings.xml",true)=="DialogSettings.xml");
  }
 }
}
'''
            source.write_text(code)
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)],check=True,capture_output=True,text=True)
            subprocess.run([str(exe)],check=True)

    def test_compiled_classifier_accepts_actual_files_rejects_every_pin_change(self):
        predecessor=native.module('corrective93_cpp_classifier_peer',c.ROOT/'repairs/2103390-bugfixes/group7/finish92/test_release92.py')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);addons=root/'addons'
            fixture=types.SimpleNamespace(root=root,before=self.classifier22,after=self.new_classifier)
            predecessor.Coherent92.compile_cpp.__func__(fixture)
            for name,body in self.after.items():
                if name.startswith(c.CC+'/'):
                    path=addons/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
            def classify(label='after',endpoint='service.py'):
                return subprocess.check_output([str(root/'cpp'/label),'special://home/addons/'+c.CC+'/'+endpoint,c.CC],
                    env=dict(os.environ,TEST_ADDONS=str(addons)),text=True)
            self.assertEqual(classify('before'),'')
            for endpoint in ('service.py','plugin.py','context.py'):
                self.assertEqual(classify(endpoint=endpoint),'command_center' if endpoint=='service.py' else 'command_center_client')
            for name in json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json']):
                path=addons/c.CC/name;body=path.read_bytes()
                try:
                    path.write_bytes(body+b'\n# changed source\n');self.assertEqual(classify(),'')
                    path.unlink();self.assertEqual(classify(),'')
                finally:path.write_bytes(body)

    def test_java_additive_route_matches_exact_payload(self):
        body,helper=dex93.java_router(self.before,self.after)
        self.assertIn(b'controllerVersion="0.3.5.23";',body)
        self.assertIn(b'controllerVersion="0.3.5.22";',body)
        for name,pin in json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json']).items():
            self.assertIn(pin.encode(),helper)
        self.assertIn(b'getCanonicalFile()',helper)
        self.assertIn(b'4 * 1024 * 1024',helper)

    def test_art_probe_separates_new_candidate_from_previous_candidate_baseline(self):
        digest='10366f343faf444493b992c49ae5cd0cee1b79545e1ad959e7bac4e93e168ec6'
        source=art93.probe_source(digest)
        self.assertIn('private static final String CANDIDATE = "'+digest+'";',source)
        self.assertIn('private static final String BASELINE = "'+dex93.BASELINE+'";',source)
        self.assertEqual(source.count(digest),1)
        self.assertEqual(source.count(dex93.BASELINE),1)
        self.assertIn('verifyReviewedController23',source)
        self.assertIn('PASSED.size() == 37',source)
        self.assertEqual(len(art93.expected(json.loads(self.after[c.UI+'/CONTROLLER-PREIMAGES.json']))),37)

    def test_option_b_first_favorite_and_stale_selection(self):
        mod=types.ModuleType('corrective93_option_b_runtime');sys.modules[mod.__name__]=mod
        exec(compile(self.after[c.UI+'/home_option_b.py'],'home_option_b','exec'),mod.__dict__)
        selected=mod.Selection(8101,0,'movies','plugin://plugin.video.umbrella/?id=1','Movie')
        mod.capture=lambda *args:selected
        calls=[]
        def rpc(method,params):
            calls.append((method,params))
            return {'favourites':None} if method=='Favourites.GetFavourites' else {}
        mod._rpc=lambda xbmc,method,params:rpc(method,params)
        self.assertTrue(mod._perform(None,None,selected,'favorite'))
        self.assertEqual([x[0] for x in calls],['Favourites.GetFavourites','Favourites.AddFavourite'])
        self.assertEqual(calls[1][1]['path'],selected.path)
        calls.clear();mod.capture=lambda *args:None
        self.assertFalse(mod._perform(None,None,selected,'favorite'));self.assertFalse(calls)

    def test_all_changed_python_xml_compile(self):
        for name in self.delta['changed_members']:
            if name.endswith('.py'):compile(self.after[name],name,'exec')
            if name.endswith('.xml'):ET.fromstring(self.after[name])

    def test_clock_measured_layout_and_actual_fold_font_width(self):
        # Kodi's auto-width label performs the live measurement. Verify its
        # worst 12-hour Latin time against the exact shipped font as a geometry
        # check, without claiming Samsung rendering/physical acceptance.
        from PIL import ImageFont
        from zipfile import ZipFile
        with ZipFile(self.apk) as z:
            font=z.read('assets/addons/'+c.SKIN+'/fonts/Roboto-Bold.ttf')
        import io
        for size,width in ((42,210),(50,1080*.26)):
            measured=ImageFont.truetype(io.BytesIO(font),size)
            maximum=max(measured.getlength('%d:%02d PM'%(h,m)) for h in range(1,13) for m in range(60))
            self.assertLess(maximum+18+8,width)
        count=0
        for name,body in self.after.items():
            if not name.endswith('/Includes_InfinityHomeUnified.xml'):continue
            count+=1;before=ET.fromstring(self.before[name]);after=ET.fromstring(body)
            a=before.find('include[@name="InfinityHomeStatusCluster"]/definition')
            b=after.find('include[@name="InfinityHomeStatusCluster"]/definition')
            group=b.find('control[@type="grouplist"]');self.assertIsNotNone(group)
            self.assertEqual(group.findtext('itemgap'),'8')
            self.assertEqual(group.findtext('align'),'right')
            clock=group.find('control[@type="label"]')
            self.assertEqual(clock.findtext('width'),'auto');self.assertEqual(clock.findtext('label'),'$INFO[System.Time]')
            self.assertEqual(clock.findtext('align'),'left')
            for n in a.findall('control[@type="label"]'):
                if n.findtext('label')!='$INFO[System.Time]':
                    self.assertIn(ET.tostring(n),[ET.tostring(x) for x in b.findall('control[@type="label"]')])
            self.assertEqual(ET.tostring(a.find('control[@type="image"]')),ET.tostring(b.find('control[@type="image"]')))
        self.assertEqual(count,10)

    def test_actual_baked_crescent_removed_only_from_new_header(self):
        from PIL import Image
        import io
        asset=c.SKIN+'/media/infinity_ui/'
        self.assertEqual(self.before[asset+'header_dark.png'],self.after[asset+'header_dark.png'])
        old=Image.open(io.BytesIO(self.before[asset+'header_dark.png'])).convert('RGBA')
        new=Image.open(io.BytesIO(self.after[asset+'header_dark_clock_safe.png'])).convert('RGBA')
        moon=Image.open(io.BytesIO(self.after[asset+'clock_moon.png'])).convert('RGBA')
        self.assertEqual(old.size,new.size);count=0
        for y in range(old.height):
            for x in range(old.width):
                if old.getpixel((x,y))!=new.getpixel((x,y)):
                    count+=1;self.assertTrue(1593<=x<=1631 and 21<=y<=59)
                    self.assertEqual(new.getpixel((x,y)),old.getpixel((1580,y)))
        self.assertEqual(count,1229)
        self.assertEqual(sum(moon.getpixel((x,y))[3]>0 for y in range(moon.height) for x in range(moon.width)),572)

if __name__=='__main__':unittest.main()
