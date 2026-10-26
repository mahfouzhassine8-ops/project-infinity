"""Compile exact adapter boundaries and a clearly isolated test-key positive fixture."""
from pathlib import Path
import subprocess
import unittest

import test_module_manifest as manifest_fixture

CC, ROOT = manifest_fixture.CC, manifest_fixture.ROOT


class InstalledModuleTests(unittest.TestCase):
    setUp = manifest_fixture.ModuleManifestTests.setUp
    write_manifest = manifest_fixture.ModuleManifestTests.write_manifest
    sign = manifest_fixture.ModuleManifestTests.sign

    @classmethod
    def setUpClass(cls):
        manifest_fixture.ModuleManifestTests.setUpClass.__func__(cls)
        stubs = cls.work / 'stubs/filesystem'
        stubs.mkdir(parents=True)
        (stubs / 'SpecialProtocol.h').write_text('''#pragma once
#include <string>
class CSpecialProtocol { public: static std::string TranslatePath(const std::string& path); };
''')
        driver = cls.work / 'adapter-driver.cpp'
        driver.write_text(r'''#include "InfinityInstalledModules.h"
#include "filesystem/SpecialProtocol.h"
#include <fstream>
#include <iostream>
#include <string>
std::string root;
int rootCalls=0;
std::string CSpecialProtocol::TranslatePath(const std::string& path) {
  ++rootCalls;
  return path=="special://home/addons/" ? root+"/" : root+"/missing-builtins/";
}
int main(int argc,char**argv) {
  if (argc!=3) return 2;
  root=argv[1]; const std::string mode=argv[2];
  const std::string cc="script.infinity.commandcenter";
  const auto source=root+"/"+cc+"/service.py";
  if (mode=="cobra-negative") {
    const auto owner=InfinityInstalledModules::Classify(root+"/script.infinity.cobra/service.py","script.infinity.cobra");
    const bool capability=InfinityInstalledModules::CapabilityReady("script.infinity.cobra",root+"/script.infinity.cobra","title-actions-v1");
    std::cout<<owner.size()<<" "<<capability<<" "<<rootCalls<<"\n"; return 0;
  }
  if (mode=="unknown-protocol") {
    std::cout<<InfinityInstalledModules::Participant("0.3.5.40",2,std::string(64,'a'))<<" "<<rootCalls<<"\n"; return 0;
  }
  char version[49]{}, hash[65]{}; unsigned int api=0;
  const int identity=InfinityCommandCenterIdentityV1((root+"/"+cc).c_str(),version,sizeof(version),hash,sizeof(hash),&api);
  if (mode=="identity") {
    std::cout<<identity<<" "<<version<<" "<<api<<" "<<hash<<"\n"; return 0;
  }
  if (mode=="bad-root") {
    const int bad=InfinityCommandCenterIdentityV1((root+"/outside").c_str(),version,sizeof(version),hash,sizeof(hash),&api);
    const int small=InfinityCommandCenterIdentityV1((root+"/"+cc).c_str(),version,8,hash,sizeof(hash),&api);
    std::cout<<bad<<" "<<small<<"\n"; return 0;
  }
  if (mode=="owner-and-participant") {
    const auto service=InfinityInstalledModules::Classify(source,cc);
    const auto client=InfinityInstalledModules::Classify(root+"/"+cc+"/plugin.py",cc);
    const auto wrong=InfinityInstalledModules::Classify(source,"script.infinity.uirepair");
    const bool participant=InfinityInstalledModules::Participant(version,api,hash);
    const bool wrongVersion=InfinityInstalledModules::Participant("0.3.5.999",api,hash);
    const bool wrongHash=InfinityInstalledModules::Participant(version,api,std::string(64,'0'));
    std::cout<<service<<" "<<client<<" "<<wrong.size()<<" "<<participant<<" "<<wrongVersion<<" "<<wrongHash<<"\n"; return 0;
  }
  if (mode=="capabilities") {
    const bool ccReady=InfinityInstalledModules::CapabilityReady(cc,root+"/"+cc,"title-actions-v1");
    const bool unlistedUi=InfinityInstalledModules::CapabilityReady("script.infinity.uirepair",root+"/script.infinity.uirepair","dialog-reflow-v1");
    const bool unknown=InfinityInstalledModules::CapabilityReady(cc,root+"/"+cc,"unknown-v2");
    std::cout<<ccReady<<" "<<unlistedUi<<" "<<unknown<<"\n"; return 0;
  }
  if (mode=="source-changed-after-cache") {
    std::ofstream code(root+"/"+cc+"/common.py",std::ios::app); code<<"changed\n"; code.close();
    const auto owner=InfinityInstalledModules::Classify(source,cc);
    std::cout<<owner.size()<<" "<<InfinityInstalledModules::CapabilityReady(cc,root+"/"+cc,"title-actions-v1")<<"\n"; return 0;
  }
  return 2;
}
''')
        production = (ROOT / 'isolated-native/InfinityInstalledModules.cpp').read_text()
        actual_key = (ROOT / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem').read_text()
        test_key = (cls.work / 'trusted-test.public.pem').read_text()
        assert production.count(actual_key) == 1
        isolated = production.replace(actual_key, test_key, 1)
        assert isolated.replace(test_key, actual_key, 1) == production
        fixture = cls.work / 'test-key-adapter.cpp'
        fixture.write_text(isolated)
        cls.production_driver = cls.work / 'production-adapter'
        cls.fixture_driver = cls.work / 'test-key-adapter'
        for source, output in ((ROOT / 'isolated-native/InfinityInstalledModules.cpp', cls.production_driver),
                               (fixture, cls.fixture_driver)):
            subprocess.run(['g++', '-std=c++14', '-Wall', '-Wextra', '-Werror',
                            '-I', str(ROOT / 'isolated-native'), '-I', str(stubs.parent),
                            str(driver), str(source), str(ROOT / 'isolated-native/InfinityModuleManifest.cpp'),
                            '-lcrypto', '-pthread', '-o', str(output)], check=True)

    @classmethod
    def tearDownClass(cls):
        manifest_fixture.ModuleManifestTests.tearDownClass.__func__(cls)

    def invoke(self, mode, production=False):
        result = subprocess.run([str(self.production_driver if production else self.fixture_driver),
                                 str(self.root), mode], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_actual_production_key_rejects_test_signed_bundle(self):
        self.assertEqual(self.invoke('identity', production=True).split()[0], '0')
        self.assertEqual(self.invoke('identity').split()[:3], ['1', '0.3.5.40', '1'])

    def test_exact_production_cobra_and_unknown_protocol_paths_have_no_root_access(self):
        self.assertEqual(self.invoke('cobra-negative', production=True), '0 0 0')
        self.assertEqual(self.invoke('unknown-protocol', production=True), '0 0')

    def test_fixture_owner_identity_and_protocol_are_jointly_required(self):
        self.assertEqual(self.invoke('owner-and-participant'), 'command_center command_center_client 0 1 0 0')
        self.write_manifest(version='0.3.5.41')
        self.assertEqual(self.invoke('identity').split()[:3], ['1', '0.3.5.41', '1'])
        self.assertEqual(self.invoke('owner-and-participant'), 'command_center command_center_client 0 1 0 0')

    def test_unlisted_compatibility_addon_does_not_inherit_capability(self):
        self.assertEqual(self.invoke('capabilities'), '1 0 0')

    def test_changed_source_cannot_reuse_prior_verified_cache_for_admission(self):
        self.assertEqual(self.invoke('source-changed-after-cache'), '0 0')

    def test_caller_root_and_output_buffer_bounds_fail_closed(self):
        self.assertEqual(self.invoke('bad-root'), '0 0')


if __name__ == '__main__':
    unittest.main(verbosity=2)
