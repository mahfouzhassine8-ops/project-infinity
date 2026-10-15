#!/usr/bin/env python3
"""Compile *production-extracted* callback and matcher with controlled Kodi peers.
Never call a mock unit test a physical Fold/GUI-lock test.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import patch_native

CPP_HEAD = r'''
#include <cassert>
#include <mutex>
#include <string>
#include <vector>
#include <iostream>
using CCriticalSection = std::mutex;
constexpr int OK = 0, DONE = 1;
constexpr int LOGDEBUG = 1;
struct CLog {
  template<class... A> static void Log(int,const char*,A...) {}
};
struct CJob {
  virtual ~CJob() = default;
  enum PRIORITY {PRIORITY_LOW, PRIORITY_NORMAL};
};
struct CDirectoryJob : CJob {
  std::string url, target;
  std::vector<int> items, types;
  mutable int bound = 0;
  CDirectoryJob(std::string u, std::vector<int> i)
      : url(std::move(u)), target("videos"), items(std::move(i)), types{4} {}
  const std::string& GetUrl() const { return url; }
  const std::vector<int>& GetItems() const { return items; }
  const std::string& GetTarget() const { return target; }
  void GetItemTypes(std::vector<int>& out) const { out = types; }
  void MarkBound() const { ++bound; }
};
struct CDirectoryProvider {
  CCriticalSection m_section;
  unsigned int m_jobID{0};
  int m_updateState{OK};
  std::vector<int> m_items, m_itemTypes;
  std::string m_currentUrl, m_currentTarget;
  void OnJobComplete(unsigned int jobID, bool success, CJob* job);
};
'''
CPP_CASES = r'''
int main() {
  const std::string movie="plugin://script.infinity.rails/?section=movies&revision=2";
  const std::string tv="plugin://script.infinity.rails/?section=tvshows";
  const std::string normal="plugin://plugin.video.pov/?action=movies";
  assert(InfinityIsAddonRailRequest(movie));
  assert(InfinityIsAddonRailRequest(tv));
  assert(InfinityIsAddonRailRequest("plugin://script.infinity.rails/?section=movies"));
  assert(!InfinityIsAddonRailRequest("plugin://script.infinity.rails/?section=moviesHidden"));
  assert(!InfinityIsAddonRailRequest("plugin://script.infinity.rails/?section=tvshows_"));
  assert(!InfinityIsAddonRailRequest("plugin://script.infinity.rails/"));
  assert(!InfinityIsAddonRailRequest(normal));
  assert(!InfinityIsAddonRailRequest("plugin://other.script/?section=movies"));

  CDirectoryProvider provider;
  provider.m_currentUrl=movie;
  provider.m_jobID=42;
  provider.m_items={99};
  CDirectoryJob tvOld(tv,{11});
  provider.OnJobComplete(41,true,&tvOld);  // old section / ID
  assert((provider.m_items == std::vector<int>{99}));
  assert(provider.m_jobID==42 && tvOld.bound==0);
  CDirectoryJob wrongUrl(tv,{100});
  provider.OnJobComplete(42,true,&wrongUrl); // same ID but wrong URL
  assert((provider.m_items == std::vector<int>{99}));
  assert(provider.m_jobID==42 && wrongUrl.bound==0);
  CDirectoryJob current(movie,{10,20,30});
  provider.OnJobComplete(42,true,&current);
  assert((provider.m_items == std::vector<int>{10,20,30}));
  assert(provider.m_jobID==0 && provider.m_updateState==DONE);
  assert(current.bound==1);
  provider.m_jobID=55;
  provider.m_updateState=OK;
  CDirectoryJob failed(movie,{});
  provider.OnJobComplete(55,false,&failed);
  assert(provider.m_jobID==0 && failed.bound==0);
  assert((provider.m_items == std::vector<int>{10,20,30}));

  // Reset while an old rail job is still finishing cannot repopulate the rail.
  provider.m_currentUrl="";
  provider.m_jobID=0;
  CDirectoryJob late(movie,{7});
  provider.OnJobComplete(54,true,&late);
  assert(provider.m_items.size()==3 && late.bound==0);

  // No behavior change for unrelated standard Kodi directories.
  CDirectoryProvider ordinary;
  ordinary.m_currentUrl=normal;
  ordinary.m_jobID=65;
  CDirectoryJob unrelated(normal,{3});
  ordinary.OnJobComplete(64,true,&unrelated);
  assert(ordinary.m_jobID==0 && unrelated.bound==1);
  assert((ordinary.m_items == std::vector<int>{3}));
  std::cout << "PASS extracted native: 8 URL identities, stale ID/URL/Reset, success/failure, unrelated legacy callback\\n";
}
'''

def verify(source: Path, out: Path):
    source = Path(source)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = (source / patch_native.SOURCE).read_text()
    assert text.count("InfinityIsAddonRailRequest") == 4
    assert text.count(patch_native.PRIORITY_AFTER) == 1
    assert text.count(patch_native.STALE_AFTER) == 1
    assert 'this, priority);' in text
    assert "threading._shutdown()" not in text
    helper_start = text.index("static bool InfinityIsAddonRailRequest(")
    helper_end = text.index("\n}\n",helper_start)+3
    helper = text[helper_start:helper_end]
    callback_start=text.index("void CDirectoryProvider::OnJobComplete(")
    callback_end=text.index("\n}\n",callback_start)+3
    callback=text[callback_start:callback_end]
    with tempfile.TemporaryDirectory() as name:
        cpp=Path(name)/"test.cpp"
        binary=Path(name)/"verify"
        cpp.write_text(CPP_HEAD+helper+"\n"+callback+"\n"+CPP_CASES)
        subprocess.run(["g++","-std=c++17","-O1","-Wall","-Wextra","-Werror",
                        str(cpp),"-o",str(binary)],check=True)
        output=subprocess.check_output([str(binary)],text=True)
    result={"status":"passed","actual_native_callback_compiled":True,
            "targeted_rails_identity_cases":8,
            "stale_request_and_section_completion_rejected":True,
            "unchanged_non_rail_callback_tested":True,
            "production_priority_branch_verified":True,
            "android_touch_injected":False,"physical_fold_verified":False}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out.parent/"RAILS-HANDOFF-HOST.txt").write_text(output)
    print(output.strip(),flush=True)

def host(root: Path, out: Path):
    with tempfile.TemporaryDirectory() as name:
        target=Path(name)/patch_native.SOURCE
        target.parent.mkdir(parents=True,exist_ok=True)
        parent=Path(root)/"repairs/android-checkpoint-shutdown/runtime/native/overlay"/patch_native.SOURCE
        shutil.copyfile(parent,target)
        patch_native.apply(Path(name))
        verify(Path(name),out)

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.source: verify(args.source,args.out)
    else: host(args.root,args.out)
