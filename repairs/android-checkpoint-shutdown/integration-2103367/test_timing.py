"""Exercise actual bounded render/presentation observations, including delayed art."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1] / 'runtime/native/overlay'
TEST = r'''
#include "guilib/listproviders/InfinityResumeTiming.h"
#include <cassert>
#include <thread>
#include <vector>
using namespace InfinityResumeTiming;
int main() {
  assert(!ValidRequest("nsecret/path") && !ValidRequest("n") && ValidRequest("p123"));
  Observation native("plugin://script.infinity.commandcenter/?media=movie");
  assert(native.RequestUrl("plugin://script.infinity.commandcenter/?media=movie").find("infinity_trace=n") != std::string::npos);
  Observation other("plugin://provider/");assert(other.RequestUrl("plugin://provider/")=="plugin://provider/");
  Layout("p1", 123, 10000, 8830);
  { CardScope card("p1", "poster", "thumb"); Texture("icon",true,false); Rendered("p1"); }
  Presented(true); assert(cards["p1"].layoutPresented && !cards["p1"].cardPresented);
  { CardScope offscreen("p1","poster","thumb");Texture("poster",true,false); }
  { CardScope visible("p1","poster","thumb");Rendered("p1"); }
  Presented(true);assert(!cards["p1"].cardPresented); // another offscreen row cannot prove visible art
  { CardScope card("p1","poster","thumb"); Texture("poster",true,false); Rendered("p1"); }
  Presented(false); assert(!cards["p1"].cardPresented); // no frame presented
  { CardScope card("p1","poster","thumb"); Texture("poster",true,false); Rendered("p1"); }
  Presented(true);assert(cards["p1"].cardPresented && cards["p1"].revision==123);
  Layout("p2", 456, 10025, 50);
  { CardScope card("p2","poster","");Texture("poster",false,true);Rendered("p2"); }
  Presented(true);assert(!cards["p2"].cardPresented);
  { CardScope card("p2","poster","");Texture("poster",true,true);Rendered("p2"); }
  Presented(true);assert(cards["p2"].cardPresented && cards["p2"].fallback);
  std::vector<std::thread> threads;
  for (unsigned t=0;t<8;++t) threads.emplace_back([] {
    for(unsigned i=0;i<100;++i){Observation row("plugin://script.infinity.commandcenter/?media=tv");row.Mark("native_cancelled");}
  });
  for(auto& thread:threads) thread.join();
  assert(cards.size()<=128);
}
'''


def main():
    with tempfile.TemporaryDirectory(prefix='infinity-timing-') as tmp:
        folder = Path(tmp); (folder / 'utils').mkdir()
        (folder / 'utils/log.h').write_text('constexpr int LOGINFO=1; struct CLog {template<class...T> static void Log(int,const char*,T&&...) {}};\n')
        (folder / 'test.cpp').write_text(TEST)
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread', '-I', str(folder), '-I', str(ROOT / 'xbmc'),
                        str(folder / 'test.cpp'), '-o', str(folder / 'test')], check=True)
        subprocess.run([str(folder / 'test')], check=True, timeout=10)
    # The runtime overlay paths are Kodi-root-relative.
    source = (ROOT / 'xbmc/guilib/GUIBaseContainer.cpp').read_text()
    assert 'InfinityResumeTiming::Layout(' in source and 'infinityRendered && infinityOnscreen' in source
    source = (ROOT / 'xbmc/windowing/GraphicContext.cpp').read_text()
    assert source.index('PresentRender(rendered, videoLayer)') < source.index('InfinityResumeTiming::Presented(rendered)')
    print('PASS actual bounded timing: layout, visible render, matching ready/fallback art, post-presentation frame, cancellation/concurrency')


if __name__ == '__main__':
    main()
