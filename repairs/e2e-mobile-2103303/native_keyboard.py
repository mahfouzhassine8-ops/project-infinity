#!/usr/bin/env python3
"""Native Android IME wiring, retaining Kodi's keyboard on TV/remote-only devices."""
from pathlib import Path
import argparse,hashlib,json
from native_controls import once
HERE=Path(__file__).resolve().parent

def apply(root):
    changes=[]
    def change(name,fn):
        p=root/name;before=p.read_bytes() if p.exists() else b''
        after=fn(before.decode()).encode();p.write_bytes(after)
        changes.append({'path':name,'before':hashlib.sha256(before).hexdigest() if before else None,
                        'after':hashlib.sha256(after).hexdigest()})
    for file in ['AndroidKeyboard.h','AndroidKeyboard.cpp']:
        change('xbmc/platform/android/activity/'+file,lambda _,f=file:(HERE/f).read_text())
    change('xbmc/platform/android/activity/CMakeLists.txt',lambda s:
        once(once(s,'            AndroidKey.cpp','            AndroidKey.cpp\n            AndroidKeyboard.cpp'),
                    '            AndroidKey.h','            AndroidKey.h\n            AndroidKeyboard.h'))
    change('xbmc/platform/android/activity/android_main.cpp',lambda s:
        once(once(s,'#include "EventLoop.h"','#include "EventLoop.h"\n#include "AndroidKeyboard.h"'),
                    '  CJNIMainActivity::RegisterNatives(env);','  CJNIMainActivity::RegisterNatives(env);\n  CAndroidKeyboard::RegisterNatives(env);'))
    def factory(s):
        s=once(s,'#include "dialogs/GUIDialogKeyboardGeneric.h"',
            '#include "dialogs/GUIDialogKeyboardGeneric.h"\n#if defined(TARGET_ANDROID)\n#include "dialogs/GUIDialogKeyboardTouch.h"\n#include "platform/android/activity/AndroidKeyboard.h"\n#endif')
        s=once(s,'  bool useKodiKeyboard = true;',
            '  bool useKodiKeyboard = true;\n#if defined(TARGET_ANDROID)\n  useKodiKeyboard = !CAndroidKeyboard::UseAndroidIME();\n#endif')
        s=once(s,'#endif // defined(TARGET_DARWIN_EMBEDDED)\n\n  if (kb)',
            '#endif // defined(TARGET_DARWIN_EMBEDDED)\n#if defined(TARGET_ANDROID)\n  else\n  {\n    auto* touch = winManager.GetWindow<CGUIDialogKeyboardTouch>(WINDOW_DIALOG_KEYBOARD_TOUCH);\n    if (touch) touch->SetInputMode(m_filtering == FILTERING_SEARCH, CAndroidKeyboard::InputKind());\n    kb = touch;\n  }\n#endif\n\n  if (kb)')
        return s
    change('xbmc/guilib/GUIKeyboardFactory.cpp',factory)
    def touch_h(s):
        s=once(s,'  CGUIDialogKeyboardTouch();','''  CGUIDialogKeyboardTouch();
#if defined(TARGET_ANDROID)
  void SetInputMode(bool search, int kind) { m_search = search; m_inputKind = kind; }
  bool OnBack(int actionID) override;
  void OnDeinitWindow(int nextWindowID) override;
#endif''')
        return once(s,'  bool m_confirmed;','  bool m_confirmed;\n  bool m_search{false};\n  int m_inputKind{0};')
    change('xbmc/dialogs/GUIDialogKeyboardTouch.h',touch_h)
    def touch(s):
        s=once(s,'#include "GUIDialogKeyboardTouch.h"',
            '#include "GUIDialogKeyboardTouch.h"\n#if defined(TARGET_ANDROID)\n#include "platform/android/activity/AndroidKeyboard.h"\n#endif')
        s=once(s,'  m_keyboard.reset(new CDarwinEmbedKeyboard());\n#endif',
            '  m_keyboard.reset(new CDarwinEmbedKeyboard());\n#elif defined(TARGET_ANDROID)\n  m_keyboard = std::make_unique<CAndroidKeyboard>(this, m_search, m_inputKind);\n#endif')
        s=once(s,'  m_keyboard.reset();','''#if defined(TARGET_ANDROID)
  // A force-close/deinit cancels the wait before the editor object is destroyed.
  Cancel();
  StopThread(true);
#endif
  m_keyboard.reset();''')
        s=once(s,'  Close();\n}', '''#if defined(TARGET_ANDROID)
  // Do not synchronously wait for the GUI thread which may be joining us.
  Close(false, 0, true, false);
#else
  Close();
#endif
}

#if defined(TARGET_ANDROID)
bool CGUIDialogKeyboardTouch::OnBack(int actionID)
{
  Cancel();
  return true;
}
void CGUIDialogKeyboardTouch::OnDeinitWindow(int nextWindowID)
{
  Cancel();
  CGUIDialog::OnDeinitWindow(nextWindowID);
}
#endif''')
        return s
    change('xbmc/dialogs/GUIDialogKeyboardTouch.cpp',touch)
    from native_numeric import repair
    change('xbmc/dialogs/GUIDialogNumeric.cpp',repair)
    return changes

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    a.receipt.write_text(json.dumps({'changes':apply(a.source),'device_validation':False},indent=2)+'\n')
