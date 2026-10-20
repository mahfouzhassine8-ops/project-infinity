"""Actual C++ classifier + Java router over real files, with platform API doubles.

These tests are host executions, NOT an Android engine or physical Fold pass.
All inputs come from the exact signed 2103391 APK. Missing inputs are errors.
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
import release as r


class Coherent92(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=r.read_original(Path(os.environ['INFINITY_2103391_APK']))
        cls.final=r.components(cls.original)
        cls.before=(r.NATIVE_BASE/r.CONTRACT_PATH).read_bytes()
        cls.after=r.contracts(cls.before,cls.final)
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.ccroot=cls.root/'external/.kodi/addons'
        for n,raw in cls.final.items():
            if n.split('/')[0] not in (r.CC,r.UI,r.WB):continue
            p=cls.ccroot/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        cls.pins=json.loads(cls.final[r.UI+'/CONTROLLER-PREIMAGES.json'])
        cls.compile_cpp()
        cls.compile_java()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def compile_cpp(cls):
        d=cls.root/'cpp';(d/'utils').mkdir(parents=True);(d/'filesystem').mkdir()
        (d/'utils/Digest.h').write_text('#pragma once\nnamespace KODI { namespace UTILITY { struct CDigest { enum class Type { SHA256 }; }; }}\n')
        (d/'InfinityAndroidCheckpoint.h').write_text('#pragma once\n#include <string>\nnamespace InfinityAndroidCheckpoint { std::string ClassifyScript(const std::string&,const std::string&); }\n')
        (d/'filesystem/SpecialProtocol.h').write_text('''#pragma once
#include <cstdlib>
#include <string>
struct CSpecialProtocol {
 static std::string TranslatePath(const std::string& p) {
  for(const char* prefix : {"special://home/addons/", "special://xbmc/addons/"})
   if(p.rfind(prefix,0)==0) {const char* root=std::getenv("TEST_ADDONS");return root?std::string(root)+"/"+p.substr(std::string(prefix).size()):std::string();}
  return p;
 }
};
''')
        (d/'Util.h').write_text('''#pragma once
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include <openssl/sha.h>
#include "filesystem/SpecialProtocol.h"
#include "utils/Digest.h"
struct CUtil {
 static std::string GetFileDigest(const std::string& path,KODI::UTILITY::CDigest::Type) {
  std::ifstream file(CSpecialProtocol::TranslatePath(path),std::ios::binary);
  if(!file)return {};
  std::string content((std::istreambuf_iterator<char>(file)),{});
  unsigned char digest[SHA256_DIGEST_LENGTH];
  SHA256(reinterpret_cast<const unsigned char*>(content.data()),content.size(),digest);
  std::ostringstream text;for(auto value:digest)text<<std::hex<<std::setw(2)<<std::setfill('0')<<int(value);
  return text.str();
 }
};
''')
        (d/'main.cpp').write_text('''#include "InfinityAndroidCheckpoint.h"
#include <iostream>
int main(int argc,char**argv){if(argc!=3)return 2;std::cout<<InfinityAndroidCheckpoint::ClassifyScript(argv[1],argv[2]);return 0;}
''')
        for label,body in (('before',cls.before),('after',cls.after)):
            p=d/(label+'.cpp');p.write_bytes(body)
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-I',str(d),str(p),str(d/'main.cpp'),'-lcrypto','-o',str(d/label)],check=True)

    @classmethod
    def compile_java(cls):
        d=cls.root/'java';d.mkdir()
        sources={
          'android/content/Context.java':'''package android.content;
import java.io.File;
public class Context {private final File root;public Context(File f){root=f;}
 public File getExternalFilesDir(String ignored){return new File(root,"external");}
 public File getFilesDir(){return new File(root,"private");}}
''',
          'android/os/Process.java':'package android.os; public class Process {public static int myPid(){return 123;}}',
          'android/util/Log.java':'package android.util; public class Log {public static int w(String a,String b){return 0;}}',
          'org/json/JSONObject.java':'package org.json; public class JSONObject {public JSONObject put(String k,Object v){return this;}}',
          'com/projectinfinity/kodi/InfinityCheckpointEvidence.java':'package com.projectinfinity.kodi; public class InfinityCheckpointEvidence {public static void register(android.content.Context c){}}',
          'com/projectinfinity/kodi/InfinityCheckpointProtocol.java':'package com.projectinfinity.kodi; public class InfinityCheckpointProtocol {public static void atomic(java.io.File f,org.json.JSONObject j){}}',
          'com/projectinfinity/kodi/InfinityCheckpointController20Installer.java':'package com.projectinfinity.kodi; public class InfinityCheckpointController20Installer {public static int calls=0;public static boolean applyBeforeNative(android.content.Context c){calls++;return true;}}',
          'com/projectinfinity/kodi/InfinityCheckpointAddonInstaller.java':'package com.projectinfinity.kodi; public class InfinityCheckpointAddonInstaller {public static boolean applyBeforeNative(android.content.Context c){return false;}}',
          'com/projectinfinity/kodi/InfinityCheckpointCompat82Installer.java':'package com.projectinfinity.kodi; public class InfinityCheckpointCompat82Installer {public static boolean applyBeforeNative(android.content.Context c){return true;}}',
          'com/projectinfinity/kodi/Check.java':'''package com.projectinfinity.kodi;
public class Check {public static void main(String[]a){
 boolean result=InfinityInstalledCheckpointInstaller.applyBeforeNative(new android.content.Context(new java.io.File(a[0])));
 System.out.print(result+":"+InfinityCheckpointController20Installer.calls);
}}
'''}
        body=r.java_router((r.JAVA_BASE/r.JAVA_PATH).read_bytes(),cls.final)
        sources['com/projectinfinity/kodi/InfinityInstalledCheckpointInstaller.java']=body.decode().replace('@APP_PACKAGE@','com.projectinfinity.kodi')
        for n,raw in sources.items():
            p=d/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(raw)
        subprocess.run(['javac','--release','8','-Xlint:all,-options','-Werror','-d',str(d),*[str(d/n) for n in sources]],check=True)

    def cpp(self,endpoint='service.py',label='after',root='special://home/addons/',addon=r.CC,script=None):
        env=dict(os.environ,TEST_ADDONS=str(self.ccroot))
        return subprocess.check_output([str(self.root/'cpp'/label),script or root+r.CC+'/'+endpoint,addon],env=env,text=True)

    def java(self):
        return subprocess.check_output(['java','-cp',str(self.root/'java'),'com.projectinfinity.kodi.Check',str(self.root)],text=True)

    def guard(self,addon,filename,function):
        raw=self.final[addon+'/'+filename]
        parsed=ast.parse(raw)
        imports=[node for node in parsed.body if isinstance(node,(ast.Import,ast.ImportFrom)) and not isinstance(node,ast.ImportFrom)]
        definitions=[node for node in parsed.body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and (node.name==function or node.name=='UnsupportedController')]
        module=ast.Module(body=imports+definitions,type_ignores=[])
        context={'__file__':str(self.ccroot/addon/filename),'Path':Path}
        exec(compile(module,filename,'exec'),context)
        return context[function](self.ccroot/r.CC)

    def test_01_exact_component_scope_no_extra_files_or_code(self):
        self.assertEqual(set(self.final),set(self.original))
        self.assertEqual({n for n in self.final if self.final[n]!=self.original[n]},r.CHANGED_ADDON_MEMBERS)
        for n in self.final:
            if 'cobra' in n.lower() or n.startswith('script.infinity.rails/'):
                self.assertEqual(self.original[n],self.final[n])
        self.assertEqual(r.components(self.original),self.final)

    def test_02_all_versions_and_complete_dependency_hashes_agree(self):
        for addon,old,new in r.PACKAGES:
            self.assertEqual(ET.fromstring(self.final[addon+'/addon.xml']).get('version'),new)
        report=r.coherence.controller_report(self.final,self.after.decode())
        self.assertEqual(report['errors'],[])
        self.assertEqual(report['checkpoint_version'],['0.3.5.22'])
        self.assertIn(b'get("version") != "0.3.5.22"',self.final[r.WB+'/controller.py'])
        self.assertEqual(len(self.pins),13)

    def test_03_actual_compiled_native_and_java_recognize_exact_final_files(self):
        for root in ('special://home/addons/','special://xbmc/addons/'):
            for endpoint in r.coherence.ENDPOINTS:
                expected='command_center' if endpoint=='service.py' else 'command_center_client'
                self.assertEqual(self.cpp(endpoint,root=root),expected)
        self.assertEqual(self.java(),'true:0')
        self.assertEqual(self.cpp(label='before'),'')

    def test_04_all_thirteen_real_file_mutations_are_rejected_by_both_guards(self):
        for name in self.pins:
            p=self.ccroot/r.CC/name;before=p.read_bytes()
            try:
                p.write_bytes(before+b'\n# changed source\n')
                with self.subTest(name=name):
                    self.assertEqual(self.cpp(),'')
                    self.assertEqual(self.java(),'false:0')
            finally:p.write_bytes(before)

    def test_05_all_thirteen_missing_files_are_rejected(self):
        for name in self.pins:
            p=self.ccroot/r.CC/name;before=p.read_bytes()
            try:
                p.unlink()
                with self.subTest(name=name):
                    self.assertEqual(self.cpp(),'')
                    self.assertEqual(self.java(),'false:0')
            finally:p.write_bytes(before)

    def test_06_java_symlinked_source_is_rejected_without_rewriting_it(self):
        p=self.ccroot/r.CC/'common.py';raw=p.read_bytes();outside=self.root/'outside.py';outside.write_bytes(raw)
        try:
            p.unlink();p.symlink_to(outside)
            self.assertEqual(self.java(),'false:0');self.assertTrue(p.is_symlink())
            self.assertEqual(outside.read_bytes(),raw)
        finally:p.unlink();p.write_bytes(raw)

    def test_07_actual_old_21_profile_then_full_coherent_source_upgrade_without_data_writes(self):
        # Model the complete actually delivered .21 source set, not only a
        # mismatched manifest on a .22 profile. This is a host file-set replay,
        # NOT Kodi's ZIP installer or Android process lifecycle qualification.
        root=self.ccroot/r.CC
        data=self.root/'external/.kodi/userdata/addon_data'/r.CC
        data.mkdir(parents=True,exist_ok=True)
        saved=data/'continue-watching.json';saved.write_bytes(b'{"schema":2,"keep":"unchanged"}')
        def write_set(payload):
            for path,raw in payload.items():
                if path.startswith(r.CC+'/'):
                    (self.ccroot/path).write_bytes(raw)
        try:
            old21=dict(self.original)
            old21[r.CC+'/addon.xml']=r.retag(self.original[r.CC+'/addon.xml'],r.CC,'0.3.5.20','0.3.5.21')
            write_set(old21)
            self.assertEqual(self.cpp(),'');self.assertEqual(self.java(),'false:0')
            self.assertIn(b'ADDON_VERSION = "0.3.5.20"',(root/'checkpoint_runtime.py').read_bytes())
            write_set(self.final)
            self.assertEqual(self.cpp(),'command_center');self.assertEqual(self.java(),'true:0')
            self.assertEqual(saved.read_bytes(),b'{"schema":2,"keep":"unchanged"}')
        finally:write_set(self.final)

    def test_08_legacy_20_router_branch_remains_unchanged(self):
        p=self.ccroot/r.CC/'addon.xml';raw=p.read_bytes()
        try:
            p.write_bytes(self.original[r.CC+'/addon.xml'])
            self.assertEqual(self.java(),'true:1')
        finally:p.write_bytes(raw)

    def test_09_all_previous_contracts_and_classifier_logic_retained(self):
        before=r.coherence.contracts(self.before.decode());after=r.coherence.contracts(self.after.decode())
        self.assertEqual(len(after),len(before)+3)
        for v in before:self.assertIn(v,after)
        self.assertEqual(self.before[self.before.index(b'std::string ClassifyScript'):],
                         self.after[self.after.index(b'std::string ClassifyScript'):])

    def test_10_coordinator_change_is_only_explicit_supported_identity(self):
        before=r.original_coordinator();after=r.coordinator(before)
        self.assertEqual(r.sha(before),r.FINAL_COORDINATOR_PREIMAGE)
        with self.assertRaises(ValueError):
            r.coordinator((r.NATIVE_BASE/r.COORDINATOR_PATH).read_bytes())
        addition=b' && active["addon_version"].asString() != "0.3.5.22"'
        self.assertEqual(after.replace(addition,b'',1),before)
        for marker in (b'AndroidCheckpointResidentCount() != 1',b'AndroidCheckpointCompatCount() != 1',b'essential_writes_durable',b'EssentialOwner',b'SealEssentialWrites',b'EssentialWritesAuthorized',b'BeginCheckpointStartupAdmission'):
            self.assertGreater(before.count(marker),0)
            self.assertEqual(before.count(marker),after.count(marker))

    def test_11_wrong_addon_or_script_is_not_admitted(self):
        for addon in ('plugin.video.cobra','unknown',''):
            self.assertEqual(self.cpp(addon=addon),'')
        for script in ('special://home/addons/@script.infinity.commandcenter|service|123',
                       'special://home/addons/unknown/service.py'):
            self.assertEqual(self.cpp(script=script),'')

    def test_12_actual_watched_helper_verify_accepts_exact_controller(self):
        self.assertEqual(self.guard(r.WB,'controller.py','verify'),self.ccroot/r.CC)

    def test_13_watched_guard_rejects_wrong_version_and_hash(self):
        p=self.ccroot/r.CC/'addon.xml';raw=p.read_bytes()
        try:
            p.write_bytes(self.original[r.CC+'/addon.xml'])
            with self.assertRaises(RuntimeError):self.guard(r.WB,'controller.py','verify')
        finally:p.write_bytes(raw)
        p=self.ccroot/r.CC/'common.py';raw=p.read_bytes()
        try:
            p.write_bytes(raw+b'\n')
            with self.assertRaises(RuntimeError):self.guard(r.WB,'controller.py','verify')
        finally:p.write_bytes(raw)

    def test_14_reapplication_and_unknown_preimages_fail_closed(self):
        with self.assertRaises(ValueError):r.components(self.final)
        with self.assertRaises(ValueError):r.contracts(self.after,self.final)
        changed=dict(self.original);changed[r.CC+'/resume_hub.py']+=b'\n'
        with self.assertRaises(ValueError):r.components(changed)

    def test_15_existing_skin229_is_same_as_the_previously_delivered_skin(self):
        self.assertEqual(self.final[r.SKIN+'/addon.xml'],r.retag(self.original[r.SKIN+'/addon.xml'],r.SKIN,'1.0.5.228','1.0.5.229'))
        for path,raw in self.original.items():
            if path.startswith(r.SKIN+'/') and not path.endswith('/addon.xml'):
                self.assertEqual(self.final[path],raw)

    def test_16_production_close_identity_gate_preserves_single_resident_requirement(self):
        # Compile the exact production stage-1 identity/count checks from the
        # final Essential-First coordinator. JSON/platform peers are doubles;
        # this does not exercise the full Android shutdown coordinator.
        before=r.original_coordinator();after=r.coordinator(before)
        template = r'''
#include <cassert>
#include <map>
#include <string>
struct Field {
  int type=0; std::string text; int number=0;
  bool isString()const{return type==1;} std::string asString()const{return text;}
  bool isInteger()const{return type==2;} int asInteger()const{return number;}
};
struct CVariant {std::map<std::string,Field> fields;Field& operator[](const char* k){return fields[k];}};
struct State {std::string directory="test";} s;
CVariant fixture;bool jsonOk=true,identityOk=true,reached=false;int residents=1;
std::string failure;
bool ReadJson(const std::string&,CVariant& v){v=fixture;return jsonOk;}
bool SameIdentity(CVariant&,State&,bool){return identityOk;}
struct CScriptInvocationManager {
 static CScriptInvocationManager& GetInstance(){static CScriptInvocationManager m;return m;}
 int AndroidCheckpointResidentCount(){return residents;}
};
void RecordFatalFailure(const char*,const char* text){failure=text;}
void Gate(){
// PRODUCTION
reached=true;
}
void reset(const std::string& version){
 fixture.fields.clear();fixture["status"]={1,"ACTIVE",0};
 fixture["participant_api"]={2,"",1};fixture["addon_version"]={1,version,0};
 jsonOk=identityOk=true;reached=false;residents=1;failure.clear();
}
int main(){
 for(const auto& version:{"0.3.5.19","0.3.5.20","0.3.5.21","0.3.5.22","unreviewed"}){
  reset(version);Gate();
  bool accepted=std::string(version)=="0.3.5.19"||std::string(version)=="0.3.5.20"||
   (AFTER && std::string(version)=="0.3.5.22");
  assert(reached==accepted && failure.empty());
 }
 for(int count:{0,2,3}){
  reset(AFTER?"0.3.5.22":"0.3.5.20");residents=count;Gate();
  assert(!reached && failure=="exactly_one_canonical_resident_required");
 }
 for(int mode=0;mode<8;++mode){
  reset(AFTER?"0.3.5.22":"0.3.5.20");
  if(mode==0)jsonOk=false;
  if(mode==1)identityOk=false;
  if(mode==2)fixture["status"]={1,"STOPPED",0};
  if(mode==3)fixture["status"]={2,"",1};
  if(mode==4)fixture["participant_api"]={2,"",2};
  if(mode==5)fixture["participant_api"]={1,"1",0};
  if(mode==6)fixture["addon_version"]={2,"",22};
  if(mode==7)fixture.fields.erase("addon_version");
  Gate();assert(!reached && failure.empty());
 }
}
'''
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for label,source in (("before",before),("after",after)):
                start=source.index(b'      CVariant active;')
                stop=source.index(b'      Operation("compat");',start)
                body=source[start:stop].decode()
                code=template.replace('// PRODUCTION',body).replace('AFTER','true' if label=='after' else 'false')
                cpp=root/(label+'.cpp');cpp.write_text(code)
                subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(root/label)],check=True)
                subprocess.run([str(root/label)],check=True)

if __name__=='__main__':unittest.main(verbosity=2)
