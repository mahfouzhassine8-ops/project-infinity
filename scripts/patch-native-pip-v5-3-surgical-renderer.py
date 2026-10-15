from pathlib import Path

src = Path('/tmp/xbmc/xbmc/cores/VideoPlayer/VideoRenderers/LinuxRendererGLES.cpp')
text = src.read_text()

# Strategy B from the v5.3 investigation: touch only the active video renderer.
# Do not patch XBMCApp.cpp, CGraphicContext, window-resize callbacks, permissions,
# storage lifecycle, or JNI registration.
include_anchor = '#include "windowing/WinSystem.h"\n'
include_insert = '''#include "windowing/WinSystem.h"\n#if defined(TARGET_ANDROID)\n#include "platform/android/activity/XBMCApp.h"\n#endif\n'''
if include_anchor not in text:
    raise SystemExit('Could not locate WinSystem include anchor')
text = text.replace(include_anchor, include_insert, 1)

render_anchor = '''void CLinuxRendererGLES::Render(unsigned int flags, int index)\n{\n  // obtain current field, if interlaced\n'''
render_insert = '''void CLinuxRendererGLES::Render(unsigned int flags, int index)\n{\n#if defined(TARGET_ANDROID)\n  // Infinity PiP v5.3 - surgical renderer bypass.\n  // This runs only while decoded video frames are being rendered. It never\n  // executes during startup, storage permission handling, Activity.onResume(),\n  // APP_CMD_RESUME, or native window-resize dispatch.\n  bool infinityPipSurfaceActive = false;\n  CRect infinitySavedDestRect = m_destRect;\n  int infinitySurfaceWidth = 0;\n  int infinitySurfaceHeight = 0;\n\n  // Query the real Android native surface that backs EGL. In Kodi 21.2,\n  // CLinuxRendererGLES does not own EGLDisplay/EGLSurface members directly,\n  // so the native window dimensions are the renderer-safe equivalent of the\n  // investigation's eglQuerySurface(EGL_WIDTH/EGL_HEIGHT) step.\n  auto infinityWindow = CXBMCApp::Get().GetNativeWindow(0);\n  if (infinityWindow)\n  {\n    infinitySurfaceWidth = infinityWindow->GetWidth();\n    infinitySurfaceHeight = infinityWindow->GetHeight();\n\n    const int infinityGfxWidth =\n        CServiceBroker::GetWinSystem()->GetGfxContext().GetWidth();\n    const int infinityGfxHeight =\n        CServiceBroker::GetWinSystem()->GetGfxContext().GetHeight();\n\n    // Detect the PiP case by requiring a valid surface that has physically\n    // shrunk below Kodi's still-cached full-screen graphics dimensions.\n    if (infinitySurfaceWidth > 0 && infinitySurfaceHeight > 0 &&\n        infinityGfxWidth > 0 && infinityGfxHeight > 0 &&\n        infinitySurfaceWidth < infinityGfxWidth &&\n        infinitySurfaceHeight < infinityGfxHeight)\n    {\n      infinityPipSurfaceActive = true;\n\n      // Match OpenGL to the TRUE PiP surface bounds.\n      glViewport(0, 0, infinitySurfaceWidth, infinitySurfaceHeight);\n\n      // Override the video destination rectangle to the PiP surface instead\n      // of projecting it against CGraphicContext's cached full-screen size.\n      m_destRect.SetRect(0.0f, 0.0f,\n                         static_cast<float>(infinitySurfaceWidth),\n                         static_cast<float>(infinitySurfaceHeight));\n\n      // LinuxRendererGLES draws from m_rotatedDestCoords, so keep those draw\n      // vertices synchronized with the temporary destination rectangle.\n      saveRotatedCoords();\n      m_rotatedDestCoords[0] = CPoint(m_destRect.x1, m_destRect.y1);\n      m_rotatedDestCoords[1] = CPoint(m_destRect.x2, m_destRect.y1);\n      m_rotatedDestCoords[2] = CPoint(m_destRect.x2, m_destRect.y2);\n      m_rotatedDestCoords[3] = CPoint(m_destRect.x1, m_destRect.y2);\n\n      CLog::Log(LOGDEBUG,\n                "Infinity PiP v5.3 renderer surface {}x{} (cached GUI {}x{})",\n                infinitySurfaceWidth, infinitySurfaceHeight,\n                infinityGfxWidth, infinityGfxHeight);\n    }\n  }\n#endif\n\n  // obtain current field, if interlaced\n'''
if render_anchor not in text:
    raise SystemExit('Could not locate CLinuxRendererGLES::Render start')
text = text.replace(render_anchor, render_insert, 1)

end_anchor = '''\n  AfterRenderHook(index);\n}\n\nvoid CLinuxRendererGLES::RenderSinglePass'''
end_insert = '''\n  AfterRenderHook(index);\n\n#if defined(TARGET_ANDROID)\n  if (infinityPipSurfaceActive)\n  {\n    // Restore Kodi's normal renderer state after this frame. No persistent\n    // global graphics/window mutation is left behind.\n    restoreRotatedCoords();\n    m_destRect = infinitySavedDestRect;\n  }\n#endif\n}\n\nvoid CLinuxRendererGLES::RenderSinglePass'''
if end_anchor not in text:
    raise SystemExit('Could not locate CLinuxRendererGLES::Render end')
text = text.replace(end_anchor, end_insert, 1)

src.write_text(text)
print('Applied Infinity PiP v5.3 surgical renderer patch to Kodi 21.2')
