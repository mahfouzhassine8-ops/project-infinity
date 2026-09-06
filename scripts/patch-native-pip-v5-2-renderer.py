from pathlib import Path
import re

src = Path('/tmp/xbmc/xbmc/cores/VideoPlayer/VideoRenderers/LinuxRendererGLES.cpp')
text = src.read_text()

include_anchor = '#include "windowing/WinSystem.h"\n'
include_insert = '#include "windowing/WinSystem.h"\n#if defined(TARGET_ANDROID)\n#include "platform/android/activity/XBMCApp.h"\n#endif\n'
if include_anchor not in text:
    raise SystemExit('Could not locate WinSystem include anchor')
text = text.replace(include_anchor, include_insert, 1)

old = '''void CLinuxRendererGLES::Render(unsigned int flags, int index)\n{\n  // obtain current field, if interlaced\n'''
new = '''void CLinuxRendererGLES::Render(unsigned int flags, int index)\n{\n#if defined(TARGET_ANDROID)\n  // Infinity PiP v5.2: renderer-only surface scaling.\n  // Do not mutate CGraphicContext or window state from Android callbacks.\n  // Instead, while the video renderer is active on Kodi's render thread,\n  // compare the real ANativeWindow size with Kodi's cached graphics size and\n  // temporarily map the video quad into the actual PiP surface coordinates.\n  bool infinityPipScaled = false;\n  int infinitySurfaceWidth = 0;\n  int infinitySurfaceHeight = 0;\n  const int infinityGfxWidth = CServiceBroker::GetWinSystem()->GetGfxContext().GetWidth();\n  const int infinityGfxHeight = CServiceBroker::GetWinSystem()->GetGfxContext().GetHeight();\n\n  auto infinityWindow = CXBMCApp::Get().GetNativeWindow(0);\n  if (infinityWindow)\n  {\n    infinitySurfaceWidth = infinityWindow->GetWidth();\n    infinitySurfaceHeight = infinityWindow->GetHeight();\n\n    if (infinitySurfaceWidth > 0 && infinitySurfaceHeight > 0 &&\n        infinityGfxWidth > 0 && infinityGfxHeight > 0 &&\n        (infinitySurfaceWidth != infinityGfxWidth || infinitySurfaceHeight != infinityGfxHeight))\n    {\n      const float scaleX = static_cast<float>(infinitySurfaceWidth) /\n                           static_cast<float>(infinityGfxWidth);\n      const float scaleY = static_cast<float>(infinitySurfaceHeight) /\n                           static_cast<float>(infinityGfxHeight);\n\n      saveRotatedCoords();\n      for (int i = 0; i < 4; ++i)\n      {\n        m_rotatedDestCoords[i].x *= scaleX;\n        m_rotatedDestCoords[i].y *= scaleY;\n      }\n\n      glViewport(0, 0, infinitySurfaceWidth, infinitySurfaceHeight);\n      glScissor(0, 0, infinitySurfaceWidth, infinitySurfaceHeight);\n      infinityPipScaled = true;\n\n      CLog::Log(LOGDEBUG,\n                "Infinity PiP renderer surface map {}x{} -> {}x{}",\n                infinityGfxWidth, infinityGfxHeight,\n                infinitySurfaceWidth, infinitySurfaceHeight);\n    }\n  }\n#endif\n\n  // obtain current field, if interlaced\n'''
if old not in text:
    raise SystemExit('Could not locate CLinuxRendererGLES::Render start')
text = text.replace(old, new, 1)

old_end = '''\n  AfterRenderHook(index);\n}\n\nvoid CLinuxRendererGLES::RenderSinglePass'''
new_end = '''\n  AfterRenderHook(index);\n\n#if defined(TARGET_ANDROID)\n  if (infinityPipScaled)\n  {\n    restoreRotatedCoords();\n    // Let Kodi's normal render-system state take over on the next pass/frame.\n    CRect viewport;\n    m_renderSystem->GetViewPort(viewport);\n    m_renderSystem->SetViewPort(viewport);\n  }\n#endif\n}\n\nvoid CLinuxRendererGLES::RenderSinglePass'''
if old_end not in text:
    raise SystemExit('Could not locate CLinuxRendererGLES::Render end')
text = text.replace(old_end, new_end, 1)

src.write_text(text)
print('Applied Infinity PiP v5.2 renderer-only scaling patch to Kodi 21.2')
