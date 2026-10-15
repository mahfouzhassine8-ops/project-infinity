#!/usr/bin/env python3
"""Compile the actual Skin.cpp resolver against a deterministic host boundary.

Tests geometry ownership, not Android rendering, provider cancellation or ANRs.
The complete ARM64 workflow separately compiles real Kodi headers and callers.
"""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from native_patch import FILES, LOCKED_PREIMAGES, digest, once, transform


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolver(text):
    start = text.index('std::string CSkinInfo::GetSkinPath(')
    end = text.index('\nbool CSkinInfo::HasSkinFile(', start)
    return text[start:end]


STUB = r'''
#include <algorithm>
#include <cassert>
#include <iostream>
#include <set>
#include <string>
#include <vector>
struct RESOLUTION_INFO { int iWidth=1920, iHeight=1080; std::string strMode="1080i"; };
struct Context { RESOLUTION_INFO GetResInfo() { return {}; } };
struct System { Context& GetGfxContext() { static Context c; return c; } };
struct CServiceBroker { static System* GetWinSystem() { static System s; return &s; } };
struct closestRes { explicit closestRes(const RESOLUTION_INFO&) {} bool operator()(const RESOLUTION_INFO&, const RESOLUTION_INFO&) { return false; } };
struct URIUtils {
  static std::string AddFileToFolder(const std::string& a,const std::string& b) {return a+"/"+b;}
  static std::string AddFileToFolder(const std::string& a,const std::string& b,const std::string& c) {return a+"/"+b+"/"+c;}
};
std::set<std::string> existing;
struct CFileUtils { static bool Exists(const std::string& s) { return existing.count(s); } };
constexpr int LOGWARNING=1, LOGERROR=2;
struct CLog { template<class... T> static void Log(int, const char*,T...) {} };
struct CSkinInfo {
  std::vector<RESOLUTION_INFO> m_resolutions{{1920,1080,"1080i"}};
  RESOLUTION_INFO m_defaultRes{1280,720,"720p"};
  bool responsive=false, adaptive=true;
  std::string Path() const { return "active"; }
  bool UsesNativeResponsiveLayout() const { return responsive; }
  bool UsesNativeWindowAdaptation() const { return adaptive; }
  std::string GetNativeResponsiveClass() const { return "tall"; }
  RESOLUTION_INFO GetNativeResponsiveResolution() const { return {1080,2400,"responsive/tall"}; }
  RESOLUTION_INFO GetNativeWindowResolution(const RESOLUTION_INFO&) const { return {968,2144,"1080i"}; }
  std::string GetSkinPath(const std::string&,RESOLUTION_INFO* =nullptr,const std::string& ="", bool=true) const;
};
'''

CHECKS = r'''
int main() {
  CSkinInfo skin;
  RESOLUTION_INFO r;
  existing={"active/1080i/Home.xml","provider/1080i/source_results.xml"};
  assert(skin.GetSkinPath("Home.xml",&r)=="active/1080i/Home.xml");
  assert(r.iWidth==968 && r.iHeight==2144); // active Home still adapts
  assert(skin.GetSkinPath("source_results.xml",&r,"provider",false)=="provider/1080i/source_results.xml");
  assert(r.iWidth==1920 && r.iHeight==1080); // actual declared folder
  existing.clear();
  assert(skin.GetSkinPath("source_progress.xml",&r,"provider",false)=="provider/720p/source_progress.xml");
  assert(r.iWidth==1280 && r.iHeight==720); // declared default, not failed active lookup
  skin.responsive=true;
  existing={"active/responsive/tall/Home.xml","provider/1080i/source_results.xml"};
  assert(skin.GetSkinPath("Home.xml",&r)=="active/responsive/tall/Home.xml");
  assert(r.iWidth==1080 && r.iHeight==2400); // marker-based Home remains responsive
  assert(skin.GetSkinPath("source_results.xml",&r,"provider",false)=="provider/1080i/source_results.xml");
  assert(r.iWidth==1920 && r.iHeight==1080); // no responsive/base leakage
  skin.responsive=false; skin.adaptive=false;
  existing={"active/1080i/Home.xml"};
  assert(skin.GetSkinPath("Home.xml",&r)=="active/1080i/Home.xml");
  assert(r.iWidth==1920 && r.iHeight==1080); // remote/TV legacy boundary
  assert(!skin.GetSkinPath("Home.xml",nullptr).empty());
  skin.m_resolutions.clear();
  assert(skin.GetSkinPath("source_results.xml",&r,"provider",false).empty());
  std::cout << "PASS: 8 compiled resolver ownership cases\n";
}
'''


