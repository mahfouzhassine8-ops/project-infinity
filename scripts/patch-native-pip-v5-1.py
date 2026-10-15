from pathlib import Path
import re

src = Path('/tmp/xbmc/xbmc/platform/android/activity/XBMCApp.cpp')
text = src.read_text()

old_resize = r'''void CXBMCApp::onResizeWindow\(\)\n\{\n  android_printf\([^\n]*\);\n  m_window\.reset\(\);\n  // no need to do anything because we are fixed in fullscreen landscape mode\n\}'''
new_resize = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n\n  // Infinity PiP v5.1: resize events can also fire while first-run dialogs\n  // (including storage permission) are being dismissed. Do not touch Kodi's\n  // graphics state until the application and window system are initialized.\n  if (!g_application.IsInitialized() || !CServiceBroker::GetWinSystem())\n  {\n    CLog::Log(LOGDEBUG, "Infinity PiP: ignoring native resize before Kodi graphics init");\n    return;\n  }\n\n  if (m_window)\n  {\n    const int width = m_window->GetWidth();\n    const int height = m_window->GetHeight();\n    if (width <= 0 || height <= 0)\n      return;\n\n    auto& gfx = CServiceBroker::GetWinSystem()->GetGfxContext();\n    if (gfx.GetWidth() == width && gfx.GetHeight() == height)\n    {\n      CLog::Log(LOGDEBUG, "Infinity PiP: ignoring unchanged native resize {}x{}", width, height);\n      return;\n    }\n\n    CLog::Log(LOGDEBUG, "Infinity PiP native window resized to {}x{}", width, height);\n    gfx.ApplyWindowResize(width, height);\n  }\n}'''
text, n = re.subn(old_resize, new_resize, text, count=1)
if n != 1:
    raise SystemExit('Could not patch CXBMCApp::onResizeWindow')

old_surface = r'''void CXBMCApp::surfaceChanged\(CJNISurfaceHolder holder, int format, int width, int height\)\n\{\n  android_printf\([^\n]*\);\n\}'''
new_surface = '''void CXBMCApp::surfaceChanged(CJNISurfaceHolder holder, int format, int width, int height)\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n\n  // The SurfaceView callback also fires around permission/activity transitions.\n  // Guard early lifecycle events and ignore no-op geometry notifications. Only\n  // a real post-init size change (such as entering native PiP) reaches Kodi's\n  // existing ApplyWindowResize path.\n  if (!g_application.IsInitialized() || !CServiceBroker::GetWinSystem())\n  {\n    CLog::Log(LOGDEBUG, "Infinity PiP: ignoring SurfaceView resize before Kodi graphics init");\n    return;\n  }\n\n  if (width <= 0 || height <= 0)\n    return;\n\n  auto& gfx = CServiceBroker::GetWinSystem()->GetGfxContext();\n  if (gfx.GetWidth() == width && gfx.GetHeight() == height)\n  {\n    CLog::Log(LOGDEBUG, "Infinity PiP: ignoring unchanged SurfaceView resize {}x{}", width, height);\n    return;\n  }\n\n  CLog::Log(LOGDEBUG, "Infinity PiP SurfaceView changed to {}x{}", width, height);\n  gfx.ApplyWindowResize(width, height);\n}'''
text, n = re.subn(old_surface, new_surface, text, count=1)
if n != 1:
    raise SystemExit('Could not patch CXBMCApp::surfaceChanged')

src.write_text(text)
print('Applied Infinity PiP v5.1 guarded native resize patch to Kodi 21.2')
