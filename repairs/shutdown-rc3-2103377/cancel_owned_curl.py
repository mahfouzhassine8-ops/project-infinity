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
CURL_H="xbmc/filesystem/CurlFile.h"
INVOKER="xbmc/interfaces/python/PythonInvoker.cpp"
HEADER="xbmc/filesystem/InfinityCloseNetworkGate.h"
PIN={
 CURL:"176f7931fa3dcfd16aa8adb689c00d6b32764616b0587ab6eb21b832d11c0233",
 CURL_H:"ed6dfa11db0568379096c75f8a6c1293de2744c92a8e3621dfeff3fa303fda8c",
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

def apply(root, *, include_invoker=True):
    root=Path(root)
    inputs={p:(root/p).read_bytes() for p in PIN if include_invoker or p!=INVOKER}
    if any(hash_bytes(inputs[p])!=PIN[p] for p in inputs):
        raise RuntimeError("RC3 requires exact green RC2 Python and Curl source hashes")
    header=root/HEADER
    if header.exists():raise RuntimeError("RC3 network owner header already exists")
    curl=inputs[CURL].decode()
    curl_header=inputs[CURL_H].decode()
    python=inputs[INVOKER].decode() if include_invoker else None
    curl=once(curl, '#include "CurlFile.h"\n',
        '#include "CurlFile.h"\n#if defined(TARGET_ANDROID)\n'
        '#include "InfinityCloseNetworkGate.h"\n#endif\n',
        "CurlFile include")
    # CCurlFile::Open is a read-only IFile::Open, not OpenForWrite. Check before
    # m_opened=true and before Curl allocates a socket.
    curl_header=once(curl_header, "          bool m_cancelled;\n",
        "          bool m_cancelled;\n#if defined(TARGET_ANDROID)\n"
        "          bool m_infinityHttpRead{false}; // HTTP-only read, never write\n#endif\n",
        "Curl CReadState HTTP-only marker")
    curl_header=once(curl_header,
       "          bool m_infinityHttpRead{false}; // HTTP-only read, never write\n",
       "          bool m_infinityHttpRead{false}; // HTTP-only read, never write\n"
       "          bool m_infinityCheckpointCancelledRead{false}; // I/O error, not EOF\n",
       "Curl checkpoint-cancel error flag")
    curl=once(curl, 'bool CCurlFile::Open(const CURL& url)\n{',
        '''bool CCurlFile::Open(const CURL& url)
{
#if defined(TARGET_ANDROID)
  m_state->m_infinityCheckpointCancelledRead = false;
  m_state->m_infinityHttpRead = url.GetProtocol() == "http" ||
                               url.GetProtocol() == "https";
  if (m_state->m_infinityHttpRead &&
      InfinityCloseNetworkGate::CancelPlaylistBrowserRead())
  {
    InfinityShutdownTrace::Event("milestone", "rc3.playlist_read_rejected_at_open");
    return false;
  }
#endif''',
        "CCurlFile HTTP read-only Open early admission")
    curl=once(curl, 'bool CCurlFile::OpenForWrite(const CURL& url, bool bOverWrite)\n{',
        '''bool CCurlFile::OpenForWrite(const CURL& url, bool bOverWrite)
{
#if defined(TARGET_ANDROID)
  m_state->m_infinityHttpRead = false; // Never cancel Curl writes.
  m_state->m_infinityCheckpointCancelledRead = false;
#endif''',
        "Curl OpenForWrite excluded")

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
    if (!m_cancelled && m_infinityHttpRead && InfinityCloseNetworkGate::CancelPlaylistBrowserRead())
    {
      m_infinityCheckpointCancelledRead = true;
      m_cancelled = true;
      InfinityShutdownTrace::Event("milestone", "rc3.playlist_read_cancelled_in_poll");
    }
    if (m_cancelled) InfinityVfsOpenTrace::CancelFlagSeen();
#endif
#if defined(TARGET_ANDROID)
    if (m_cancelled && m_infinityCheckpointCancelledRead)
      return FILLBUFFER_FAIL; // I/O failure is not successful EOF.
#endif
    if (m_cancelled)
      return FILLBUFFER_NO_DATA;'''
    curl=once(curl,marker,replacement,"Curl buffered read cancellation check")
    # Connect() can read HTTP status after FillBuffer returns failure.
    # Cancelled reads must never become successful HTTP 200 empty bodies.
    curl=once(curl, '  m_httpresponse = m_state->Connect(m_bufferSize);',
        '''  m_httpresponse = m_state->Connect(m_bufferSize);
#if defined(TARGET_ANDROID)
  if (m_state->m_infinityCheckpointCancelledRead)
    return false;
#endif''', "HTTP Connect must fail after RC3 cancellation")
    # The real pinned Android Curl source already limits multi_poll to 200ms.
    # Do not touch Curl handles from another thread or add unneeded callbacks.
    assert curl.count('multi_poll(m_multiHandle, 200, &ready)') == 1
    curl=once(curl, '''void CCurlFile::Reset()
{
  m_state->m_cancelled = false;
}''',
        '''void CCurlFile::Reset()
{
  m_state->m_cancelled = false;
#if defined(TARGET_ANDROID)
  m_state->m_infinityCheckpointCancelledRead = false;
#endif
}''', "reset RC3 cancellation on Curl state reuse")

    if include_invoker:
        python=once(python,'#include "PythonInvoker.h"\n',
            '#include "PythonInvoker.h"\n#if defined(TARGET_ANDROID)\n'
            '#include "filesystem/InfinityCloseNetworkGate.h"\n#endif\n',
            "Python invoker include")
        python=once(python,'  m_sourceFile = script;\n',
            '''  m_sourceFile = script;
#if defined(TARGET_ANDROID)
  // Bind the executing Python service's addon to synchronous Curl reads.
  // No AST inspection, diagnostic-tracer dependence or global network ban.
  InfinityCloseNetworkGate::ScopedOwner infinityNetworkOwner(
      m_addon ? m_addon->ID() : std::string{});
#endif
''',
            "Python interpreter worker identity binding")
    outputs={CURL:curl.encode(),CURL_H:curl_header.encode(),HEADER:HEADER_SOURCE.encode()}
    if include_invoker: outputs[INVOKER]=python.encode()
    for p,data in outputs.items():
        target=root/p
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    return {
      "before":PIN,"after":{p:hash_bytes(v) for p,v in outputs.items()},
      "changed":sorted(p for p in PIN if include_invoker or p!=INVOKER),"added":[HEADER],
      "full_python_invoker_bound":include_invoker,
      "scope":"Targeted HTTP(S) native Curl read only for verified Playlist Browser owner when native Close active; OpenForWrite unaffected",
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
