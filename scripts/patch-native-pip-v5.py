from pathlib import Path
import re

src = Path('/tmp/xbmc/xbmc/platform/android/activity/XBMCApp.cpp')
text = src.read_text()

old_resize = r'''void CXBMCApp::onResizeWindow\(\)\n\{\n  android_printf\([^\n]*\);\n  m_window\.reset\(\);\n  // no need to do anything because we are fixed in fullscreen landscape mode\n\}'''
new_resize = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n\n  // Infinity PiP: Android can resize the existing ANativeWindow without\n  // recreating it. Kodi 21.2 historically ignored this because Android\n  // was assumed to stay fixed fullscreen. Synchronize Kodi's internal\n  // graphics coordinate space with the real native window dimensions.\n  if (m_window)\n  {\n    const int width = m_window->GetWidth();\n    const int height = m_window->GetHeight();\n    if (width > 0 && height > 0 && CServiceBroker::GetWinSystem())\n    {\n      CLog::Log(LOGDEBUG, "Infinity PiP native window resized to {}x{}", width, height);\n      CServiceBroker::GetWinSystem()->GetGfxContext().ApplyWindowResize(width, height);\n    }\n  }\n}'''
text, n = re.subn(old_resize, new_resize, text, count=1)
if n != 1:
    raise SystemExit('Could not patch CXBMCApp::onResizeWindow')

old_surface = r'''void CXBMCApp::surfaceChanged\(CJNISurfaceHolder holder, int format, int width, int height\)\n\{\n  android_printf\([^\n]*\);\n\}'''
new_surface = '''void CXBMCApp::surfaceChanged(CJNISurfaceHolder holder, int format, int width, int height)\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n\n  // The Java SurfaceView callback contains the authoritative PiP surface\n  // dimensions. Push them through Kodi's existing window-resize path so\n  // CGraphicContext, the render system and video destination rectangles\n  // are recalculated for the small PiP viewport.\n  if (width > 0 && height > 0 && CServiceBroker::GetWinSystem())\n  {\n    CLog::Log(LOGDEBUG, "Infinity PiP SurfaceView changed to {}x{}", width, height);\n    CServiceBroker::GetWinSystem()->GetGfxContext().ApplyWindowResize(width, height);\n  }\n}'''
text, n = re.subn(old_surface, new_surface, text, count=1)
if n != 1:
    raise SystemExit('Could not patch CXBMCApp::surfaceChanged')

src.write_text(text)
print('Applied Infinity PiP v5 native resize patch to Kodi 21.2')