class PatchContracts(unittest.TestCase):
    def test_locked_apk_source_proof_matches_reconstructed_preimage(self):
        for name,h in LOCKED_PREIMAGES.items():
            self.assertEqual(digest(PARENT[name].encode()),h,name)

    def test_actual_cpp_resolver(self):
        with tempfile.TemporaryDirectory(prefix='infinity-provider-resolver-') as temp:
            root = Path(temp)
            source = root/'resolver.cpp'
            source.write_text(STUB + resolver(CANDIDATE[FILES[1]]) + CHECKS)
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(source),'-o',str(root/'resolver')],check=True)
            subprocess.run([str(root/'resolver')],check=True)

    def test_preimage_failure_is_explicit(self):
        for name, text in PARENT.items():
            with self.subTest(path=name), self.assertRaises(ValueError):
                transform(name, text.replace('GetSkinPath', 'UnexpectedResolver'))

    def test_not_silently_applied_twice(self):
        for name, text in CANDIDATE.items():
            with self.subTest(path=name), self.assertRaises(ValueError):
                transform(name, text)

    def test_all_fallback_lookups_opt_out(self):
        xml = CANDIDATE[FILES[2]]
        self.assertEqual(xml.count('skinInfo->GetSkinPath(xmlFilename, &res, "", false)'), 2)
        self.assertEqual(xml.count('g_SkinInfo->GetSkinPath(xmlFilename, &res, basePath, false)'),1)
        self.assertIn('g_SkinInfo->GetSkinPath(xmlFilename, &res);', xml)
        self.assertEqual(xml.count('std::make_shared<ADDON::CSkinInfo>(addonInfo, declaredRes)'),2)

    def test_provider_callbacks_and_cancel_policy_unchanged(self):
        old, new = PARENT[FILES[2]], CANDIDATE[FILES[2]]
        for a,b in [('    bool WindowXML::OnMessage(', '    void WindowXML::AllocResources('),
                    ('    void WindowXML::AllocResources(', '    bool WindowXML::OnClick('),
                    ('    WindowXMLDialog::WindowXMLDialog(', '\n  }\n')]:
            self.assertEqual(old[old.index(a):old.index(b,old.index(a))],
                             new[new.index(a):new.index(b,new.index(a))])
        callback='invokeCallback(new CallbackFunction<WindowXML,AddonClass::Ref<Action> >(this,&WindowXML::onAction,inf.get()));'
        self.assertEqual(new.count(callback),old.count(callback))
        self.assertNotIn('ACTION_SELECT_ITEM',new[new.index('Infinity provider Back queued:'):new.index('Infinity provider Back queued:')+300])

    def test_diagnostics_do_not_claim_callback_completion(self):
        xml=CANDIDATE[FILES[2]]
        self.assertIn('Infinity provider Back queued:',xml)
        self.assertNotIn('Back completed',xml)
        for token in ('Infinity.ProviderOwned','Infinity.ProviderLogicalWidth','Infinity.ProviderLogicalHeight'):
            self.assertIn(token,xml)


def main():
    global PARENT, CANDIDATE
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,type=Path,help='exact unmodified 3304 native preimage (same native as 3305)')
    p.add_argument('--bootstrap-lineage',type=Path,help='host-only pinned upstream audit: native_layout.py and inplace_reflow.py')
    args=p.parse_args()
    PARENT={n:(args.source/n).read_text() for n in FILES}
    if args.bootstrap_lineage:
        native=load(args.bootstrap_lineage/'native_layout.py')
        retained=load(args.bootstrap_lineage/'inplace_reflow.py')
        for n, fn in [(FILES[0],'patch_skin_h'),(FILES[1],'patch_skin_cpp')]:
            PARENT[n]=getattr(retained,fn)(getattr(native,fn)(PARENT[n]))
        # The 3303 evidence-only heartbeat adds these two exact Skin.cpp edits.
        # The locked 3305 source hash below proves this bootstrap is complete.
        PARENT[FILES[1]]=once(once(PARENT[FILES[1]],'#include "Skin.h"',
            '#include "Skin.h"\n#if defined(TARGET_ANDROID)\n'
            '#include "platform/android/activity/InfinityResponsiveness.h"\n#endif'),
            'void CSkinInfo::Start()\n{',
            'void CSkinInfo::Start()\n{\n#if defined(TARGET_ANDROID)\n'
            '  ++InfinityHealth::skinGeneration;\n#endif')
    CANDIDATE={n:transform(n,s) for n,s in PARENT.items()}
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PatchContracts)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__=='__main__':main()
