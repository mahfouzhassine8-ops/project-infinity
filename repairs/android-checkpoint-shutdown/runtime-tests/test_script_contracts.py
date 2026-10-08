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
    args = parser.parse_args()
    files = {f"script.infinity.commandcenter/{p.name}": p for p in args.command_center.glob("*.py")}
    files["script.infinity.commandcenter/addon.xml"] = args.command_center / "addon.xml"
    for p in args.embedded.rglob("*.py"):
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
 // A different unmodified trusted root remains independently verifiable.
 assert(ClassifyScript("special://xbmc/addons/service.infinity.compat/service.py","service.infinity.compat")=="compat");
 Test::digests.erase("special://home/addons/script.infinity.commandcenter/resume_hub.py");
 assert(ClassifyScript("special://home/addons/script.infinity.commandcenter/service.py","script.infinity.commandcenter").empty());
 assert(ClassifyScript("special://home/addons/script.infinity.commandcenter/plugin.py","script.infinity.commandcenter").empty());
 std::cout<<"PASS: actual source classifier, both roots, dependency mismatch, missing source, arbitrary path/addon, unknown writer\n";
}
''')
        binary = root / "test"
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", str(root),
                        str(root / "harness.cpp"), "-o", str(binary)], check=True)
        subprocess.run([str(binary), str(mapping)], check=True, timeout=10)


if __name__ == "__main__":
    main()
