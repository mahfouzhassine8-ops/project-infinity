#!/usr/bin/env python3
"""Compile the production callback; reproduce the Fold cycle with OS mutexes.

Controlled GUI-item peers deliberately acquire the graphics mutex at final
release, as the real GUI layout/texture cleanup can do. This is a causal host
regression test, not an Android or physical Fold acceptance result.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import native_patch

ROOT = Path(__file__).resolve().parents[2]
HEAD = r'''
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <iostream>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
using CCriticalSection = std::timed_mutex;
std::mutex graphics;
std::mutex signalMutex;
std::condition_variable signal;
bool retiring=false;
struct CGUIStaticItem {
  int id; bool hasLayout;
  CGUIStaticItem(int i,bool layout=false):id(i),hasLayout(layout){}
  ~CGUIStaticItem() {
    if(!hasLayout)return;
    {std::lock_guard<std::mutex> lock(signalMutex);retiring=true;}
    signal.notify_all();
    std::lock_guard<std::mutex> lock(graphics);
  }
};
using CGUIStaticItemPtr = std::shared_ptr<CGUIStaticItem>;
constexpr int OK=0,DONE=2,INVALIDATED=3,LOGDEBUG=0;
struct CLog {template<class... A> static void Log(int,const char*,A...) {}};
struct CJob {virtual ~CJob()=default;};
struct CDirectoryJob:CJob {
  std::string url,target="videos";
  std::vector<CGUIStaticItemPtr> items;
  std::vector<int> types{4};
  mutable int bound=0;
  bool failCopy=false;
  CDirectoryJob(std::string u,int id):url(std::move(u)) {
    items.push_back(std::make_shared<CGUIStaticItem>(id));
  }
  const std::string& GetUrl() const {return url;}
  const std::string& GetTarget() const {return target;}
  const std::vector<CGUIStaticItemPtr>& GetItems() const {
    if(failCopy)throw std::bad_alloc();
    return items;
  }
  void GetItemTypes(std::vector<int>& out)const {out=types;}
  void MarkBound()const {++bound;}
};
struct CDirectoryProvider {
  CCriticalSection m_section;
  unsigned int m_jobID=42;
  int m_updateState=OK;
  std::vector<CGUIStaticItemPtr> m_items;
  std::vector<int> m_itemTypes;
  std::string m_currentUrl,m_currentTarget;
  void OnJobComplete(unsigned int,bool,CJob*);
};
'''
CASES = r'''
int main(int argc,char**) {
  const bool expectCycle=argc>1;
  const std::string movie="plugin://script.infinity.rails/?section=movies&revision=2";
  const std::string tv="plugin://script.infinity.rails/?section=tvshows";
  const std::string ordinary="plugin://plugin.video.pov/?action=movies";
  CDirectoryProvider p;
  p.m_currentUrl=movie;
  p.m_items.push_back(std::make_shared<CGUIStaticItem>(99,true));
  CDirectoryJob fresh(movie,7);
  // GUI owns graphics while the completion worker releases a bound GUI item.
  std::unique_lock<std::mutex> guiGraphics(graphics);
  std::thread worker([&]{p.OnJobComplete(42,true,&fresh);});
  {std::unique_lock<std::mutex> lock(signalMutex);
   assert(signal.wait_for(lock,std::chrono::seconds(3),[]{return retiring;}));}
  // The baseline still holds directory here. The corrected callback releases
  // directory before retiring layouts, allowing the GUI to bind new items.
  const bool guiCanProceed=p.m_section.try_lock_for(std::chrono::milliseconds(250));
  if(guiCanProceed) {
    assert(p.m_items.size()==1 && p.m_items[0]->id==7);
    p.m_section.unlock();
  }
  assert(guiCanProceed != expectCycle);
  guiGraphics.unlock();
  worker.join();
  assert(p.m_jobID==0 && p.m_updateState==DONE && fresh.bound==1);
  if(expectCycle){std::cout<<"PASS baseline reproduces reciprocal lock dependency\n";return 0;}

  // Preserve the original stale rail ID/URL gates and successful publication.
  p.m_jobID=55;p.m_updateState=OK;
  CDirectoryJob wrongId(movie,20),wrongUrl(tv,21),current(movie,22);
  p.OnJobComplete(54,true,&wrongId);
  p.OnJobComplete(55,true,&wrongUrl);
  assert(p.m_items[0]->id==7 && p.m_jobID==55);
  assert(wrongId.bound==0 && wrongUrl.bound==0);
  p.OnJobComplete(55,true,&current);
  assert(p.m_items[0]->id==22 && p.m_jobID==0 && current.bound==1);
  // Failed completions retain the existing list and do not mark it bound.
  p.m_jobID=56;p.m_updateState=OK;
  CDirectoryJob failed(movie,23);
  p.OnJobComplete(56,false,&failed);
  assert(p.m_items[0]->id==22 && p.m_jobID==0 && failed.bound==0);
  // Reset/late rail callback cannot repopulate a departed section.
  p.m_currentUrl="";p.m_jobID=0;
  p.OnJobComplete(55,true,&current);
  assert(p.m_items[0]->id==22 && current.bound==1);
  // Existing non-rail callback semantics remain intact.
  p.m_currentUrl=ordinary;p.m_jobID=60;p.m_updateState=INVALIDATED;
  CDirectoryJob other(ordinary,30);
  p.OnJobComplete(59,true,&other);
  assert(p.m_items[0]->id==30 && other.bound==1 && p.m_updateState==INVALIDATED);
  assert(p.m_itemTypes==std::vector<int>{4} && p.m_currentTarget=="videos");
  // A failed incoming copy leaves the old items intact and releases the guard.
  CDirectoryJob throwing(ordinary,31);throwing.failCopy=true;
  try {p.OnJobComplete(60,true,&throwing);assert(false);}
  catch(const std::bad_alloc&){}
  assert(p.m_items[0]->id==30 && p.m_section.try_lock());
  p.m_section.unlock();
  // Empty successful results retire the old list after directory unlock too.
  CDirectoryJob empty(ordinary,32);empty.items.clear();
  p.OnJobComplete(61,true,&empty);
  assert(p.m_items.empty() && empty.bound==1);
  std::cout<<"PASS corrected callback: GUI proceeds during graphics cleanup; stale/failure/reset/ordinary/exception/empty semantics retained\n";
}
'''


def extract(text):
    start = text.index("static bool InfinityIsAddonRailRequest(")
    end = text.index("\n}\n", start) + 3
    return text[start:end] + "\n" + native_patch.callback(text)[2]


def verify(before, after, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    with tempfile.TemporaryDirectory() as temp:
        for name, text, args in (("baseline", before, ["expect-cycle"]),
                                 ("candidate", after, [])):
            cpp = Path(temp) / (name + ".cpp")
            binary = cpp.with_suffix("")
            cpp.write_text(HEAD + extract(text) + CASES)
            subprocess.run(["g++", "-std=c++17", "-O1", "-pthread", "-Wall", "-Wextra",
                            "-Werror", str(cpp), "-o", str(binary)], check=True)
            result = subprocess.run([str(binary)] + args, text=True, capture_output=True,
                                    timeout=10, check=True)
            results[name] = result.stdout.strip()
    results.update(status="passed", production_callback_compiled=True,
                   real_os_mutexes=True, baseline_cycle_reproduced=True,
                   candidate_directory_unlocked_during_graphics_cleanup=True,
                   preserved_semantics=["stale_id", "stale_url", "failed_job", "reset",
                                        "non_rail", "invalidated_state", "copy_exception", "empty_result"],
                   android_runtime=False, physical_fold_verified=False)
    (out / "LOCK-RETIREMENT-HOST.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


def fixture():
    text = (ROOT / "repairs/android-checkpoint-shutdown/runtime/native/overlay" /
            native_patch.SOURCE).read_text()
    spec = importlib.util.spec_from_file_location("rails_delta", ROOT / "repairs/rails-handoff-2103377/patch_native.py")
    rails = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rails)
    text = text.replace("using namespace PVR;\n", "using namespace PVR;\n" + rails.HELPER)
    text = text.replace(rails.STALE_BEFORE, rails.STALE_AFTER)
    with tempfile.TemporaryDirectory() as temp:
        file = Path(temp) / native_patch.SOURCE
        file.parent.mkdir(parents=True)
        file.write_text(text)
        native_patch.apply(temp)
        return text, file.read_text()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path)
    parser.add_argument("--after", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    before, after = (args.before.read_text(), args.after.read_text()) if args.before else fixture()
    verify(before, after, args.out)
