"""Check the exact diagnostic delta without running Kodi or touching a profile."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
HEADER = "xbmc/interfaces/generic/InfinityStartupTrace.h"
INVOKER = "xbmc/interfaces/python/PythonInvoker.cpp"

HOST = r"""
#include "xbmc/interfaces/generic/InfinityStartupTrace.h"

#include <cassert>
#include <future>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace Trace = InfinityStartupTrace;
using Trace::Stage;

struct ThreadState { void* interp; };
ThreadState interpreter{};
bool m_invokerOwnsGil = true;
struct Addon {
  const std::string& ID() const { return id; }
  std::string id{"script.infinity.commandcenter"};
};
Addon addon;
Addon* m_addon = &addon;
int GetId() { return 40; }

enum class Wait { InCreate, InLedger, None };
Wait waitAt{Wait::None};
bool returnNull{false};
int releases{0};
std::promise<void> entered;
std::promise<void> resume;
std::future<void> resumeSignal;
void WaitAt(Wait location)
{
  if (waitAt == location)
  {
    entered.set_value();
    resumeSignal.wait();
  }
}

ThreadState* Py_NewInterpreter()
{
  WaitAt(Wait::InCreate);
  return returnNull ? nullptr : &interpreter;
}
void PyEval_ReleaseThread(ThreadState* state)
{
  assert(state == &interpreter);
  ++releases;
}
namespace InfinityScriptPersistence {
void InitializationProgress(int id, const std::string& stage, uint64_t identity)
{
  assert(id == 40);
  if (stage == "native.interpreter.created")
    WaitAt(Wait::InLedger);
  else
    assert(stage == "native.interpreter.create" && identity == 0);
}
}

ThreadState* RunBoundary()
{
  ThreadState* l_threadState = nullptr;
  m_invokerOwnsGil = true;
BODY
  return l_threadState; // NULL cleanup remains in the unmodified production code.
}

std::vector<Trace::Event> Drain()
{
  std::vector<Trace::Event> events;
  Trace::Drain([&](const Trace::Event& event) { events.push_back(event); });
  return events;
}

void CheckWait(Wait wait, Stage lastBeforeRelease)
{
  waitAt = wait;
  entered = std::promise<void>{};
  resume = std::promise<void>{};
  resumeSignal = resume.get_future();
  auto enteredSignal = entered.get_future();
  auto worker = std::async(std::launch::async, RunBoundary);
  assert(enteredSignal.wait_for(std::chrono::seconds(3)) == std::future_status::ready);
  auto events = Drain();
  assert(events.size() == (wait == Wait::InCreate ? 1 : 2));
  assert(events.front().stage == Stage::InterpreterCreate);
  assert(std::string(events.front().addonId) == addon.id);
  assert(events.back().stage == lastBeforeRelease);
  assert(events.back().invoker == 40 && events.back().tid == events.front().tid);
  if (wait == Wait::InLedger)
    assert(events.back().value == 1);
  resume.set_value();
  assert(worker.get() == &interpreter && !m_invokerOwnsGil);
  events = Drain();
  assert(events.size() == (wait == Wait::InCreate ? 2 : 1));
  assert(events.back().stage == Stage::InterpreterCreated);
}

int main()
{
  // Exercise the original process gate before enabling the host fixture.
  Trace::Record(Stage::InterpreterReturned, 41, 1);
  assert(Drain().empty());
  Trace::hostInfinity = true;
  CheckWait(Wait::InCreate, Stage::InterpreterCreate);
  CheckWait(Wait::InLedger, Stage::InterpreterReturned);
  assert(releases == 2);
  assert(std::string(Trace::Name(Stage::InterpreterReturned)) == "interpreter.returned");

  waitAt = Wait::None;
  returnNull = true;
  assert(RunBoundary() == nullptr);
  auto events = Drain();
  assert(events.size() == 2);
  assert(events.back().stage == Stage::InterpreterReturned && events.back().value == 0);
  assert(releases == 2);

  errno = EBUSY;
  Trace::Record(Stage::InterpreterCreate, 41, 0, 0, 0, "plugin://test/?key=private");
  Trace::Record(Stage::InterpreterCreate, 42, 0, 0, 0, std::string(128, 'a').c_str());
  Trace::Record(Stage::InterpreterCreate, 43);
  assert(errno == EBUSY);
  events = Drain();
  assert(events.size() == 3);
  for (const auto& event : events)
    assert(event.addonId[0] == '\0');

  const unsigned prior = Trace::next.load();
  for (unsigned i = prior; i < Trace::CAPACITY + 1; ++i)
    Trace::Record(Stage::InterpreterReturned, 41, 1);
  assert(Trace::CAPACITY == 8192 && Trace::dropped.load() == 1);
}
"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(native_root, scope_file, patch_file, fixture, after=None):
    scope = json.loads((HERE / scope_file).read_bytes())
    allowlist = scope["source_allowlist"]
    with tempfile.TemporaryDirectory(prefix="infinity514-boundary-") as tmp:
        work = Path(tmp)
        for name, hashes in allowlist.items():
            original = native_root / name
            assert sha(original) == hashes["before_sha256"], name
            target = work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)

        patch = HERE / patch_file
        stats = subprocess.check_output(["git", "apply", "--numstat", patch], cwd=work, text=True)
        assert {line.split("\t")[-1] for line in stats.splitlines()} == set(allowlist)
        subprocess.run(["git", "apply", "--check", patch], cwd=work, check=True)
        subprocess.run(["git", "apply", patch], cwd=work, check=True)
        for name, hashes in allowlist.items():
            assert sha(work / name) == hashes["after_sha256"], name

        invoker = (work / INVOKER).read_text()
        anchor = '#if defined(TARGET_ANDROID)\n      InfinityScriptPersistence::InitializationProgress(GetId(), "native.interpreter.create", 0);'
        start = invoker.index(anchor)
        end = invoker.index("      if (l_threadState == nullptr)", start)
        source = work / "host.cpp"
        source.write_text(fixture.replace("BODY", invoker[start:end]))
        executable = work / "startup-boundary"
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pthread",
             "-D", "INFINITY_STARTUP_TRACE_HOST", "-D", "TARGET_ANDROID",
             "-I", work, source, "-o", executable],
            check=True,
        )
        subprocess.run([executable], timeout=10, check=True)
        if after is not None:
            after(native_root, work)
        print("PASS Exact native preimages, call-site ordering and bounded trace behavior")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify_startup_boundary.py <authenticated native source root>")
    check(Path(sys.argv[1]), "SCOPE.json", "startup-boundary.patch", HOST)
