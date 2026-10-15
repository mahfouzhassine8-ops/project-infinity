from pathlib import Path

src = Path('/tmp/xbmc/xbmc/platform/android/activity/XBMCApp.cpp')
text = src.read_text()

old_cfg = '''void CXBMCApp::onConfigurationChanged()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  // ignore any configuration changes like screen rotation etc\n}\n'''
new_cfg = '''void CXBMCApp::onConfigurationChanged()\n{\n  android_printf("%s: Infinity Fold Test configuration changed", __PRETTY_FUNCTION__);\n\n  // Fold/cover and multi-window changes can alter the real native surface size.\n  // Keep Kodi alive and refresh its active graphics resolution from the actual\n  // ANativeWindow instead of assuming the original fullscreen metrics.\n  const auto nativeWindow = GetNativeWindow(0);\n  if (nativeWindow && CServiceBroker::GetWinSystem())\n  {\n    const int width = nativeWindow->GetWidth();\n    const int height = nativeWindow->GetHeight();\n    if (width > 0 && height > 0)\n    {\n      auto& gfx = CServiceBroker::GetWinSystem()->GetGfxContext();\n      RESOLUTION_INFO res = gfx.GetResInfo();\n      res.iWidth = width;\n      res.iHeight = height;\n      res.iScreenWidth = width;\n      res.iScreenHeight = height;\n      res.fPixelRatio = 1.0f;\n      gfx.SetResInfo(res);\n\n      if (CServiceBroker::GetGUI())\n      {\n        CGUIMessage msg(GUI_MSG_WINDOW_RESIZE, 0, 0, width, height);\n        CServiceBroker::GetGUI()->GetWindowManager().SendMessage(msg);\n      }\n      CLog::Log(LOGINFO, "Infinity Fold Test: configuration surface {}x{}", width, height);\n    }\n  }\n}\n'''
if old_cfg not in text:
    raise SystemExit('onConfigurationChanged anchor not found')
text = text.replace(old_cfg, new_cfg, 1)

old_resize = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  m_window.reset();\n  // no need to do anything because we are fixed in fullscreen landscape mode\n}\n'''
new_resize = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: Infinity Fold Test window resized", __PRETTY_FUNCTION__);\n  m_window.reset();\n\n  const auto nativeWindow = GetNativeWindow(2000);\n  if (!nativeWindow || !CServiceBroker::GetWinSystem())\n    return;\n\n  const int width = nativeWindow->GetWidth();\n  const int height = nativeWindow->GetHeight();\n  if (width <= 0 || height <= 0)\n    return;\n\n  auto& gfx = CServiceBroker::GetWinSystem()->GetGfxContext();\n  RESOLUTION_INFO res = gfx.GetResInfo();\n  res.iWidth = width;\n  res.iHeight = height;\n  res.iScreenWidth = width;\n  res.iScreenHeight = height;\n  res.fPixelRatio = 1.0f;\n  gfx.SetResInfo(res);\n\n  if (CServiceBroker::GetGUI())\n  {\n    CGUIMessage msg(GUI_MSG_WINDOW_RESIZE, 0, 0, width, height);\n    CServiceBroker::GetGUI()->GetWindowManager().SendMessage(msg);\n  }\n\n  CLog::Log(LOGINFO, "Infinity Fold Test: resized native surface to {}x{}", width, height);\n}\n'''
if old_resize not in text:
    raise SystemExit('onResizeWindow anchor not found')
text = text.replace(old_resize, new_resize, 1)

old_focus = '''void CXBMCApp::onLostFocus()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n  m_hasFocus = false;\n}\n'''
new_focus = '''void CXBMCApp::onLostFocus()\n{\n  android_printf("%s: Infinity Fold Test lost focus; keeping playback pipeline alive", __PRETTY_FUNCTION__);\n  m_hasFocus = false;\n  // Deliberately do not stop or pause playback here. Android multi-window can\n  // move interaction focus to the other pane while Kodi remains visible.\n}\n'''
if old_focus not in text:
    raise SystemExit('onLostFocus anchor not found')
text = text.replace(old_focus, new_focus, 1)

src.write_text(text)
print('Applied Infinity Fold/Multitask native test patch (no PiP renderer/silver-line patch)')
