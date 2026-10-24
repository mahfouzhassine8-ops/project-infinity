from pathlib import Path

root = Path('kodi')
main_h = root / 'xbmc/platform/android/activity/JNIMainActivity.h'
main_cpp = root / 'xbmc/platform/android/activity/JNIMainActivity.cpp'
app_h = root / 'xbmc/platform/android/activity/XBMCApp.h'
app_cpp = root / 'xbmc/platform/android/activity/XBMCApp.cpp'
for p in (main_h, main_cpp, app_h, app_cpp):
    if not p.exists():
        raise SystemExit(f'missing Kodi 21.3 source file: {p}')

# Candidate D extends the stable hook contract without moving theme UI into libkodi.
# Core/native exposes facts/actions; app/skin chooses presentation.

h = main_h.read_text()
if '_infinitySystemThemeMode' not in h:
    anchor = '  static void _infinitySyncDisplayState(JNIEnv* env, jobject context);\n'
    if anchor not in h:
        raise SystemExit('Candidate C native hook must be applied first')
    h = h.replace(anchor, anchor +
        '  static jint _infinitySystemThemeMode(JNIEnv* env, jobject context);\n'
        '  static jint _infinityWindowWidth(JNIEnv* env, jobject context);\n'
        '  static jint _infinityWindowHeight(JNIEnv* env, jobject context);\n'
        '  static jint _infinityBridgeVersion(JNIEnv* env, jobject context);\n', 1)

if 'infinityWindowWidth() const' not in h:
    anchor = '  virtual void infinitySyncDisplayStateFromBridge() = 0;\n'
    if anchor not in h:
        raise SystemExit('Candidate C virtual bridge contract missing')
    h = h.replace(anchor, anchor +
        '  virtual int infinityWindowWidth() const = 0;\n'
        '  virtual int infinityWindowHeight() const = 0;\n', 1)
main_h.write_text(h)

cpp = main_cpp.read_text()
if '"_infinitySystemThemeMode"' not in cpp:
    anchor = '        {"_infinitySyncDisplayState", "()V",\n         reinterpret_cast<void*>(&CJNIMainActivity::_infinitySyncDisplayState)},\n'
    if anchor not in cpp:
        raise SystemExit('Candidate C registration hook missing')
    cpp = cpp.replace(anchor, anchor +
        '        {"_infinitySystemThemeMode", "()I",\n'
        '         reinterpret_cast<void*>(&CJNIMainActivity::_infinitySystemThemeMode)},\n'
        '        {"_infinityWindowWidth", "()I",\n'
        '         reinterpret_cast<void*>(&CJNIMainActivity::_infinityWindowWidth)},\n'
        '        {"_infinityWindowHeight", "()I",\n'
        '         reinterpret_cast<void*>(&CJNIMainActivity::_infinityWindowHeight)},\n'
        '        {"_infinityBridgeVersion", "()I",\n'
        '         reinterpret_cast<void*>(&CJNIMainActivity::_infinityBridgeVersion)},\n', 1)

if 'jint CJNIMainActivity::_infinitySystemThemeMode' not in cpp:
    anchor = 'void CJNIMainActivity::_onVisibleBehindCanceled(JNIEnv* env, jobject context)\n'
    pos = cpp.find(anchor)
    if pos < 0:
        raise SystemExit('JNIMainActivity implementation anchor missing')
    body = r'''jint CJNIMainActivity::_infinitySystemThemeMode(JNIEnv* env, jobject context)
{
  if (!env || !context)
    return 0;

  // Read Android Configuration.uiMode directly through JNI so System theme is
  // a native bridge fact rather than duplicated guesswork in the skin layer.
  jclass contextClass = env->GetObjectClass(context);
  if (!contextClass)
    return 0;
  jmethodID getResources = env->GetMethodID(contextClass, "getResources", "()Landroid/content/res/Resources;");
  if (!getResources)
    return 0;
  jobject resources = env->CallObjectMethod(context, getResources);
  if (!resources)
    return 0;
  jclass resourcesClass = env->GetObjectClass(resources);
  jmethodID getConfiguration = env->GetMethodID(resourcesClass, "getConfiguration", "()Landroid/content/res/Configuration;");
  if (!getConfiguration)
    return 0;
  jobject configuration = env->CallObjectMethod(resources, getConfiguration);
  if (!configuration)
    return 0;
  jclass configurationClass = env->GetObjectClass(configuration);
  jfieldID uiModeField = env->GetFieldID(configurationClass, "uiMode", "I");
  if (!uiModeField)
    return 0;
  const jint uiMode = env->GetIntField(configuration, uiModeField);
  const jint night = uiMode & 0x30; // UI_MODE_NIGHT_MASK
  if (night == 0x20) // UI_MODE_NIGHT_YES
    return 2;
  if (night == 0x10) // UI_MODE_NIGHT_NO
    return 1;
  return 0;
}

jint CJNIMainActivity::_infinityWindowWidth(JNIEnv* env, jobject context)
{
  (void)env;
  (void)context;
  return m_appInstance ? m_appInstance->infinityWindowWidth() : -1;
}

jint CJNIMainActivity::_infinityWindowHeight(JNIEnv* env, jobject context)
{
  (void)env;
  (void)context;
  return m_appInstance ? m_appInstance->infinityWindowHeight() : -1;
}

jint CJNIMainActivity::_infinityBridgeVersion(JNIEnv* env, jobject context)
{
  (void)env;
  (void)context;
  return 2; // Candidate D contract: player + sync + theme + native dimensions
}

'''
    cpp = cpp[:pos] + body + cpp[pos:]
main_cpp.write_text(cpp)

ah = app_h.read_text()
if 'infinityWindowWidth() const override' not in ah:
    anchor = '  void infinitySyncDisplayStateFromBridge() override;\n'
    if anchor not in ah:
        raise SystemExit('Candidate C XBMCApp hook missing')
    ah = ah.replace(anchor, anchor +
        '  int infinityWindowWidth() const override;\n'
        '  int infinityWindowHeight() const override;\n', 1)
app_h.write_text(ah)

ac = app_cpp.read_text()
if 'int CXBMCApp::infinityWindowWidth() const' not in ac:
    marker = 'void CXBMCApp::onConfigurationChanged()\n'
    pos = ac.find(marker)
    if pos < 0:
        raise SystemExit('XBMCApp insertion anchor missing')
    body = r'''int CXBMCApp::infinityWindowWidth() const
{
  auto window = GetNativeWindow(0);
  return window ? window->GetWidth() : -1;
}

int CXBMCApp::infinityWindowHeight() const
{
  auto window = GetNativeWindow(0);
  return window ? window->GetHeight() : -1;
}

'''
    ac = ac[:pos] + body + ac[pos:]
app_cpp.write_text(ac)

checks = {
    main_h: ('_infinitySystemThemeMode', '_infinityWindowWidth', '_infinityBridgeVersion'),
    main_cpp: ('"_infinitySystemThemeMode"', 'UI_MODE_NIGHT_MASK', 'return 2; // Candidate D contract'),
    app_h: ('infinityWindowWidth() const override', 'infinityWindowHeight() const override'),
    app_cpp: ('GetNativeWindow(0)', 'window->GetWidth()', 'window->GetHeight()'),
}
for p, tokens in checks.items():
    txt = p.read_text()
    for token in tokens:
        if token not in txt:
            raise SystemExit(f'{p}: missing expected Candidate D token {token}')

print('Infinity Candidate D native contract installed: theme state + window dimensions + bridge version')
