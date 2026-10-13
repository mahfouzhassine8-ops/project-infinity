#!/usr/bin/env python3
"""Exercise the actual gate in separate JVM processes with real OS file locks.

No Android task manager, native engine or phone acceptance is inferred.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import select
import subprocess
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parents[1]
PEER = '''package com.projectinfinity.kodi;
import java.io.*;
public final class GatePeer {
  static void require(boolean value) { if (!value) throw new AssertionError("gate invariant"); }
  public static void main(String[] args) throws Exception {
    File dir=new File(args[1]); String mode=args[0];
    if (mode.startsWith("entry")) {
      if (!InfinityTaskLifecycleGate.retainEntry(dir)) { System.out.println("BUSY"); return; }
      if (mode.equals("entry-repeat")) {
        require(InfinityTaskLifecycleGate.retainEntry(dir));
        require(InfinityTaskLifecycleGate.beginRemoval(dir)==null);
        require(!InfinityTaskLifecycleGate.retainEntry(new File(dir,"different-directory")));
      }
      System.out.println("ACQUIRED");System.out.flush();
      new BufferedReader(new InputStreamReader(System.in)).readLine();
      // Intentionally no release API: the process must retain entry until exit.
    } else {
      try (InfinityTaskLifecycleGate.Removal removal=InfinityTaskLifecycleGate.beginRemoval(dir)) {
        if (removal==null) {System.out.println("BUSY");return;}
        if(mode.equals("removal-repeat")) {
          require(InfinityTaskLifecycleGate.beginRemoval(dir)==null);
          require(!InfinityTaskLifecycleGate.retainEntry(dir));
        }
        System.out.println("ACQUIRED");System.out.flush();
        new BufferedReader(new InputStreamReader(System.in)).readLine();
      }
    }
  }
}
'''

class ProcessGateTest(unittest.TestCase):
    build = None
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.peers = []
    def tearDown(self):
        for peer in self.peers:
            if peer.poll() is None:
                peer.kill()
            peer.communicate(timeout=10)
        self.temp.cleanup()
    def start(self, mode):
        peer = subprocess.Popen(['java','-ea','-cp',str(self.build),
            'com.projectinfinity.kodi.GatePeer',mode,str(self.directory)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            text=True)
        self.peers.append(peer)
        ready,_,_=select.select([peer.stdout],[],[],10)
        if not ready:
            self.fail('Gate peer did not return a nonblocking decision before test watchdog')
        result=peer.stdout.readline().strip()
        if result not in ('ACQUIRED','BUSY'):
            self.fail('Peer failed: '+result+' '+peer.stderr.read())
        return peer,result
    def stop(self, peer, killed=False):
        if killed:
            peer.kill()
            peer.communicate(timeout=10)
        else:
            out,err=peer.communicate('\n',timeout=10)
            self.assertEqual(peer.returncode,0,err)
    def busy(self,mode):
        p,r=self.start(mode);self.assertEqual(r,'BUSY');self.stop(p)
    def held(self,mode):
        p,r=self.start(mode);self.assertEqual(r,'ACQUIRED');return p

    def test_entry_blocks_removal_before_publication(self):
        p=self.held('entry');self.busy('removal');self.stop(p)
        q=self.held('removal');self.stop(q)
    def test_removal_blocks_entry_until_completion(self):
        p=self.held('removal');self.busy('entry');self.stop(p)
        q=self.held('entry');self.stop(q)
    def test_failed_removal_contender_does_not_release_owner(self):
        p=self.held('removal');self.busy('removal');self.busy('entry');self.stop(p)
    def test_same_process_entry_probes_do_not_drop_os_lease(self):
        p=self.held('entry-repeat');self.busy('removal');self.stop(p)
    def test_same_process_removal_probes_do_not_drop_os_lease(self):
        p=self.held('removal-repeat');self.busy('entry');self.stop(p)
    def test_entry_process_death_releases_lease(self):
        p=self.held('entry');self.busy('removal');self.stop(p,killed=True)
        q=self.held('removal');self.stop(q)
    def test_guard_process_death_releases_lease(self):
        p=self.held('removal');self.busy('entry');self.stop(p,killed=True)
        q=self.held('entry');self.stop(q)
    def test_shared_entry_owners_all_have_to_exit(self):
        p=self.held('entry');q=self.held('entry');self.busy('removal');self.stop(p)
        self.busy('removal');self.stop(q);r=self.held('removal');self.stop(r)
    def test_lock_inode_not_replaced_on_retirement(self):
        p=self.held('removal');path=self.directory/'infinity-native-task-entry-v1.lock'
        original=os.stat(path).st_ino;self.stop(p)
        q=self.held('entry');self.assertEqual(original,os.stat(path).st_ino);self.stop(q)
    def test_repeated_guard_and_entry_handoff(self):
        for _ in range(5):
            p=self.held('removal');self.busy('entry');self.stop(p)
            q=self.held('entry');self.busy('removal');self.stop(q)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    gate=HERE/'InfinityTaskLifecycleGate.java.in'
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp);package=folder/'com/projectinfinity/kodi';package.mkdir(parents=True)
        (package/'InfinityTaskLifecycleGate.java').write_text(gate.read_text().replace('@APP_PACKAGE@','com.projectinfinity.kodi'))
        (package/'GatePeer.java').write_text(PEER)
        subprocess.run(['javac','--release','11','-Xlint:all','-Werror','-d',str(folder),
            str(package/'InfinityTaskLifecycleGate.java'),str(package/'GatePeer.java')],check=True)
        ProcessGateTest.build=folder
        with (args.out/'process-gate.log').open('w') as log:
            result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProcessGateTest))
    report={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'passed':result.wasSuccessful(),'gate_sha256':hashlib.sha256(gate.read_bytes()).hexdigest(),
        'scope':'Actual Java gate in separate host JVMs; real file locks and process death. Not Android task lifecycle or a native-engine build.'}
    (args.out/'process-gate.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not result.wasSuccessful():raise SystemExit(1)
if __name__=='__main__':main()
