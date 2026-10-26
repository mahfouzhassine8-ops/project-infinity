"""Deterministic exceptional-consumer regression against the real signed407 module."""
import ast
import hashlib
import os
from pathlib import Path
import threading
import types
import unittest
import uuid

import patch_search_lifetime

BASE = Path(os.environ["FINAL_SIGNED_SEARCH"])
FIXED = Path(os.environ["FINAL_PATCHED_SEARCH"])
PATH = "plugin://plugin.video.seren/?q=verified-test"

def load(path, rpc, monitor=None, thread_api=threading):
    parsed = ast.parse(path.read_text())
    nodes = [n for n in parsed.body if isinstance(n, ast.FunctionDef)
             and n.name in ("_native_search_admission", "_leased_directory")]
    assert len(nodes) == 2
    scope = dict(threading=thread_api, hashlib=hashlib, uuid=uuid, MAX_RESULTS=40,
                 PROPERTIES=["title"], rpc=rpc,
                 xbmc=types.SimpleNamespace(Monitor=monitor or
                      (lambda: types.SimpleNamespace(abortRequested=lambda:False))))
    exec(compile(ast.fix_missing_locations(ast.Module(nodes,type_ignores=[])),str(path),"exec"),scope)
    return scope

class Home:
    def __init__(self, fail_cleanup=False):
        self.props = {}
        self.clear_attempts = []
        self.fail_cleanup = fail_cleanup
        self.lock = threading.Lock()
    def setProperty(self, key, value):
        with self.lock:
            self.props[key] = value
    def getProperty(self, key):
        with self.lock:
            if ".Result." in key:
                self.props[key] = "completed"
            return self.props.get(key, "")
    def clearProperty(self, key):
        with self.lock:
            self.clear_attempts.append(key)
            if self.fail_cleanup and ".Request." in key:
                raise RuntimeError("controlled cleanup failure")
            self.props.pop(key, None)

class RPC:
    def __init__(self, error=False):
        self.started = threading.Event()
        self.release = threading.Event()
        self.guard = threading.Lock()
        self.count = self.inflight = self.peak = 0
        self.error = error
    def __call__(self, method, params):
        assert method == "Files.GetDirectory"
        assert params["directory"].startswith("plugin://plugin.video.")
        assert "|infinity_search=" in params["directory"]
        with self.guard:
            self.count += 1
            self.inflight += 1
            self.peak = max(self.peak, self.inflight)
            self.started.set()
        try:
            if not self.release.wait(5):
                raise RuntimeError("test worker deadline")
            if self.error:
                raise ValueError("controlled provider error")
            return {"result":{"files":[]}}
        finally:
            with self.guard:
                self.inflight -= 1

