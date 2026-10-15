#!/usr/bin/env python3
"""Latch checkpoint abort for late Monitor registration; no save/exit waiver."""
from pathlib import Path
import argparse
import hashlib
import json

PINS = {
    'xbmc/interfaces/python/XBPython.cpp': 'b8c041ef300537694d7ad6156ab8f507ab97c05f7f3a503dd6cf484de279ab27',
    'xbmc/interfaces/python/XBPython.h': '306b2a9629b191e49fa66e7e7b6caca598364606a38b1dfc23d7d1e2ca509c7f',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Missing or ambiguous approved source anchor: ' + old[:120])
    return text.replace(old, new, 1)


def transform(name, text):
    if name.endswith('XBPython.h'):
        text = once(text, '#include <memory>\n', '#include <memory>\n#if defined(TARGET_ANDROID)\n#include <set>\n#endif\n')
        return once(text, '  MonitorCallbackList m_vecMonitorCallbackList;\n', '''  MonitorCallbackList m_vecMonitorCallbackList;
#if defined(TARGET_ANDROID)
  // Guarded by m_vecMonitorCallbackList. Admission is closed before checkpoint
  // notification; IDs cannot be admitted/reused after this latch is installed.
  std::set<long> m_checkpointAbortedInvokerIds;
#endif
''')
    if name.endswith('XBPython.cpp'):
        text = once(text, '#include "XBPython.h"\n', '''#include "XBPython.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif
''')
        text = once(text, '''  if (IsShutdownRequested())
    pCallback->AbortNotify();''', '''  if (IsShutdownRequested()
#if defined(TARGET_ANDROID)
      || (InfinityAndroidCheckpoint::IsActive() &&
          m_checkpointAbortedInvokerIds.count(pCallback->GetInvokerId()) != 0)
#endif
      )
    pCallback->AbortNotify();''')
        return once(text, '''  LOCK_AND_COPY(std::vector<XBMCAddon::xbmc::Monitor*>, tmp, m_vecMonitorCallbackList);
  for (auto& it : tmp)
  {
    if (CHECK_FOR_ENTRY(m_vecMonitorCallbackList, it))
    {
      if (invokerId < 0 || it->GetInvokerId() == invokerId)
        it->AbortNotify();
    }
  }
}''', '''#if defined(TARGET_ANDROID)
  if (invokerId >= 0 && InfinityAndroidCheckpoint::IsActive())
  {
    // Signal only the invocation selected by the existing coordinator. Keep
    // canonical save participants running. The same native lock serializes
    // latching, existing notifications and registration, so both orders work.
    // AbortNotify sets a native event; no GIL, callback, join or exception.
    std::unique_lock<CCriticalSection> lock(m_vecMonitorCallbackList);
    m_checkpointAbortedInvokerIds.insert(invokerId);
    for (auto* monitor : m_vecMonitorCallbackList)
      if (monitor->GetInvokerId() == invokerId)
        monitor->AbortNotify();
    return;
  }
#endif
  LOCK_AND_COPY(std::vector<XBMCAddon::xbmc::Monitor*>, tmp, m_vecMonitorCallbackList);
  for (auto& it : tmp)
  {
    if (CHECK_FOR_ENTRY(m_vecMonitorCallbackList, it))
    {
      if (invokerId < 0 || it->GetInvokerId() == invokerId)
        it->AbortNotify();
    }
  }
}''')
    raise ValueError('Unapproved target: ' + name)


def apply(root, receipt):
    root = Path(root)
    inputs = {name: (root / name).read_bytes() for name in PINS}
    if any(digest(inputs[name]) != expected for name, expected in PINS.items()):
        raise ValueError('Not the exact green 2103377 XBPython source')
    outputs = {name: transform(name, data.decode()).encode() for name, data in inputs.items()}
    for name, data in outputs.items():
        (root / name).write_bytes(data)
    result = dict(before=PINS, after={name: digest(data) for name, data in outputs.items()},
                  changed=sorted(PINS), checkpoint_abort_latched=True,
                  save_authority_changed=False, termination_authority_changed=False,
                  shutdown_timeout_changed=False, threads_forcibly_killed=False,
                  shutdown_repaired=False, complete_native_compilation=False)
    Path(receipt).write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    apply(args.source, args.receipt)
