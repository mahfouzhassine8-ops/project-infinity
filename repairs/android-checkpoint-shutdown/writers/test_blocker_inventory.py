#!/usr/bin/env python3
"""Compile the native script-persistence blocker ledger against controlled writers."""
from pathlib import Path
import argparse
import subprocess
import tempfile

HARNESS = r'''
#include "platform/android/activity/InfinityScriptPersistence.h"
#include <cassert>
#include <iostream>
using namespace InfinityScriptPersistence;

int main() {
  Admit(1,"bad.one:service.py");
  Observed(1);
  Fail(1,"first_failure","path=/tmp/one.db");
  Fail(1,"first_failure","path=/tmp/one.db");
  Retired(1);

  auto first=Snapshot();
  assert(first.active==0);
  assert(first.retired==0);
  assert(first.failedSettled==1);
  assert(first.blockers.size()==1);
  assert(first.blockers[0].writer=="bad.one:service.py");
  assert(first.blockers[0].reason=="first_failure");
  assert(first.blockers[0].count==2);
  assert(!DurableRetirement("bad.one:service.py"));

  Admit(2,"good:service.py");
  Observed(2);
  Retired(2);
  assert(DurableRetirement("good:service.py"));

  Admit(3,"bad.two:service.py");
  Observed(3);
  Fail(3,"second_failure","path=/tmp/two.json");
  Retired(3);

  auto all=Snapshot();
  assert(all.active==0);
  assert(all.retired==1);
  assert(all.failedSettled==2);
  assert(all.blockers.size()==2);
  assert(all.failure=="python_writer:first_failure");
  assert(all.failureWriterId==1);
  assert(all.failureWriter=="bad.one:service.py");
  assert(all.failureDetail=="path=/tmp/one.db");
  assert(DurableRetirement("good:service.py"));
  assert(BlockedRetirement("bad.one:service.py"));
  assert(BlockedRetirement("bad.two:service.py"));
  assert(!BlockedRetirement("good:service.py"));

  assert(PollInventory());
  auto synced=Snapshot();
  assert(synced.syncStarted && synced.syncFinished);
  assert(!synced.durable);
  assert(!PollCommit());

  // A post-seal writer is still fail-closed and is added to the same bounded inventory.
  Admit(4,"late:service.py");
  auto late=Snapshot();
  assert(late.blockers.size()==3);
  assert(late.blockers[2].reason=="script_writer_admission_after_seal_or_limit");
  assert(!PollCommit());

  std::cout<<"PASS: blocker inventory retains every writer failure without granting unsafe retirement\n";
}
'''

ADVISORY_HARNESS = r'''
#include "platform/android/activity/InfinityScriptPersistence.h"
#include <cassert>
#include <chrono>
#include <iostream>
#include <thread>
using namespace InfinityScriptPersistence;

int main() {
  for (const auto& item : std::vector<std::pair<int,std::string>>{
      {10,"recover.sqlite:service.py"},
      {11,"recover.script:default.py"},
      {12,"recover.cleanup:service.py"}}) {
    Admit(item.first,item.second);
    Observed(item.first);
  }
  Fail(10,"sqlite_write_failed","statement_failed_but_rolled_back");
  Fail(11,"uncaught_script_failure_before_persistence_receipt");
  Fail(12,"unraisable_python_cleanup_or_write_failure");
  Retired(10);Retired(11);Retired(12);

  auto before=Snapshot();
  assert(before.active==0);
  assert(before.retired==3);
  assert(before.failedSettled==0);
  assert(before.advisoryRetired==3);
  assert(before.blockingCount==0);
  assert(before.advisoryCount==3);
  assert(before.failure.empty());
  assert(DurableRetirement("recover.sqlite:service.py"));
  assert(DurableRetirement("recover.script:default.py"));
  assert(DurableRetirement("recover.cleanup:service.py"));
  assert(!BlockedRetirement("recover.sqlite:service.py"));

  for(int i=0;i<1000 && !PollCommit();++i)
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
  assert(PollCommit());
  auto after=Snapshot();
  assert(after.durable);
  assert(after.blockingCount==0);
  assert(after.advisoryCount==3);
  std::cout<<"PASS: recovered operation/script diagnostics remain visible without poisoning a durable retirement\n";
}
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--runtime",type=Path,required=True)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="script-blocker-inventory-") as temp:
        temp=Path(temp)
        for name, harness in (("blocking", HARNESS), ("advisory", ADVISORY_HARNESS)):
            source=temp/(name+".cpp")
            source.write_text(harness)
            binary=temp/name
            subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-pthread",
                            "-I",str(args.runtime/"xbmc"),str(source),"-o",str(binary)],check=True)
            subprocess.run([str(binary)],check=True,timeout=10)

if __name__=="__main__":
    main()
