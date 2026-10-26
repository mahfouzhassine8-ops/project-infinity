"""Compile actual narrow native gate expressions and audit whole source inventory."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

import stage_native_modules as integration

ROOT=Path(__file__).parent


def block(source,start):
    """Find balanced C++ scope/condition without treating quoted braces as code."""
    masked=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'',
                  lambda m:' '*len(m[0]),source)
    open_at=next(i for i in range(start,len(masked)) if masked[i] in '({')
    opening=masked[open_at];closing=')' if opening=='(' else '}'
    depth=1
    for i in range(open_at+1,len(masked)):
        if masked[i]==opening:depth+=1
        elif masked[i]==closing:
            depth-=1
            if depth==0:return source[start:i+1]
    raise ValueError('Unbalanced native source')


class NativeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=Path(os.environ.get('FINAL_NATIVE_SOURCE_ROOT',ROOT.parents[2]/'baseline-2103407/reconstructed407-native'))
        cls.map=Path(os.environ.get('FINAL_NATIVE_SOURCE_MAP',ROOT.parents[2]/'baseline-2103407/reconstructed407-evidence/SIGNED407-NATIVE-SOURCE-MAP.json'))
        cls.workspace=tempfile.TemporaryDirectory();cls.work=Path(cls.workspace.name)
        cls.candidate=cls.work/'native';shutil.copytree(cls.native,cls.candidate,symlinks=True)
        cls.receipt=integration.stage(cls.candidate,cls.map,cls.work/'evidence')

    @classmethod
    def tearDownClass(cls):cls.workspace.cleanup()

    def compile_driver(self,name,source):
        cpp=self.work/(name+'.cpp');exe=self.work/name;cpp.write_text(source)
        subprocess.run(['g++','-std=c++14','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)

    def test_full9407_existing_sources_only_seven_owned_files_differ(self):
        before=json.loads(self.map.read_text())
        after={p.relative_to(self.candidate).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
               for p in self.candidate.rglob('*') if p.is_file()}
        self.assertEqual(set(n for n in before if before[n]!=after[n]),
                         set(integration.OWNED))
        self.assertEqual(len(set(after)-set(before)),4)
        self.assertEqual(self.receipt['unchanged_existing_sources'],9400)
        for path in ('xbmc/guilib/GUIBaseContainer.h','xbmc/input/InputManager.cpp'):
            self.assertEqual((self.native/path).read_bytes(),(self.candidate/path).read_bytes())

    def test_tampered_source_and_unknown_member_fail_before_native_stage(self):
        raw=(self.native/integration.TITLE).read_bytes()
        with self.assertRaises(ValueError):integration.patch(integration.TITLE,raw+b'\n')
        with self.assertRaises(ValueError):integration.patch('xbmc/video/VideoPlayer.cpp',raw)
        altered=dict(json.loads(self.map.read_text()));altered['xbmc/input/InputManager.cpp']='0'*64
        wrong=self.work/'wrong-map.json';wrong.write_text(json.dumps(altered))
        with self.assertRaises(ValueError):integration.stage(self.native,wrong,self.work/'must-not-exist')
        self.assertFalse((self.work/'must-not-exist').exists())

    def test_touch_mapping_selection_actions_and_favourites_remain_byte_exact(self):
        before=(self.native/integration.TITLE).read_text();after=(self.candidate/integration.TITLE).read_text()
        for name in ('OnInfinityOptionBLongPress','OnInfinityFavouritesLongPress','OnInfinityRailLongPress',
                     'PrepareInfinityBrowseLongPress','OnInfinityMediaTouch','OnInfinityUiTouch',
                     'OnInfinityAddonBrowserTouch','OnInfinityUiContextMenu'):
            needle='bool CGUIBaseContainer::'+name+'('
            self.assertTrue(needle in before,'Missing actual selected native method: '+name)
            # Include both the parameter list and complete function body.
            start=before.index(needle);body_start=before.index('{',start)
            current=after.index(needle);current_body=after.index('{',current)
            self.assertEqual(block(before,body_start),block(after,current_body),name)
        for name in integration.OWNED:
            actual=(self.candidate/name).read_text()
            for old,new in reversed(integration.edits(name)):actual=actual.replace(new,old,1)
            self.assertEqual(actual,(self.native/name).read_text())

    def test_legacy_contracts_and_all_checkpoint_operations_are_preserved(self):
        before=(self.native/integration.CONTRACTS).read_text();after=(self.candidate/integration.CONTRACTS).read_text()
        a=before[before.index('struct Contract'):before.index('std::string ClassifyScript')]
        b=after[after.index('struct Contract'):after.index('std::string ClassifyScript')]
        self.assertEqual(a,b)
        self.assertIn('if (!moduleOwner.empty()) return moduleOwner;',after)
        original=(self.native/integration.CHECKPOINT).read_text();candidate=(self.candidate/integration.CHECKPOINT).read_text()
        old,new=integration.edits(integration.CHECKPOINT)[1]
        self.assertEqual(candidate[candidate.index('if (s.stage == 2)'):],original[original.index('if (s.stage == 2)'):])
        self.assertEqual(candidate.count(new),1)
        self.assertIn('!SameIdentity(active, s, false)',candidate)
        self.assertIn('AndroidCheckpointResidentCount() != 1',candidate)

    def test_actual_title_gate_requires_exact_infinity_ownership_and_authenticated_capability(self):
        source=(self.candidate/integration.TITLE).read_text()
        start=source.index('static bool InfinityTitleOwnerReady()');opening=source.index('{',start)
        function=source[start:opening]+block(source,opening)
        self.compile_driver('title-gate',r'''#include <cassert>
#include <memory>
#include <string>
std::string skin="skin.infinity.diggz", version="0.3.5.40";
bool enabled=true,verified=false;int verifiedCalls=0;
struct Version { std::string asString() const { return version; } };
namespace ADDON { enum class OnlyEnabled { CHOICE_YES }; struct Addon {
  ::Version Version()const{return {};}
  std::string ID()const{return "script.infinity.commandcenter";}
  std::string Path()const{return "/native-resolved/addons/script.infinity.commandcenter/";}
}; using AddonPtr=std::shared_ptr<Addon>; }
struct Settings {std::string GetString(const std::string&)const{return skin;} };
struct Component {Settings*GetSettings(){static Settings s;return &s;} };
struct Manager {bool GetAddon(const std::string&id,ADDON::AddonPtr&a,ADDON::OnlyEnabled){
  assert(id=="script.infinity.commandcenter");a=std::make_shared<ADDON::Addon>();return enabled;}};
struct CServiceBroker {static Component*GetSettingsComponent(){static Component s;return &s;}
static Manager&GetAddonMgr(){static Manager m;return m;}};
struct CSpecialProtocol {static std::string TranslatePath(const std::string&p){return p;}};
namespace InfinityInstalledModules {bool CapabilityReady(const std::string&id,const std::string&root,const std::string&cap){
 ++verifiedCalls;assert(id=="script.infinity.commandcenter");
 assert(root=="/native-resolved/addons/script.infinity.commandcenter/");assert(cap=="title-actions-v1");return verified;}}
'''+function+r'''
int main(){
 assert(!InfinityTitleOwnerReady());verified=true;assert(InfinityTitleOwnerReady());
 verifiedCalls=0;skin="skin.cobra";assert(!InfinityTitleOwnerReady());assert(verifiedCalls==0);
 skin="skin.infinity.diggz";enabled=false;assert(!InfinityTitleOwnerReady());assert(verifiedCalls==0);
 enabled=true;verified=false;version="0.3.5.35";assert(InfinityTitleOwnerReady());assert(verifiedCalls==0);
 version="0.3.5.39";assert(!InfinityTitleOwnerReady());
}
''')

    def test_actual_participant_predicate_retains_identity_api_and_signature_requirements(self):
        source=(self.candidate/integration.CHECKPOINT).read_text()
        marker='if (!ReadJson(s.directory + "/active.json", active)'
        condition=block(source,source.index(marker)+3)[1:-1]
        self.compile_driver('participant-gate',r'''#include <cassert>
#include <map>
#include <string>
struct Field {std::string value;bool integer=false;bool isInteger()const{return integer;}
 bool isString()const{return !integer;}int asInteger()const{return std::stoi(value);}std::string asString()const{return value;}};
std::map<std::string,Field> fields;
struct CVariant {Field operator[](const std::string&key)const{return fields[key];}};
struct State {std::string directory;};State s;
bool same=true,readable=true,authenticated=false;int verifyCalls=0;
bool ReadJson(const std::string&,CVariant&){return readable;}
bool SameIdentity(const CVariant&,const State&,bool){return same;}
namespace InfinityInstalledModules {bool Participant(const std::string&v,unsigned int api,const std::string&hash){
 ++verifyCalls;return authenticated && v=="0.3.5.40" && api==1 && hash==std::string(64,'a');}}
bool Rejected(){CVariant active;return '''+condition+r''';}
int main(){fields["status"]={"ACTIVE",false};fields["participant_api"]={"1",true};
 fields["addon_version"]={"0.3.5.40",false};fields["module_manifest_sha256"]={std::string(64,'a'),false};
 assert(Rejected());authenticated=true;assert(!Rejected());
 verifyCalls=0;same=false;assert(Rejected());assert(verifyCalls==0);same=true;
 fields["participant_api"]={"2",true};assert(Rejected());assert(verifyCalls==0);
 fields["participant_api"]={"1",true};fields["module_manifest_sha256"]={std::string(64,'b'),false};assert(Rejected());
 fields["module_manifest_sha256"]={std::string(64,'a'),false};fields["addon_version"]={"0.3.5.41",false};assert(Rejected());
 fields["addon_version"]={"0.3.5.35",false};authenticated=false;assert(!Rejected());
}
''')


if __name__=='__main__':unittest.main(verbosity=2)
