/*
 *  Copyright (C) 2015-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "JNIMainActivity.h"
#include "InfinityAndroidCheckpoint.h"
#include "InfinityResponsiveness.h"
#include "AndroidTouch.h"

#include "CompileInfo.h"
#include "InfinityBridgeState.h"

#include <androidjni/Build.h>
#include <androidjni/JNIThreading.h>

#include <androidjni/Activity.h>
#include <androidjni/Intent.h>
#include <androidjni/jutils-details.hpp>

using namespace jni;

CJNIMainActivity* CJNIMainActivity::m_appInstance(NULL);

namespace
{
std::string CheckpointJniString(JNIEnv* env, jstring value)
{
  if (!value)
    return {};
  const char* bytes = env->GetStringUTFChars(value, nullptr);
  if (!bytes)
    return {};
  const std::string result(bytes);
  env->ReleaseStringUTFChars(value, bytes);
  return result;
}
}

jboolean CJNIMainActivity::_infinityRequestPersistenceCheckpoint(
    JNIEnv* env, jobject, jstring session, jstring owner, jint pid)
{
  return InfinityAndroidCheckpoint::Request(CheckpointJniString(env, session),
                                            CheckpointJniString(env, owner), pid) ? JNI_TRUE : JNI_FALSE;
}

jstring CJNIMainActivity::_infinityPersistenceCheckpointStatus(
    JNIEnv* env, jobject, jstring session, jstring owner, jint pid)
{
  const auto status = InfinityAndroidCheckpoint::Status(CheckpointJniString(env, session),
                                                       CheckpointJniString(env, owner), pid);
  return env->NewStringUTF(status.c_str());
}

jboolean CJNIMainActivity::_infinityAuthorizeCheckpointTermination(
    JNIEnv* env, jobject, jstring session, jstring owner, jint pid)
{
  return InfinityAndroidCheckpoint::AuthorizeTermination(CheckpointJniString(env, session),
                                                        CheckpointJniString(env, owner), pid) ? JNI_TRUE : JNI_FALSE;
}

CJNIMainActivity::CJNIMainActivity(const ANativeActivity *nativeActivity)
  : CJNIActivity(nativeActivity)
{
  m_appInstance = this;
}

CJNIMainActivity::~CJNIMainActivity()
{
  m_appInstance = NULL;
}

void CJNIMainActivity::RegisterNatives(JNIEnv* env)
{
  std::string pkgRoot = CCompileInfo::GetClass();

  const std::string mainClass = pkgRoot + "/Main";
  const std::string settingsObserver = pkgRoot + "/XBMCSettingsContentObserver";
  const std::string inputDeviceListener = pkgRoot + "/XBMCInputDeviceListener";

  jclass cMain = env->FindClass(mainClass.c_str());
  if (cMain)
  {
    JNINativeMethod methods[] = {
        {"infinityRequestPersistenceCheckpoint", "(Ljava/lang/String;Ljava/lang/String;I)Z",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityRequestPersistenceCheckpoint)},
        {"infinityPersistenceCheckpointStatus", "(Ljava/lang/String;Ljava/lang/String;I)Ljava/lang/String;",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityPersistenceCheckpointStatus)},
        {"infinityAuthorizeCheckpointTermination", "(Ljava/lang/String;Ljava/lang/String;I)Z",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityAuthorizeCheckpointTermination)},
        {"_onNewIntent", "(Landroid/content/Intent;)V",
         reinterpret_cast<void*>(&CJNIMainActivity::_onNewIntent)},
        {"_onActivityResult", "(IILandroid/content/Intent;)V",
         reinterpret_cast<void*>(&CJNIMainActivity::_onActivityResult)},
        {"_doFrame", "(J)V", reinterpret_cast<void*>(&CJNIMainActivity::_doFrame)},
        {"_infinityHeartbeat", "()[J", reinterpret_cast<void*>(&CJNIMainActivity::_infinityHeartbeat)},
        {"_callNative", "(JJ)V", reinterpret_cast<void*>(&CJNIMainActivity::_callNative)},
        {"_onVisibleBehindCanceled", "()V",
         reinterpret_cast<void*>(&CJNIMainActivity::_onVisibleBehindCanceled)},
        {"_infinityHasActiveVideo", "()Z",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityHasActiveVideo)},
        {"_infinitySyncDisplayState", "()V",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinitySyncDisplayState)},
        {"_infinitySystemThemeMode", "()I",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinitySystemThemeMode)},
        {"_infinityWindowWidth", "()I",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityWindowWidth)},
        {"_infinityWindowHeight", "()I",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityWindowHeight)},
        {"_infinityBridgeVersion", "()I",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityBridgeVersion)},
        {"_infinityCanEnterPictureInPicture", "()Z",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityCanEnterPictureInPicture)},
        {"_infinityVideoAspectRatio", "()F",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityVideoAspectRatio)},
        {"_infinityWindowMode", "()I",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityWindowMode)},
        {"_infinityGetState", "()[J",
         reinterpret_cast<void*>(&CJNIMainActivity::_infinityGetState)},
    };
    env->RegisterNatives(cMain, methods, sizeof(methods) / sizeof(methods[0]));
  }

  jclass cSettingsObserver = env->FindClass(settingsObserver.c_str());
  if (cSettingsObserver)
  {
    JNINativeMethod methods[] = {
        {"_onVolumeChanged", "(I)V", reinterpret_cast<void*>(&CJNIMainActivity::_onVolumeChanged)},
    };
    env->RegisterNatives(cSettingsObserver, methods, sizeof(methods) / sizeof(methods[0]));
  }

  jclass cInputDeviceListener = env->FindClass(inputDeviceListener.c_str());
  if (cInputDeviceListener)
  {
    JNINativeMethod methods[] = {
        {"_onInputDeviceAdded", "(I)V",
         reinterpret_cast<void*>(&CJNIMainActivity::_onInputDeviceAdded)},
        {"_onInputDeviceChanged", "(I)V",
         reinterpret_cast<void*>(&CJNIMainActivity::_onInputDeviceChanged)},
        {"_onInputDeviceRemoved", "(I)V",
         reinterpret_cast<void*>(&CJNIMainActivity::_onInputDeviceRemoved)}};
    env->RegisterNatives(cInputDeviceListener, methods, sizeof(methods) / sizeof(methods[0]));
  }
}

void CJNIMainActivity::_onNewIntent(JNIEnv *env, jobject context, jobject intent)
{
  (void)env;
  (void)context;
  if (m_appInstance)
    m_appInstance->onNewIntent(CJNIIntent(jhobject::fromJNI(intent)));
}

void CJNIMainActivity::_onActivityResult(JNIEnv *env, jobject context, jint requestCode, jint resultCode, jobject resultData)
{
  (void)env;
  (void)context;
  if (m_appInstance)
    m_appInstance->onActivityResult(requestCode, resultCode, CJNIIntent(jhobject::fromJNI(resultData)));
}

void CJNIMainActivity::_callNative(JNIEnv *env, jobject context, jlong funcAddr, jlong variantAddr)
{
  (void)env;
  (void)context;
  ((void (*)(CVariant *))funcAddr)((CVariant *)variantAddr);
}

namespace
{
// Optional bridge calls fail closed, with no JNI exception left pending.
bool InfinityClearException(JNIEnv* env)
{
  if (env && env->ExceptionCheck())
  {
    env->ExceptionDescribe();
    env->ExceptionClear();
    return true;
  }
  return false;
}

jint InfinityReadIntSnapshot(JNIEnv* env, jobject context, const char* method)
{
  if (!env || !context)
    return 0;
  jclass cls = env->GetObjectClass(context);
  if (InfinityClearException(env) || !cls)
    return 0;
  const jmethodID id = env->GetMethodID(cls, method, "()I");
  env->DeleteLocalRef(cls);
  if (InfinityClearException(env) || !id)
    return 0;
  const jint value = env->CallIntMethod(context, id);
  return InfinityClearException(env) ? 0 : value;
}
} // namespace

jboolean CJNIMainActivity::_infinityHasActiveVideo(JNIEnv* env, jobject context)
{
  (void)env;
  (void)context;
  return m_appInstance ? m_appInstance->infinityHasActiveVideo() : JNI_FALSE;
}

void CJNIMainActivity::_infinitySyncDisplayState(JNIEnv* env, jobject context)
{
  (void)env;
  (void)context;
  if (m_appInstance)
    m_appInstance->infinitySyncDisplayStateFromBridge();
}

jint CJNIMainActivity::_infinitySystemThemeMode(JNIEnv* env, jobject context)
{
  return InfinityReadIntSnapshot(env, context, "infinityGetSystemThemeMode");
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
  return CInfinityBridgeState::VERSION;
}

jboolean CJNIMainActivity::_infinityCanEnterPictureInPicture(JNIEnv* env, jobject context)
{
  (void)env;
  (void)context;
  return m_appInstance ? m_appInstance->infinityCanEnterPictureInPicture() : JNI_FALSE;
}

jfloat CJNIMainActivity::_infinityVideoAspectRatio(JNIEnv* env, jobject context)
{
  (void)env;
  (void)context;
  return m_appInstance ? m_appInstance->infinityVideoAspectRatio() : 16.0f / 9.0f;
}

jint CJNIMainActivity::_infinityWindowMode(JNIEnv* env, jobject context)
{
  return InfinityReadIntSnapshot(env, context, "infinityGetWindowMode");
}

jlongArray CJNIMainActivity::_infinityGetState(JNIEnv* env, jobject context)
{
  (void)context;
  if (!env) return nullptr;
  const auto snapshot = m_appInstance ? m_appInstance->infinityGetState() : std::array<int64_t, 16>{};
  jlong values[16];
  for (size_t i = 0; i < 16; ++i) values[i] = static_cast<jlong>(snapshot[i]);
  jlongArray result = env->NewLongArray(16);
  if (!result) return nullptr; // Preserve JVM OOM for the caller; no further JNI calls.
  env->SetLongArrayRegion(result, 0, 16, values);
  return result;
}

int CJNIMainActivity::infinityGetSystemTheme() const
{
  const jint value = call_method<jint>(m_context, "infinityGetSystemThemeMode", "()I");
  return InfinityClearException(xbmc_jnienv()) ? 0 : value;
}

int CJNIMainActivity::infinityGetModeSnapshot() const
{
  const jint value = call_method<jint>(m_context, "infinityGetWindowMode", "()I");
  return InfinityClearException(xbmc_jnienv()) ? 0 : value;
}

void CJNIMainActivity::infinityNotifyPlaybackChanged()
{
  call_method<void>(m_context, "infinityOnPlaybackStateChanged", "()V");
  InfinityClearException(xbmc_jnienv());
}

uint64_t CJNIMainActivity::infinityGetWindowSize() const
{
  const jlong size = call_method<jlong>(m_context, "infinityGetWindowSize", "()J");
  return InfinityClearException(xbmc_jnienv()) ? 0 : static_cast<uint64_t>(size);
}

bool CJNIMainActivity::infinityIsPictureInPicture() const
{
  if (CJNIBuild::SDK_INT < 26)
    return false;
  const jboolean pip = call_method<jboolean>(m_context, "isInPictureInPictureMode", "()Z");
  return !InfinityClearException(xbmc_jnienv()) && pip == JNI_TRUE;
}

void CJNIMainActivity::_onVisibleBehindCanceled(JNIEnv* env, jobject context)
{
  (void)env;
  (void)context;
  if (m_appInstance)
    m_appInstance->onVisibleBehindCanceled();
}

void CJNIMainActivity::runNativeOnUiThread(void (*callback)(void*), void* variant)
{
  call_method<void>(m_context,
                    "runNativeOnUiThread", "(JJ)V", (jlong)callback, (jlong)variant);
}

void CJNIMainActivity::_onVolumeChanged(JNIEnv *env, jobject context, jint volume)
{
  (void)env;
  (void)context;
  if(m_appInstance)
    m_appInstance->onVolumeChanged(volume);
}

void CJNIMainActivity::_onInputDeviceAdded(JNIEnv *env, jobject context, jint deviceId)
{
  static_cast<void>(env);
  static_cast<void>(context);

  if (m_appInstance != nullptr)
    m_appInstance->onInputDeviceAdded(deviceId);
}

void CJNIMainActivity::_onInputDeviceChanged(JNIEnv *env, jobject context, jint deviceId)
{
  static_cast<void>(env);
  static_cast<void>(context);

  if (m_appInstance != nullptr)
    m_appInstance->onInputDeviceChanged(deviceId);
}

void CJNIMainActivity::_onInputDeviceRemoved(JNIEnv *env, jobject context, jint deviceId)
{
  static_cast<void>(env);
  static_cast<void>(context);

  if (m_appInstance != nullptr)
    m_appInstance->onInputDeviceRemoved(deviceId);
}

void CJNIMainActivity::_doFrame(JNIEnv *env, jobject context, jlong frameTimeNanos)
{
  // INFINITY_WINDOW_INPUT_V1: this callback already runs on Android's UI thread.
  CAndroidTouch::RefreshInputViewport(env, context);
  if(m_appInstance)
    m_appInstance->doFrame(frameTimeNanos);
}

jlongArray CJNIMainActivity::_infinityHeartbeat(JNIEnv* env, jclass)
{
  std::array<int64_t,InfinityHealth::FIELD_COUNT> snapshot{};
  if (!InfinityHealth::Read(snapshot)) return nullptr;
  jlongArray result = env->NewLongArray(snapshot.size());
  std::array<jlong,InfinityHealth::FIELD_COUNT> javaValues{};
  for (size_t i = 0; i < snapshot.size(); ++i) javaValues[i] = snapshot[i];
  if (result) env->SetLongArrayRegion(result,0,javaValues.size(),javaValues.data());
  return result;
}

CJNIRect CJNIMainActivity::getDisplayRect()
{
  return call_method<jhobject>(m_context,
                               "getDisplayRect", "()Landroid/graphics/Rect;");
}

void CJNIMainActivity::registerMediaButtonEventReceiver()
{
  call_method<void>(m_context,
                    "registerMediaButtonEventReceiver", "()V");
}

void CJNIMainActivity::unregisterMediaButtonEventReceiver()
{
  call_method<void>(m_context,
                    "unregisterMediaButtonEventReceiver", "()V");
}
