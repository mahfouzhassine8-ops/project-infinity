#!/usr/bin/env python3
"""Stage one native source file only; never edit the restored native tree or build an engine."""
from pathlib import Path
import difflib,hashlib,json
HERE=Path(__file__).resolve().parent
NATIVE=Path('/tmp/kodi451-restored-native')
PATH='xbmc/messaging/ApplicationMessenger.cpp'

PREDICATE='''namespace
{
bool IsCheckpointPlaybackControl(const ThreadMessage& message)
{
  // These Android lifecycle/focus requests target CApplication::OnAction,
  // whose existing checkpoint guard refuses execution before any player or
  // persistence work. Never admit a window-targeted or unrelated GUI action.
  if (message.dwMessage != TMSG_GUI_ACTION || message.param1 != WINDOW_INVALID ||
      message.param2 != -1 || message.param3 != 0 || !message.lpVoid || !message.strParam.empty() ||
      !message.params.empty())
    return false;

  const int action = static_cast<const CAction*>(message.lpVoid)->GetID();
  return action == ACTION_PAUSE || action == ACTION_STOP || action == ACTION_PLAYER_PLAY;
}
} // namespace

'''

def sha(raw):return hashlib.sha256(raw).hexdigest()
def once(text,before,after):
    assert text.count(before)==1,before
    return text.replace(before,after,1)
def transform(raw):
    text=raw.decode()
    text=once(text,'#include "platform/android/activity/InfinityAndroidCheckpoint.h"',
      '#include "platform/android/activity/InfinityAndroidCheckpoint.h"\n'
      '#include "guilib/WindowIDs.h"\n#include "input/actions/Action.h"\n#include "input/actions/ActionIDs.h"')
    text=once(text,'#if defined(TARGET_ANDROID)\nvoid CApplicationMessenger::ProcessCheckpointDisplayMessages()',
      '#if defined(TARGET_ANDROID)\n'+PREDICATE+'void CApplicationMessenger::ProcessCheckpointDisplayMessages()')
    text=once(text,"  // Only Kodi's process thread may touch its native display. The checkpoint\n  // continues to reject ordinary actions/writes, including after a failure.",
      "  // Only Kodi's process thread may run these receivers. Playback controls\n  // reach the unchanged OnAction rejection guard; ordinary messages/writes\n  // remain closed, including after a failed checkpoint.")
    text=once(text,'if (!selected && (message->dwMessage == TMSG_DISPLAY_SETUP ||\n                        message->dwMessage == TMSG_DISPLAY_DESTROY))',
      'if (!selected && (message->dwMessage == TMSG_DISPLAY_SETUP ||\n                        message->dwMessage == TMSG_DISPLAY_DESTROY ||\n                        IsCheckpointPlaybackControl(*message)))')
    text=once(text,'    // Retain the real callback, payload lifetime and acknowledgment ordering.\n    // Do not wake Android before its display operation has actually returned.',
      '    // Retain the real receiver, payload lifetime and acknowledgment order.\n    // Wake the sender only after the display handler or existing playback\n    // rejection guard has returned. This grants no persistence receipt.')
    return text.encode()
def main():
    expected=json.loads(Path('/tmp/kodi451-restored-proof/CANDIDATE-NATIVE-SOURCE-MAP.json').read_text())
    before=(NATIVE/PATH).read_bytes();assert sha(before)==expected[PATH]
    out=HERE/'candidate';assert not out.exists(),'Preserve existing candidate'
    after=transform(before);target=out/PATH;target.parent.mkdir(parents=True);target.write_bytes(after)
    (HERE/'CANDIDATE.patch').write_text(''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+PATH,tofile='b/'+PATH)))
    delta={'native_preimage':'preserved452; baseline451 retained; no release promotion','changed_paths':[PATH],
      'before':{PATH:sha(before)},'after':{PATH:sha(after)},
      'changed_methods':['new Android-only IsCheckpointPlaybackControl predicate','ProcessCheckpointDisplayMessages selective admission only'],
      'allowed_actions':['ACTION_PAUSE','ACTION_STOP','ACTION_PLAYER_PLAY (existing onResume request)'],
      'unchanged':['SendMsg synchronization','ProcessMessage routing','Cleanup/Stop','native Android callbacks','OnAction checkpoint guard','display handlers','checkpoint coordinator/write/durability gates','all settings-retirement code'],
      'behavior_during_checkpoint':'Existing OnAction refusal completes; player Pause/Stop/Play does not execute. Sender completion is not save completion.',
      'production_tree_edited':False,'engine_or_APK_built':False}
    (HERE/'SOURCE-DELTA.json').write_text(json.dumps(delta,indent=2)+'\n')
    print(json.dumps(delta,indent=2))
if __name__=='__main__':main()
