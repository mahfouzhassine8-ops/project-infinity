#!/usr/bin/env python3
"""RC3 cancellation: only verified Playlist Browser read-only native HTTP.

Scope comes from the actual CPythonInvoker, NOT from diagnostic tracer slots.
The Curl polling thread checks its own cancellation bit: no cross-thread
CCurlFile* access, no pthread kill and no authority to abandon save writers.
"""
import hashlib
import json
from pathlib import Path

CURL="xbmc/filesystem/CurlFile.cpp"
INVOKER="xbmc/interfaces/python/PythonInvoker.cpp"
HEADER="xbmc/filesystem/InfinityCloseNetworkGate.h"
PIN={
 CURL:"176f7931fa3dcfd16aa8adb689c00d6b32764616b0587ab6eb21b832d11c0233",
 INVOKER:"7a1453fe755e4362ce8ee429ff8fc15787119ae47bd4be2e81de4e710749e54b",
}
HEADER_SOURCE=r'''/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
// A minimal independent source identity; tracer capacity/diagnostics never
// determine operational cancellation. Binding exists only for the actual
// CPythonInvoker worker's synchronous calls. Unknown child threads fail closed.
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include <string>

namespace InfinityCloseNetworkGate
{
inline std::string& Owner()
{
  static thread_local std::string addon;
  return addon;
}

class ScopedOwner
{
public:
  explicit ScopedOwner(const std::string& addon) : m_previous(Owner())
  {
    Owner() = addon;
  }
  ~ScopedOwner() { Owner() = m_previous; }
  ScopedOwner(const ScopedOwner&) = delete;
  ScopedOwner& operator=(const ScopedOwner&) = delete;
private:
  std::string m_previous;
};

inline bool CancelPlaylistBrowserRead() noexcept
{
  // Exact owner, read-only HTTP path, only after native Request() owns Close.
  // The caller is responsible for ensuring this is an HTTP read, not a write.
  return InfinityAndroidCheckpoint::IsActive() &&
         Owner() == "plugin.video.playlistbrowser";
}
} // namespace InfinityCloseNetworkGate
'''

def hash_bytes(data): return hashlib.sha256(data).hexdigest()

def once(text,old,new,desc):
    count=text.count(old)
    if count!=1: raise RuntimeError("Unmatched RC3 source anchor: "+desc+" count="+str(count))
    return text.replace(old,new,1)

def apply(root):
    root=Path(root)
    inputs={p:(root/p).read_bytes() for p in PIN}
    if any(hash_bytes(inputs[p])!=PIN[p] for p in PIN):
        raise RuntimeError("RC3 requires exact green RC2 Python and Curl source hashes")
    header=root/HEADER
    if header.exists():raise RuntimeError("RC3 network owner header already exists")
    curl=inputs[CURL].decode()
    python=inputs[INVOKER].decode()
    curl=once(curl, '#include "CurlFile.h"\n',
        '#include "CurlFile.h"\n#if defined(TARGET_ANDROID)\n'
        '#include "InfinityCloseNetworkGate.h"\n#endif\n',
        "CurlFile include")
    # CCurlFile::Open is a read-only IFile::Open, not OpenForWrite. Check before
    # m_opened=true and before Curl allocates a socket.
    curl=once(curl, 'bool CCurlFile::Open(const CURL& url)\n{',
        '''bool CCurlFile::Open(const CURL& url)
{
#if defined(TARGET_ANDROID)
  if (InfinityCloseNetworkGate::CancelPlaylistBrowserRead())
  {
    InfinityShutdownTrace::Event("milestone", "rc3.playlist_read_rejected_at_open");
    return false;
  }
#endif''',
        "CCurlFile read-only Open early admission")
    # A native HTTP request already inside Curl may be stuck in multi_poll().
    # CReadState::FillBuffer() resumes at a bounded poll boundary. Self-cancel
    # there on the SAME Python/native thread: no unsafe cross-thread pointer.
    # Keep existing cancelled instrumentation, normal behavior and retries.
    marker='''#if defined(TARGET_ANDROID)
    if (m_cancelled) InfinityVfsOpenTrace::CancelFlagSeen();
#endif
    if (m_cancelled)
      return FILLBUFFER_NO_DATA;'''
    replacement='''#if defined(TARGET_ANDROID)
    if (!m_cancelled && InfinityCloseNetworkGate::CancelPlaylistBrowserRead())
    {
      m_cancelled = true;
      InfinityShutdownTrace::Event("milestone", "rc3.playlist_read_cancelled_in_poll");
    }
    if (m_cancelled) InfinityVfsOpenTrace::CancelFlagSeen();
#endif
    if (m_cancelled)
      return FILLBUFFER_NO_DATA;'''
    curl=once(curl,marker,replacement,"Curl buffered read cancellation check")
    python=once(python,'#include "PythonInvoker.h"\n',
        '#include "PythonInvoker.h"\n#if defined(TARGET_ANDROID)\n'
        '#include "filesystem/InfinityCloseNetworkGate.h"\n#endif\n',
        "Python invoker include")
    python=once(python,'  m_sourceFile = script;\n',
        '''  m_sourceFile = script;
#if defined(TARGET_ANDROID)
  // Exactly bind this executing Python service's add-on ID for native HTTP
  // reads. No AST inspection, tracer dependency or global network ban.
  InfinityCloseNetworkGate::ScopedOwner infinityNetworkOwner(
      m_addon ? m_addon->ID() : std::string{});
#endif
''',
        "Python interpreter worker identity binding")
    outputs={CURL:curl.encode(),INVOKER:python.encode(),HEADER:HEADER_SOURCE.encode()}
    for p,data in outputs.items():
        target=root/p
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    return {
      "before":PIN,"after":{p:hash_bytes(v) for p,v in outputs.items()},
      "changed":sorted(PIN),"added":[HEADER],
      "scope":"Targeted read-only native Curl for verified Playlist Browser owner when native Close active",
      "ordinary_running_unchanged":True,
      "unverified_addon_writes_abandoned":False,
      "required_saves_waived":False,
      "native_thread_kills":False,
      "snapshot_of_unidentified_child_threads_cancelled":False,
      "full_engine_compiled":False,
      "physical_verified":False
    }

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    result=apply(a.source)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
