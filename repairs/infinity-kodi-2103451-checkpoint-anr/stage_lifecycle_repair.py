"""Stage only the checkpoint display-dispatch correction on exact source preimages.

This does not compile/package an engine or substitute a partial source inventory
for the required final native map and signed-451 preservation gates.
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import json

APP = 'xbmc/application/Application.cpp'
CPP = 'xbmc/messaging/ApplicationMessenger.cpp'
HEADER = 'xbmc/messaging/ApplicationMessenger.h'
PINS = {
    APP: 'fb5167b4fd7cb7fa16357fe367c9d212ae9440b4821870e4fd2d90018d9b4356',
    CPP: 'e998192278d6f5d99783647a1f16a4fdb71be791a826cbe4b5db31b67b2e50a5',
    HEADER: 'c89c0b7c5cf53349ac6c739b9d6f3365a40ddcf4fdbf8c4cc438b52c561fa251',
}

DISPLAY_PUMP = r'''#if defined(TARGET_ANDROID)
void CApplicationMessenger::ProcessCheckpointDisplayMessages()
{
  // Only Kodi's process thread may touch its native display. The checkpoint
  // continues to reject ordinary actions/writes, including after a failure.
  if (!IsProcessThread() || !InfinityAndroidCheckpoint::IsActive())
    return;

  std::unique_lock<CCriticalSection> lock(m_critSection);
  // Bound one pass to the initially queued population. New lifecycle events
  // remain owned by the same queue and can run on a later application frame.
  std::size_t remaining = m_vecMessages.size();
  while (remaining > 0 && !m_bStop)
  {
    --remaining;
    ThreadMessage* selected = nullptr;
    std::queue<ThreadMessage*> retained;
    while (!m_vecMessages.empty())
    {
      ThreadMessage* message = m_vecMessages.front();
      m_vecMessages.pop();
      if (!selected && (message->dwMessage == TMSG_DISPLAY_SETUP ||
                        message->dwMessage == TMSG_DISPLAY_DESTROY))
        selected = message;
      else
        retained.push(message);
    }
    m_vecMessages.swap(retained);
    if (!selected)
      return;

    // Retain the real callback, payload lifetime and acknowledgment ordering.
    // Do not wake Android before its display operation has actually returned.
    const std::shared_ptr<CEvent> waitEvent = selected->waitEvent;
    lock.unlock();
    ProcessMessage(selected);
    if (waitEvent)
      waitEvent->Set();
    delete selected;
    lock.lock();
  }
}
#endif

'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Unexpected checkpoint source anchor: ' + before[:100])
    return text.replace(before, after, 1)


def transform(name, raw):
    if sha(raw) != PINS[name]:
        raise ValueError('Not the reviewed native preimage: ' + name)
    text = raw.decode()
    if name == APP:
        before = '''void CApplication::OnApplicationMessage(ThreadMessage* pMsg)
{
#if defined(TARGET_ANDROID)
  if (InfinityAndroidCheckpoint::IsActive())
    return; // A checkpoint never enters legacy Stop/Cleanup through a queued quit.
#endif'''
        after = '''void CApplication::OnApplicationMessage(ThreadMessage* pMsg)
{
#if defined(TARGET_ANDROID)
  if (InfinityAndroidCheckpoint::IsActive() &&
      pMsg->dwMessage != TMSG_DISPLAY_SETUP && pMsg->dwMessage != TMSG_DISPLAY_DESTROY)
    return; // Keep ordinary actions and legacy Stop/Cleanup outside the checkpoint.
#endif'''
        text = once(text, before, after)
        before = '''void CApplication::Process()
{
#if defined(TARGET_ANDROID)
  if (InfinityAndroidCheckpoint::IsActive())
  {
    InfinityAndroidCheckpoint::Pump(*this);'''
        after = '''void CApplication::Process()
{
#if defined(TARGET_ANDROID)
  if (InfinityAndroidCheckpoint::IsActive())
  {
    // Android can synchronously await surface cleanup while a checkpoint is
    // draining or failed. Service only its real display messages, not general
    // queued actions/callbacks or legacy teardown.
    CServiceBroker::GetAppMessenger()->ProcessCheckpointDisplayMessages();
    InfinityAndroidCheckpoint::Pump(*this);'''
        text = once(text, before, after)
    elif name == HEADER:
        text = once(text, '  void ProcessMessages();', '''  void ProcessMessages();
#if defined(TARGET_ANDROID)
  // Required native lifecycle dispatch while Infinity checkpoint admission is closed.
  void ProcessCheckpointDisplayMessages();
#endif''')
    elif name == CPP:
        text = once(text, '#include "platform/android/activity/InfinityShutdownTrace.h"',
                    '#include "platform/android/activity/InfinityShutdownTrace.h"\n'
                    '#include "platform/android/activity/InfinityAndroidCheckpoint.h"')
        text = once(text, 'void CApplicationMessenger::ProcessMessages()\n{',
                    DISPLAY_PUMP + 'void CApplicationMessenger::ProcessMessages()\n{')
    else:
        raise ValueError('Unauthorized native path: ' + name)
    return text.encode()


def stage(source, out):
    if out.exists():
        raise ValueError('Refusing to overwrite an existing staged candidate')
    originals = {name: (source / name).read_bytes() for name in PINS}
    changed = {name: transform(name, raw) for name, raw in originals.items()}
    out.mkdir(parents=True)
    patch = []
    for name, raw in changed.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        patch.extend(difflib.unified_diff(originals[name].decode().splitlines(True),
                                        raw.decode().splitlines(True),
                                        fromfile='a/' + name, tofile='b/' + name))
    proof = {'kind': 'staged checkpoint-only native display dispatch correction',
             'before': PINS, 'after': {name: sha(raw) for name, raw in changed.items()},
             'changed_methods': ['CApplication::Process checkpoint branch',
                                 'CApplication::OnApplicationMessage checkpoint guard',
                                 'CApplicationMessenger::ProcessCheckpointDisplayMessages (new, Android only)'],
             'unchanged_message_methods': ['SendMsg', 'Cleanup', 'ProcessMessages',
                                           'ProcessWindowMessages', 'ProcessMessage', 'Stop'],
             'queue_payloads_or_waiters_discarded': False,
             'persistence_or_termination_authorization_changed': False,
             'normal_noncheckpoint_dispatch_changed': False,
             'full_native_source_map_verified': False,
             'android_verified': False, 'apk_built_or_signed': False}
    (out / 'SOURCE-DELTA.json').write_text(json.dumps(proof, indent=2) + '\n')
    (out / 'reviewed.patch').write_text(''.join(patch))
    return proof


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(stage(a.source, a.out), indent=2))
