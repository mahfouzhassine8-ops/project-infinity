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

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--runtime",type=Path,required=True)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="script-blocker-inventory-") as temp:
        temp=Path(temp)
        source=temp/"test.cpp"
        source.write_text(HARNESS)
        binary=temp/"test"
        subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-pthread",
                        "-I",str(args.runtime/"xbmc"),str(source),"-o",str(binary)],check=True)
        subprocess.run([str(binary)],check=True,timeout=10)

if __name__=="__main__":
    main()
