"""Check the amended startup overlay and keep the original ABI fixture separate."""
from pathlib import Path
import re
import subprocess
import sys

from verify_startup_boundary import HOST, check

observation = r"""
struct Observation : Trace::Event { std::string addonId; };
std::vector<Observation> Drain()
{
  std::vector<Observation> events;
  Trace::Drain([&](const Trace::Event& event, const char* addonId)
  {
    events.push_back({event, addonId});
  });
  return events;
}
"""

tail = r"""
  Trace::Record(Stage::StoppingBeforeBytecode, 41);
  unsigned cancelled = 0;
  Trace::Drain([&](const Trace::Event& event)
  {
    if (event.stage == Stage::StoppingBeforeBytecode)
      ++cancelled;
  });
  assert(cancelled == 1);

  const unsigned prior = Trace::next.load();
  for (unsigned i = prior; i < Trace::CAPACITY + 1; ++i)
    Trace::Record(Stage::InterpreterReturned, 41, 1);
  assert(Trace::CAPACITY == 8192 && Trace::dropped.load() == 1);
  events = Drain();
  assert(events.back().stage == Stage::Overflow && events.back().value == 1 &&
         events.back().addonId.empty());
"""

def test_fixture():
    start = HOST.index("std::vector<Trace::Event> Drain()")
    end = HOST.index("\nvoid CheckWait", start)
    base = HOST[:start] + observation.strip() + "\n" + HOST[end:]
    base = base.replace(
        'Trace::Record(Stage::InterpreterCreate, 41, 0, 0, 0, "plugin://test/?key=private")',
        'Trace::RecordInterpreterCreate(41, "plugin://test/?key=private")')
    base = base.replace(
        "Trace::Record(Stage::InterpreterCreate, 42, 0, 0, 0, std::string(128, 'a').c_str())",
        "Trace::RecordInterpreterCreate(42, std::string(128, 'a').c_str())")
    base = base.replace(r"assert(event.addonId[0] == '\0');", "assert(event.addonId.empty());")
    return base[:base.index("  const unsigned prior = Trace::next.load();")] + tail + "}\n"


def check_exports(baseline, work):
    probe = work / "exports.cpp"
    fixture = r'''
#include "xbmc/interfaces/generic/InfinityStartupTrace.h"
namespace Trace = InfinityStartupTrace;
extern "C" const char* startup_probe(Trace::Stage stage)
{
  Trace::Record(stage);
#ifdef CANDIDATE
  Trace::RecordInterpreterCreate(42, "script.infinity.commandcenter");
#endif
  return Trace::Name(stage);
}
'''
    probe.write_text(fixture)

    def symbols(source, extra):
        lib = work / "check.so"
        subprocess.run(
            ["g++", "-std=c++17", "-shared", "-fPIC", "-fno-gnu-unique", "-O0",
             "-DTARGET_ANDROID", *extra, "-I", source, probe, "-o", lib],
            check=True,
        )
        rows = subprocess.check_output(["readelf", "--dyn-syms", "--wide", lib], text=True)
        return {row[7]: (row[3], row[4], int(row[2], 0) if row[3] == "OBJECT" else None)
                for line in rows.splitlines() if len(row := line.split()) >= 8 and
                row[4] in ("WEAK", "GLOBAL") and row[6] != "UND" and
                re.search("InfinityStartupTrace", row[7])}

    original = symbols(baseline, [])
    candidate = symbols(work, ["-DCANDIDATE"])
    assert any("6Record" in name for name in original), original
    assert candidate == original, (candidate.keys() - original.keys(),
                                   original.keys() - candidate.keys(),
                                   {n for n in original.keys() & candidate.keys()
                                    if original[n] != candidate[n]})

if __name__ == "__main__":
    check(Path(sys.argv[1]), "STARTUP-ABI-SCOPE.json", "startup-boundary-abi.patch", test_fixture(), check_exports)