class SearchLifetimeTests(unittest.TestCase):
    def start_faulting_consumer(self, source):
        rpc, home = RPC(), Home()
        fault_seen, done = threading.Event(), threading.Event()
        errors = []
        def fail():
            fault_seen.set()
            raise RuntimeError("controlled consumer callback failure")
        scope = load(source, rpc, lambda:types.SimpleNamespace(abortRequested=fail))
        def call():
            try:
                scope["_leased_directory"](PATH, home)
            except Exception as error:
                errors.append(error)
            finally:
                done.set()
        caller = threading.Thread(target=call)
        caller.start()
        self.assertTrue(rpc.started.wait(2))
        self.assertTrue(fault_seen.wait(2))
        return rpc, home, caller, done, errors
    def retire(self, rpc, *callers):
        rpc.release.set()
        for caller in callers:
            caller.join(2)
            self.assertFalse(caller.is_alive(), "Test consumer failed to retire")
        # The consumer joins its worker in the candidate. The old reproduction's
        # escaped worker is independently bounded by the same release event.
        for worker in threading.enumerate():
            if worker.name == "InfinitySearchResult":
                worker.join(2)
                self.assertFalse(worker.is_alive())
        self.assertEqual(rpc.inflight, 0)
    def test_signed407_reproduces_slot_release_with_live_rpc(self):
        rpc, home, caller, done, errors = self.start_faulting_consumer(BASE)
        second = None
        try:
            self.assertTrue(done.wait(2), "Signed407 exceptional consumer did not return")
            self.assertEqual(rpc.inflight, 1)
            other_scope = load(BASE, rpc)
            second = threading.Thread(target=lambda:other_scope["_leased_directory"](
                "plugin://plugin.video.umbrella/?q=independent", Home()))
            second.start()
            # Observe the second actual RPC admission under a deterministic
            # event, rather than infer concurrency from pending thread count.
            with rpc.guard:
                peak = rpc.peak
            if peak < 2:
                for unused in range(100):
                    with rpc.guard:
                        peak = rpc.peak
                    if peak == 2:
                        break
                    threading.Event().wait(.01)
            self.assertEqual(peak, 2, "Expected baseline exceptional-consumer race")
            self.assertEqual(len(errors), 1)
        finally:
            self.retire(rpc, caller, *([second] if second else []))
    def test_candidate_holds_slot_until_original_rpc_retires_after_consumer_fault(self):
        rpc, home, caller, done, errors = self.start_faulting_consumer(FIXED)
        try:
            self.assertFalse(done.is_set(), "Live original native consumer must stay owned")
            independent = load(FIXED, rpc)
            status, result = independent["_leased_directory"](
                "plugin://plugin.video.umbrella/?q=independent", Home())
            self.assertEqual(status, "busy")
            self.assertIn("previous Infinity Search", result["error"]["message"])
            self.assertEqual(rpc.count, 1)
            self.assertEqual(rpc.peak, 1)
        finally:
            self.retire(rpc, caller)
        self.assertEqual(len(errors), 1)
        self.assertEqual(home.props, {})
    def test_fifty_independent_invokers_do_not_queue_workers_or_leak_descriptors(self):
        before = len(os.listdir("/proc/self/fd"))
        rpc, home, caller, done, errors = self.start_faulting_consumer(FIXED)
        try:
            for index in range(50):
                independent = load(FIXED, rpc)
                status, unused = independent["_leased_directory"](PATH+str(index), Home())
                self.assertEqual(status, "busy")
            self.assertEqual(rpc.count, 1)
            self.assertEqual(sum(t.name == "InfinitySearchResult" for t in threading.enumerate()), 1)
        finally:
            self.retire(rpc, caller)
        self.assertEqual(len(os.listdir("/proc/self/fd")), before)
    def test_rpc_error_releases_capacity_and_original_path_handshake_stays(self):
        rpc = RPC(error=True)
        rpc.release.set()
        for index in range(4):
            home = Home()
            status, result = load(FIXED, rpc)["_leased_directory"](PATH+str(index), home)
            self.assertEqual(status, "completed")
            self.assertEqual(result, {"error":{"message":"provider_failed"}})
            self.assertEqual(home.props, {})
        self.assertEqual(rpc.count, 4)
        self.assertEqual(rpc.peak, 1)
    def test_each_token_cleanup_is_attempted_and_error_is_not_hidden(self):
        rpc = RPC()
        rpc.release.set()
        home = Home(fail_cleanup=True)
        with self.assertRaisesRegex(RuntimeError, "cleanup failure"):
            load(FIXED, rpc)["_leased_directory"](PATH, home)
        self.assertEqual(len(home.clear_attempts), 3)
        self.assertFalse(any(".Result." in k for k in home.props))
        load(FIXED, rpc)["_leased_directory"](PATH, Home())
        self.assertEqual(rpc.count, 2)
    def test_thread_start_failure_does_not_strand_admission_or_tokens(self):
        class NoStart:
            ident = None
            def __init__(self, **kwargs):
                pass
            def start(self):
                raise RuntimeError("controlled start failure")
            def is_alive(self):
                return False
        rpc, home = RPC(), Home()
        with self.assertRaisesRegex(RuntimeError, "start failure"):
            load(FIXED, rpc, thread_api=types.SimpleNamespace(Thread=NoStart))["_leased_directory"](PATH, home)
        self.assertEqual(home.props, {})
        self.assertEqual(rpc.count, 0)
        rpc.release.set()
        load(FIXED, rpc)["_leased_directory"](PATH, Home())
        self.assertEqual(rpc.count, 1)
    def test_exact_delta_rejects_unknown_source_and_keeps_all_other_functions(self):
        raw = BASE.read_bytes()
        self.assertEqual(patch_search_lifetime.patch(raw), FIXED.read_bytes())
        with self.assertRaises(ValueError):
            patch_search_lifetime.patch(raw+b"\n# unknown source\n")
        before, after = {}, {}
        for path, target in ((BASE,before),(FIXED,after)):
            text = path.read_text()
            for n in ast.parse(text).body:
                if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                    target[n.name] = ast.get_source_segment(text,n)
        self.assertEqual(set(before), set(after))
        self.assertEqual([k for k in before if before[k] != after[k]], ["_leased_directory"])
        self.assertEqual(before["_native_search_admission"], after["_native_search_admission"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
