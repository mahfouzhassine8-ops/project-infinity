#!/usr/bin/env python3
"""Evidence-only native GUI heartbeat and real native cleanup milestone."""
from pathlib import Path
import argparse,hashlib,json
from native_controls import once
HERE=Path(__file__).resolve().parent

def apply(root):
    changes=[]
    def change(name,fn):
        p=root/name;before=p.read_bytes() if p.exists() else b'';after=fn(before.decode()).encode()
        p.write_bytes(after);changes.append({'path':name,'before':hashlib.sha256(before).hexdigest() if before else None,
                                           'after':hashlib.sha256(after).hexdigest()})
    change('xbmc/platform/android/activity/InfinityResponsiveness.h',lambda _:(HERE/'InfinityResponsiveness.h').read_text())
    def manager(s):
        s=once(s,'#include "GUIWindowManager.h"', '#include "GUIWindowManager.h"\n#if defined(TARGET_ANDROID)\n#include "addons/Skin.h"\n#include "platform/android/activity/InfinityResponsiveness.h"\n#endif')
        old='''  for (auto& itr : m_dirtyregions)
    m_tracker.MarkDirtyRegion(itr);
}'''
        new=old[:-1]+'''
#if defined(TARGET_ANDROID)
  // Publish on the GUI owner thread. Watchdogs read only these atomics: no GUI
  // calls, renderer locks, JNI View access or JSON-RPC on the observer thread.
  const int64_t now = InfinityHealth::UptimeMillis();
  static const int64_t sessionStart = now;
  static int64_t lastPublished = 0;
  if (now - lastPublished >= 500)
  {
    lastPublished = now;
    const auto appPlayer = CServiceBroker::GetAppComponents().GetComponent<CApplicationPlayer>();
    const auto* home = GetWindow(WINDOW_HOME);
    const auto* background = home ? home->GetControl(29900) : nullptr;
    const int flags = appPlayer ? (appPlayer->IsPlayingVideo() ? 1 : 0) |
        (appPlayer->IsPlayingAudio() ? 2 : 0) | (appPlayer->IsPausedPlayback() ? 4 : 0) : 0;
    const auto& gfx = CServiceBroker::GetWinSystem()->GetGfxContext();
    const auto* active = GetWindow(GetActiveWindow());
    const int lw = active ? active->GetCoordsRes().iWidth : 0;
    const int lh = active ? active->GetCoordsRes().iHeight : 0;
    const int aspect = lh <= 0 ? 0 : lw * 100 < lh * 80 ? 1 : lw * 100 > lh * 125 ? 3 : 2;
    const uint64_t requested = InfinityHealth::requestedGeometry.load();
    const uint64_t committed = InfinityHealth::committedGeometry.load();
    InfinityHealth::Publish({1, now, GetActiveWindow(), GetTopmostDialog(), flags,
        GetActiveWindow() == WINDOW_HOME && background && background->IsVisible() ? 1 : 0,
        home && home->GetProperty("Infinity.NativeAmbient.Active").asString() == "true" ? 1 : 0,
        gfx.GetWidth(), gfx.GetHeight(), lw, lh, InfinityHealth::skinGeneration.load(),
        aspect, sessionStart, int(requested >> 32), int(uint32_t(requested)),
        int(committed >> 32), int(uint32_t(committed)), InfinityHealth::windowGeneration.load(),
        InfinityHealth::requestedAt.load(), InfinityHealth::committedAt.load(),
        g_SkinInfo && g_SkinInfo->ID() == "skin.infinity.diggz" ? 1 : 0});
  }
#endif
}'''
        return once(s,old,new)
    change('xbmc/guilib/GUIWindowManager.cpp',manager)
    def geometry(s):
        s=once(s,'#include "WinSystemAndroidGLESContext.h"',
            '#include "WinSystemAndroidGLESContext.h"\n#include "platform/android/activity/InfinityResponsiveness.h"')
        s=once(s,'  m_pGLContext.DestroySurface();\n\n  if (!CWinSystemAndroid::CreateNewWindow',
            '  InfinityHealth::ClearGeometry();\n  InfinityHealth::RequestGeometry(res.iWidth, res.iHeight);\n  m_pGLContext.DestroySurface();\n\n  if (!CWinSystemAndroid::CreateNewWindow')
        s=once(s,'''  if (!m_pGLContext.BindContext())
  {
    return false;
  }

  return true;''','''  if (!m_pGLContext.BindContext())
  {
    return false;
  }
  InfinityHealth::CommitGeometry(res.iWidth, res.iHeight);
  return true;''')
        s=once(s,'''  CRenderSystemGLES::ResetRenderSystem(newWidth, newHeight);
  return true;''','''  InfinityHealth::RequestGeometry(newWidth, newHeight);
  const bool accepted = CRenderSystemGLES::ResetRenderSystem(newWidth, newHeight);
  if (accepted) InfinityHealth::CommitGeometry(newWidth, newHeight);
  return accepted;''')
        return s
    change('xbmc/windowing/android/WinSystemAndroidGLESContext.cpp',geometry)
    def clear_geometry(s):
        s=once(s,'#include "WinSystemAndroid.h"',
            '#include "WinSystemAndroid.h"\n#include "platform/android/activity/InfinityResponsiveness.h"')
        return once(s,'  m_nativeWindow.reset();\n  m_bWindowCreated = false;',
            '  InfinityHealth::ClearGeometry();\n  m_nativeWindow.reset();\n  m_bWindowCreated = false;')
    change('xbmc/windowing/android/WinSystemAndroid.cpp',clear_geometry)
    change('xbmc/addons/Skin.cpp',lambda s:once(once(s,'#include "Skin.h"',
        '#include "Skin.h"\n#if defined(TARGET_ANDROID)\n#include "platform/android/activity/InfinityResponsiveness.h"\n#endif'),
        'void CSkinInfo::Start()\n{','void CSkinInfo::Start()\n{\n#if defined(TARGET_ANDROID)\n  ++InfinityHealth::skinGeneration;\n#endif'))
    change('xbmc/platform/android/activity/JNIMainActivity.h',lambda s:once(s,
        '  static void _doFrame(JNIEnv *env, jobject context, jlong frameTimeNanos);',
        '  static void _doFrame(JNIEnv *env, jobject context, jlong frameTimeNanos);\n  static jlongArray _infinityHeartbeat(JNIEnv* env, jclass);'))
    def jni(s):
        s=once(s,'#include "JNIMainActivity.h"','#include "JNIMainActivity.h"\n#include "InfinityResponsiveness.h"')
        s=once(s,'        {"_doFrame", "(J)V", reinterpret_cast<void*>(&CJNIMainActivity::_doFrame)},',
                    '        {"_doFrame", "(J)V", reinterpret_cast<void*>(&CJNIMainActivity::_doFrame)},\n        {"_infinityHeartbeat", "()[J", reinterpret_cast<void*>(&CJNIMainActivity::_infinityHeartbeat)},')
        return once(s,'CJNIRect CJNIMainActivity::getDisplayRect()', '''jlongArray CJNIMainActivity::_infinityHeartbeat(JNIEnv* env, jclass)
{
  std::array<int64_t,InfinityHealth::FIELD_COUNT> snapshot{};
  if (!InfinityHealth::Read(snapshot)) return nullptr;
  jlongArray result = env->NewLongArray(snapshot.size());
  if (result) env->SetLongArrayRegion(result,0,snapshot.size(),reinterpret_cast<const jlong*>(snapshot.data()));
  return result;
}

CJNIRect CJNIMainActivity::getDisplayRect()''')
    change('xbmc/platform/android/activity/JNIMainActivity.cpp',jni)
    def cleanup(s):
        s=once(s,'#include <thread>','#include <thread>\n#include <fstream>\n#include <chrono>\n#include <cstdio>')
        s=once(s,'extern void android_main(struct android_app* state)\n{',
        '''extern void android_main(struct android_app* state)
{
  // Copy the pathname while ANativeActivity still owns its storage.
  const std::string cleanupPath = state && state->activity && state->activity->internalDataPath
      ? std::string(state->activity->internalDataPath) + "/infinity-native-cleanup.json" : "";''')
        return once(s,'    CXBMCApp::Destroy();\n  }', '''    CXBMCApp::Destroy();
    // NativeActivity's Java onDestroy need not return: this function exits the
    // process below. Record the actual completion after Destroy, before exit(0).
    if (!cleanupPath.empty())
    {
      const std::string temporary = cleanupPath + ".tmp";
      std::ofstream record(temporary,std::ios::trunc);
      const auto epoch = std::chrono::duration_cast<std::chrono::milliseconds>(
          std::chrono::system_clock::now().time_since_epoch()).count();
      record << "{\\"schema\\":1,\\"milestone\\":\\"native.CXBMCApp.Destroy.complete\\",\\"pid\\":"
             << getpid() << ",\\"epoch_ms\\":" << epoch << "}\\n";
      record.flush();
      const bool written = record.good();
      record.close();
      if (written && std::rename(temporary.c_str(),cleanupPath.c_str()) == 0)
        CXBMCApp::android_printf("Infinity native cleanup completion persisted");
    }
  }''')
    change('xbmc/platform/android/activity/android_main.cpp',cleanup)
    return changes

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    a.receipt.write_text(json.dumps({'changes':apply(a.source),'evidence_only':True},indent=2)+'\n')
