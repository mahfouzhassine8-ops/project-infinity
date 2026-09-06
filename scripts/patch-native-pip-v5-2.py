from pathlib import Path
import re

src = Path('/tmp/xbmc/xbmc/platform/android/activity/XBMCApp.cpp')
text = src.read_text()

old_resize = r'''void CXBMCApp::onResizeWindow\(\)\n\{\n  android_printf\([^\n]*\);\n  m_window\.reset\(\);\n  // no need to do anything because we are fixed in fullscreen landscape mode\n\}'''
new_resize = '''void CXBMCApp::onResizeWindow()\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n\n  // Infinity PiP v5.2: Android also emits resize events while first-run\n  // permission dialogs are being dismissed. PiP resize handling is only\n  // needed while an actual video is playing, so do not touch Kodi graphics\n  // during setup, permission flow, or ordinary non-video UI transitions.\n  const bool videoPlaying =\n      (m_playback_state & PLAYBACK_STATE_PLAYING) &&\n      (m_playback_state & PLAYBACK_STATE_VIDEO);\n  if (!videoPlaying)\n  {\n    CLog::Log(LOGDEBUG, "Infinity PiP: ignoring native resize because no video is playing");\n    return;\n  }\n\n  if (!g_application.IsInitialized() || !CServiceBroker::GetWinSystem())\n  {\n    CLog::Log(LOGDEBUG, "Infinity PiP: ignoring native resize before Kodi graphics init");\n    return;\n  }\n\n  if (m_window)\n  {\n    const int width = m_window->GetWidth();\n    const int height = m_window->GetHeight();\n    if (width <= 0 || height <= 0)\n      return;\n\n    auto& gfx = CServiceBroker::GetWinSystem()->GetGfxContext();\n    if (gfx.GetWidth() == width && gfx.GetHeight() == height)\n    {\n      CLog::Log(LOGDEBUG, "Infinity PiP: ignoring unchanged native resize {}x{}", width, height);\n      return;\n    }\n\n    CLog::Log(LOGDEBUG, "Infinity PiP native window resized to {}x{} during video playback", width, height);\n    gfx.ApplyWindowResize(width, height);\n  }\n}'''
text, n = re.subn(old_resize, new_resize, text, count=1)
if n != 1:
    raise SystemExit('Could not patch CXBMCApp::onResizeWindow')

old_surface = r'''void CXBMCApp::surfaceChanged\(CJNISurfaceHolder holder, int format, int width, int height\)\n\{\n  android_printf\([^\n]*\);\n\}'''
new_surface = '''void CXBMCApp::surfaceChanged(CJNISurfaceHolder holder, int format, int width, int height)\n{\n  android_printf("%s: ", __PRETTY_FUNCTION__);\n\n  // Same rule for the authoritative SurfaceView callback: only propagate\n  // geometry changes into Kodi's renderer while video playback is active.\n  // This prevents storage-permission/dialog resize noise from reaching the\n  // graphics subsystem at all.\n  const bool videoPlaying =\n      (m_playback_state & PLAYBACK_STATE_PLAYING) &&\n      (m_playback_state & PLAYBACK_STATE_VIDEO);\n  if (!videoPlaying)\n  {\n    CLog::Log(LOGDEBUG, "Infinity PiP: ignoring SurfaceView resize because no video is playing");\n    return;\n  }\n\n  if (!g_application.IsInitialized() || !CServiceBroker::GetWinSystem())\n  {\n    CLog::Log(LOGDEBUG, "Infinity PiP: ignoring SurfaceView resize before Kodi graphics init");\n    return;\n  }\n\n  if (width <= 0 || height <= 0)\n    return;\n\n  auto& gfx = CServiceBroker::GetWinSystem()->GetGfxContext();\n  if (gfx.GetWidth() == width && gfx.GetHeight() == height)\n  {\n    CLog::Log(LOGDEBUG, "Infinity PiP: ignoring unchanged SurfaceView resize {}x{}", width, height);\n    return;\n  }\n\n  CLog::Log(LOGDEBUG, "Infinity PiP SurfaceView changed to {}x{} during video playback", width, height);\n  gfx.ApplyWindowResize(width, height);\n}'''
text, n = re.subn(old_surface, new_surface, text, count=1)
if n != 1:
    raise SystemExit('Could not patch CXBMCApp::surfaceChanged')

src.write_text(text)
print('Applied Infinity PiP v5.2 playback-gated native resize patch to Kodi 21.2')
