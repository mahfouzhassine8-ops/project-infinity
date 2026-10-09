#!/usr/bin/env python3
"""Compile actual native source classifier; digest adapter uses hashes of real runtime files."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--command-center", type=Path, required=True)
    parser.add_argument("--embedded", type=Path, required=True)
    parser.add_argument("--compat-script", default="service.py")
    args = parser.parse_args()
    files = {f"script.infinity.commandcenter/{p.name}": p for p in args.command_center.glob("*.py")}
    files["script.infinity.commandcenter/addon.xml"] = args.command_center / "addon.xml"
    for p in args.embedded.rglob("*"):
        if p.is_file() and p.suffix in (".py", ".xml"):
            files[p.relative_to(args.embedded).as_posix()] = p
    with tempfile.TemporaryDirectory(prefix="script-contract-host-") as name:
        root = Path(name)
        for rel in ["platform/android/activity/InfinityScriptCheckpointContracts.cpp",
                    "platform/android/activity/InfinityAndroidCheckpoint.h"]:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.runtime / "xbmc" / rel, target)
        headers = {
            "utils/Digest.h": '#pragma once\nnamespace KODI {namespace UTILITY {class CDigest {public: enum class Type{SHA256};};}}\n',
            "Util.h": '''#pragma once
#include "utils/Digest.h"
#include <map>
#include <string>
namespace Test {inline std::map<std::string,std::string> digests;}
class CUtil {public:static std::string GetFileDigest(const std::string& path,KODI::UTILITY::CDigest::Type){return Test::digests[path];}};
''',
            "filesystem/SpecialProtocol.h": '''#pragma once
#include <string>
class CSpecialProtocol {public:static std::string TranslatePath(const std::string& path){
 for(const auto& p:{std::pair<std::string,std::string>{"special://home/addons/","/home-addons/"},{"special://xbmc/addons/","/system-addons/"}})
  if(path.rfind(p.first,0)==0)return p.second+path.substr(p.first.size());
 return path;
}};
''',
        }
        for rel, content in headers.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        # Exact reviewed phone observer and its inherited lifecycle repair.
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'e2e-mobile-2103303'))
        from ambient_lifecycle import repair
        ambient = Path(__file__).with_name('fixtures') / 'infinity_native_ambient.py'
        ambient_current = root / 'ambient-current.py'
        ambient_current.write_text(repair(ambient.read_text()))
        assert hashlib.sha256(ambient.read_bytes()).hexdigest() == '3e33144282d81aa727466f530fd3d37deaee8357c5973c0c7b932bbcc3db1f5f'
        assert hashlib.sha256(ambient_current.read_bytes()).hexdigest() == 'de30a5114302a303638c589342024b348d3070c5aa76ba4a360d2506dd4402f7'
        files['skin.infinity.diggz/resources/lib/infinity_native_ambient.py'] = ambient_current
        mapping = root / "digests"
        mapping.write_text("".join(f"{alias}{rel} {hashlib.sha256(path.read_bytes()).hexdigest()}\n"
                                   for rel, path in files.items()
                                   for alias in ["special://home/addons/", "special://xbmc/addons/"]))
        (root / "harness.cpp").write_text(r'''
#include "platform/android/activity/InfinityScriptCheckpointContracts.cpp"
#include <cassert>
#include <fstream>
#include <iostream>
using InfinityAndroidCheckpoint::ClassifyScript;
int main(int argc,char** argv){
 assert(argc==2);std::ifstream map(argv[1]);std::string file,hash;while(map>>file>>hash)Test::digests[file]=hash;
 for(const char*root:{"special://home/addons/","special://xbmc/addons/"}){
  const std::string base=root;
  assert(ClassifyScript(base+"script.infinity.commandcenter/service.py","script.infinity.commandcenter")=="command_center");
  assert(ClassifyScript(base+"script.infinity.commandcenter/plugin.py","script.infinity.commandcenter")=="command_center_client");
  assert(ClassifyScript(base+"script.infinity.commandcenter/default.py","script.infinity.commandcenter").empty());
  assert(ClassifyScript(base+"service.infinity.compat/service.py","service.infinity.compat")=="compat");
  assert(ClassifyScript(base+"service.infinity.compat/layout_service.py","service.infinity.compat")=="nonpersistent:layout-properties");
  assert(ClassifyScript(base+"service.infinity.compat/theme_contract.py","service.infinity.compat")=="reconstructible-cache:theme-revision");
  assert(ClassifyScript(base+"service.infinity.refresh/service.py","service.infinity.refresh")=="reconstructible-cache:refresh-policy");
  assert(ClassifyScript(base+"script.infinity.audiopolicy/default.py","script.infinity.audiopolicy").empty());
 }
 assert(ClassifyScript("/arbitrary/service.infinity.compat/service.py","service.infinity.compat").empty());
 assert(ClassifyScript("special://home/addons/service.infinity.compat/service.py","wrong.addon").empty());
 const std::string dependency="special://home/addons/service.infinity.compat/checkpoint_runtime.py";
 Test::digests[dependency]="changed";
 assert(ClassifyScript("special://home/addons/service.infinity.compat/service.py","service.infinity.compat").empty());
 // The no-addon Home RunScript requires exact full path, source and APK library.
 const std::string ambient="special://home/addons/skin.infinity.diggz/resources/lib/infinity_native_ambient.py";
 const std::string native="/trusted-libs/libinfinityambient.so";
 const auto ambientHash=Test::digests[ambient];
 assert(ClassifyScript(ambient,"").empty()); // Native library location not registered.
 setenv("KODI_ANDROID_LIBS","/trusted-libs",1);
 assert(ClassifyScript(ambient,"").empty()); // Library missing.
 Test::digests[native]="a876a76abe4faea63046953579899b0b7a67572722c2ed92331e41fcd1475684";
 assert(ClassifyScript(ambient,"")=="nonpersistent:ambient-glass");
 assert(ClassifyScript(ambient,"skin.infinity.diggz")=="nonpersistent:ambient-glass");
 assert(ClassifyScript(ambient,"wrong.addon").empty());
 assert(ClassifyScript("/untrusted/infinity_native_ambient.py","").empty());
 Test::digests[ambient]="3e33144282d81aa727466f530fd3d37deaee8357c5973c0c7b932bbcc3db1f5f";
 assert(ClassifyScript(ambient,"")=="nonpersistent:ambient-glass");
 Test::digests[ambient]="changed";assert(ClassifyScript(ambient,"").empty());
 Test::digests[ambient]=ambientHash;
 Test::digests[native]="changed";assert(ClassifyScript(ambient,"").empty());
 Test::digests.erase(native);assert(ClassifyScript(ambient,"").empty());
 unsetenv("KODI_ANDROID_LIBS");
 // A different unmodified trusted root remains independently verifiable.
 assert(ClassifyScript("special://xbmc/addons/service.infinity.compat/service.py","service.infinity.compat")=="compat");
 Test::digests.erase("special://home/addons/script.infinity.commandcenter/resume_hub.py");
 assert(ClassifyScript("special://home/addons/script.infinity.commandcenter/service.py","script.infinity.commandcenter").empty());
 assert(ClassifyScript("special://home/addons/script.infinity.commandcenter/plugin.py","script.infinity.commandcenter").empty());
 std::cout<<"PASS: actual source classifier, both roots, dependency mismatch, missing source, arbitrary path/addon, unknown writer\n";
}
'''.replace('service.infinity.compat/service.py', 'service.infinity.compat/'+args.compat_script))
        binary = root / "test"
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", str(root),
                        str(root / "harness.cpp"), "-o", str(binary)], check=True)
        subprocess.run([str(binary), str(mapping)], check=True, timeout=10)


if __name__ == "__main__":
    main()
