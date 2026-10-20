"""Real released-byte regression tests plus compiled host C++ classification.

Not an Android, real-filesystem, physical Fold, service-ownership or crash pass.
Required APK fixtures are errors when absent, never silently skipped.
"""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
import release_coherence as c

SIGNED_SHA='47609f2ada1d6bbc7cdbddb791d11815bdbf1100a083bd8205d60ac21c882151'
BASE='83df773b742dc3f7e576a90157a04c15bc61fdb3'

class ReleaseCoherenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apk=Path(os.environ['INFINITY_2103391_APK'])
        if c.digest(cls.apk.read_bytes()) != SIGNED_SHA:
            raise AssertionError('Wrong original permanently signed APK')
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temp.name)
        with zipfile.ZipFile(cls.apk) as z:
            cls.payload={n[len('assets/addons/'):]:z.read(n) for n in z.namelist()
                         if n.startswith('assets/addons/') and not n.endswith('/')
                         and n[len('assets/addons/'):].split('/')[0] in (c.CC,)+c.CONSUMERS}
            cls.native=z.read('lib/arm64-v8a/libkodi.so')
        cls.before=subprocess.check_output(['git','show',BASE+':'+c.NATIVE_PATH],cwd=c.ROOT,text=True)
        cls.after=c.append_reviewed_group1_contracts(cls.before,cls.payload)
        cls.hashes={p:c.digest(data) for p,data in cls.payload.items()}
        (cls.root/'utils').mkdir();(cls.root/'filesystem').mkdir()
        (cls.root/'utils/Digest.h').write_text('#pragma once\nnamespace KODI { namespace UTILITY { struct CDigest { enum class Type { SHA256 }; }; }}\n')
        (cls.root/'InfinityAndroidCheckpoint.h').write_text('#pragma once\n#include <string>\nnamespace InfinityAndroidCheckpoint { std::string ClassifyScript(const std::string&, const std::string&); }\n')
        (cls.root/'Util.h').write_text('#pragma once\n#include <map>\n#include <string>\n#include "utils/Digest.h"\nextern std::map<std::string,std::string> hashes;\nstruct CUtil { static std::string GetFileDigest(const std::string& p, KODI::UTILITY::CDigest::Type) { auto i=hashes.find(p); return i==hashes.end()?std::string():i->second; } };\n')
        (cls.root/'filesystem/SpecialProtocol.h').write_text('#pragma once\n#include <string>\nstruct CSpecialProtocol { static std::string TranslatePath(const std::string& p) { return p; } };\n')
        (cls.root/'main.cpp').write_text('#include <map>\n#include <string>\n#include <fstream>\n#include <iostream>\n#include "InfinityAndroidCheckpoint.h"\nstd::map<std::string,std::string> hashes;\nint main(int argc,char** argv) { if(argc!=4) return 2; std::ifstream f(argv[3]); if(!f) return 3; std::string p,h; while(f>>h>>p) hashes[p]=h; std::cout<<InfinityAndroidCheckpoint::ClassifyScript(argv[1],argv[2]); return 0; }\n')
        for label,source in [('old',cls.before),('new',cls.after)]:
            cpp=cls.root/(label+'.cpp');cpp.write_text(source)
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-I',str(cls.root),str(cpp),str(cls.root/'main.cpp'),'-o',str(cls.root/label)],check=True)

    @classmethod
    def tearDownClass(cls):
        del cls.native
        cls.temp.cleanup()

    def classify(self,label,hashes,endpoint='service.py',addon=c.CC,root='special://home/addons/',script=None):
        fixture=self.root/'hashes.txt'
        fixture.write_text(''.join(v+' '+root+k+'\n' for k,v in sorted(hashes.items())))
        actual=script if script is not None else root+c.CC+'/'+endpoint
        return subprocess.check_output([str(self.root/label),actual,addon,str(fixture)],text=True)

    def test_01_old_native_classifier_rejects_actual_group1_bytes(self):
        for endpoint in c.ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.classify('old',self.hashes,endpoint),'')
        for pin in c.OLD.values():self.assertIn(pin.encode(),self.native)

    def test_02_corrected_compiled_classifier_accepts_reviewed_full_contract_both_roots(self):
        for root in ('special://home/addons/','special://xbmc/addons/'):
            for endpoint in c.ENDPOINTS:
                owner='command_center' if endpoint=='service.py' else 'command_center_client'
                self.assertEqual(self.classify('new',self.hashes,endpoint,root=root),owner)

    def test_03_all_thirteen_one_file_mutations_and_missing_files_fail_closed(self):
        variant=c.matching_variants(self.after,c.CC,c.CC+'/service.py',self.hashes)[0]
        self.assertEqual(len(variant['pins']),13)
        for path in variant['pins']:
            for mode in ('mutate','missing'):
                with self.subTest(path=path,mode=mode):
                    hashes=dict(self.hashes)
                    if mode=='mutate':hashes[path]='0'*64
                    else:del hashes[path]
                    self.assertEqual(self.classify('new',hashes),'')

    def test_04_every_prior_legacy_contract_and_unrelated_contract_is_retained(self):
        old=c.contracts(self.before);new=c.contracts(self.after)
        self.assertEqual(len(new),len(old)+3)
        for variant in old:
            self.assertIn(variant,new)
            script=variant['script'];root='special://home/addons/'
            hashes=dict(variant['pins'])
            for label in ('old','new'):
                self.assertEqual(self.classify(label,hashes,addon=variant['addon'],script=root+script),variant['owner'])

    def test_05_wrong_identity_cobra_and_escaped_duplicate_are_not_newly_admitted(self):
        for addon in ('plugin.video.cobra','unreviewed.addon',''):
            self.assertEqual(self.classify('new',self.hashes,addon=addon),'')
        for script in ('special://home/addons/@script.infinity.commandcenter|service|ae33445389842165','special://home/addons/unreviewed/service.py'):
            self.assertEqual(self.classify('new',self.hashes,script=script),'')

    def test_06_exact_retagged_command_center_reproduces_all_identity_failures(self):
        from export_matched_addons import new_manifest
        changed=dict(self.payload)
        changed[c.CC+'/addon.xml']=new_manifest(changed[c.CC+'/addon.xml'],c.CC,'0.3.5.20','0.3.5.21')
        report=c.controller_report(changed,self.after)
        self.assertFalse(report['coherent'])
        self.assertIn('checkpoint ADDON_VERSION differs from actual manifest',report['errors'])
        self.assertEqual(sum('controller preimage mismatch' in error for error in report['errors']),2)
        self.assertEqual(self.classify('new',{p:c.digest(data) for p,data in changed.items()}),'')

    def test_07_exact_embedded_consumer_preimages_pass_after_source_contract_correction(self):
        report=c.controller_report(self.payload,self.after)
        self.assertEqual(report['errors'],[])
        self.assertFalse(report['physical_fold_verified'])

    def test_08_corrected_source_does_not_certify_old_native_binary(self):
        report=c.controller_report(self.payload,self.after,self.native)
        self.assertFalse(report['coherent'])
        self.assertTrue(any('shipped binary' in error for error in report['errors']))

    def test_09_contract_generator_refuses_unreviewed_bytes_or_repeat_patch(self):
        changed=dict(self.payload);changed[c.CC+'/common.py']+=b'\n'
        with self.assertRaises(c.CoherenceError):c.append_reviewed_group1_contracts(self.before,changed)
        with self.assertRaises(c.CoherenceError):c.append_reviewed_group1_contracts(self.after,self.payload)

    def test_10_export_retag_refused_before_creating_output(self):
        import export_matched_addons as exporter
        receipt=Path(os.environ['INFINITY_2103391_RECEIPT'])
        target=self.root/'must-not-exist'
        with self.assertRaises(c.CoherenceError):exporter.export(self.apk,receipt,target)
        self.assertFalse(target.exists())

    def test_11_contract_alternatives_are_or_not_and(self):
        self.assertFalse(c.matching_variants(self.before,c.CC,c.CC+'/service.py',self.hashes))
        matching=c.matching_variants(self.after,c.CC,c.CC+'/service.py',self.hashes)
        self.assertEqual(len(matching),1)
        self.assertGreater(len([v for v in c.contracts(self.after) if v['script']==c.CC+'/service.py']),1)

    def test_12_original_signed_apk_is_still_byte_identical(self):
        self.assertEqual(c.digest(self.apk.read_bytes()),SIGNED_SHA)

if __name__=='__main__':unittest.main(verbosity=2)
