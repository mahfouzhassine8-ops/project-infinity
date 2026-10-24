from pathlib import Path
import re

root = Path('kodi')
main_h = root / 'xbmc/platform/android/activity/JNIMainActivity.h'
main_cpp = root / 'xbmc/platform/android/activity/JNIMainActivity.cpp'
app_h = root / 'xbmc/platform/android/activity/XBMCApp.h'
app_cpp = root / 'xbmc/platform/android/activity/XBMCApp.cpp'
for p in (main_h, main_cpp, app_h, app_cpp):
    if not p.exists():
        raise SystemExit(f'missing Kodi 21.3 source file: {p}')

# -----------------------------------------------------------------------------
# Native hook contract exposed to the Android/Infinity layer.
# Keep it deliberately narrow: player truth + safe display-state synchronization.
# New upper-layer behavior should use these hooks before adding more native surgery.
# -----------------------------------------------------------------------------

h = main_h.read_text()
if '_infinityHasActiveVideo' not in h:
    anchor = '  static void _onVisibleBehindCanceled(JNIEnv *env, jobject context);\n'
    if anchor not in h:
        raise SystemExit('JNIMainActivity.h static-method anchor missing')
    h = h.replace(anchor, anchor +
        '  static jboolean _infinityHasActiveVideo(JNIEnv* env, jobject context);\n'
        '  static void _infinitySyncDisplayState(JNIEnv* env, jobject context);\n', 1)

if 'infinityHasActiveVideo() const' not in h:
    anchor = '  virtual void onDisplayRemoved(int displayId)=0;\n'
    if anchor not in h:
        raise SystemExit('JNIMainActivity.h virtual anchor missing')
    h = h.replace(anchor, anchor +
        '\n  // Infinity stable native bridge.\n'
        '  virtual bool infinityHasActiveVideo() const = 0;\n'
        '  virtual void infinitySyncDisplayStateFromBridge() = 0;\n', 1)
main_h.write_text(h)

cpp = main_cpp.read_text()
if '"_infinityHasActiveVideo"' not in cpp:
    anchor = '        {"_onVisibleBehindCanceled", "()V",\n         reinterpret_cast<void*>(&CJNIMainActivity::_onVisibleBehindCanceled)},\n'
    if anchor not in cpp:
        raise SystemExit('JNIMainActivity.cpp registration anchor missing')
    cpp = cpp.replace(anchor, anchor +
        '        {"_infinityHasActiveVideo", "()Z",\n'
        '         reinterpret_cast<void*>(&CJNIMainActivity::_infinityHasActiveVideo)},\n'
        '        {"_infinitySyncDisplayState", "()V",\n'
        '         reinterpret_cast<void*>(&CJNIMainActivity::_infinitySyncDisplayState)},\n', 1)

if 'jboolean CJNIMainActivity::_infinityHasActiveVideo' not in cpp:
    anchor = 'void CJNIMainActivity::_onVisibleBehindCanceled(JNIEnv* env, jobject context)\n'
    pos = cpp.find(anchor)
    if pos < 0:
        raise SystemExit('JNIMainActivity.cpp implementation anchor missing')
    body = '''jboolean CJNIMainActivity::_infinityHasActiveVideo(JNIEnv* env, jobject context)\n{\n  (void)env;\n  (void)context;\n  return (m_appInstance && m_appInstance->infinityHasActiveVideo()) ? JNI_TRUE : JNI_FALSE;\n}\n\nvoid CJNIMainActivity::_infinitySyncDisplayState(JNIEnv* env, jobject context)\n{\n  (void)env;\n  (void)context;\n  if (m_appInstance)\n    m_appInstance->infinitySyncDisplayStateFromBridge();\n}\n\n'''
    cpp = cpp[:pos] + body + cpp[pos:]
main_cpp.write_text(cpp)

ah = app_h.read_text()
if 'infinityHasActiveVideo() const override' not in ah:
    anchor = '  bool HasFocus() const { return m_hasFocus; }\n'
    if anchor not in ah:
        raise SystemExit('XBMCApp.h public hook anchor missing')
    ah = ah.replace(anchor, anchor +
        '\n  // Infinity native bridge implementation.\n'
        '  bool infinityHasActiveVideo() const override;\n'
        '  void infinitySyncDisplayStateFromBridge() override;\n', 1)
app_h.write_text(ah)

ac = app_cpp.read_text()
if 'bool CXBMCApp::infinityHasActiveVideo() const' not in ac:
    marker = 'void CXBMCApp::onConfigurationChanged()\n'
    pos = ac.find(marker)
    if pos < 0:
        raise SystemExit('XBMCApp.cpp hook insertion anchor missing')
    body = '''bool CXBMCApp::infinityHasActiveVideo() const\n{\n  if (!g_application.IsInitialized())\n    return false;\n\n  const auto& components = CServiceBroker::GetAppComponents();\n  const auto appPlayer = components.GetComponent<CApplicationPlayer>();\n  return appPlayer && appPlayer->IsPlaying() && appPlayer->HasVideo();\n}\n\nvoid CXBMCApp::infinitySyncDisplayStateFromBridge()\n{\n  InfinitySyncDisplayState();\n}\n\n'''
    ac = ac[:pos] + body + ac[pos:]
app_cpp.write_text(ac)

# Static contract checks.
checks = {
    main_h: ('_infinityHasActiveVideo', 'infinitySyncDisplayStateFromBridge'),
    main_cpp: ('"_infinityHasActiveVideo"', 'CJNIMainActivity::_infinitySyncDisplayState'),
    app_h: ('infinityHasActiveVideo() const override', 'infinitySyncDisplayStateFromBridge() override'),
    app_cpp: ('appPlayer->IsPlaying() && appPlayer->HasVideo()', 'InfinitySyncDisplayState();'),
}
for p, tokens in checks.items():
    txt = p.read_text()
    for token in tokens:
        if token not in txt:
            raise SystemExit(f'{p}: missing expected token {token}')

print('Infinity 7.1 native hook installed: core player gate + display sync bridge')
