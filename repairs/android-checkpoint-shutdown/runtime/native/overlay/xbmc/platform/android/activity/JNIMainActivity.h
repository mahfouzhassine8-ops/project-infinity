/*
 *  Copyright (C) 2015-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#pragma once

#include <cstdint>
#include <array>

#include <androidjni/Activity.h>
#include <androidjni/InputManager.h>
#include <androidjni/Rect.h>

namespace jni
{

class CJNIMainActivity : public CJNIActivity, public CJNIInputManagerInputDeviceListener
{
public:
  explicit CJNIMainActivity(const ANativeActivity *nativeActivity);
  ~CJNIMainActivity() override;

  static CJNIMainActivity* GetAppInstance() { return m_appInstance; }

  static void RegisterNatives(JNIEnv* env);
  static jboolean _infinityRequestPersistenceCheckpoint(JNIEnv*, jobject, jstring, jstring, jint);
  static jstring _infinityPersistenceCheckpointStatus(JNIEnv*, jobject, jstring, jstring, jint);
  static jboolean _infinityAuthorizeCheckpointTermination(JNIEnv*, jobject, jstring, jstring, jint);

  static void _onNewIntent(JNIEnv *env, jobject context, jobject intent);
  static void _onActivityResult(JNIEnv *env, jobject context, jint requestCode, jint resultCode, jobject resultData);
  static void _onVolumeChanged(JNIEnv *env, jobject context, jint volume);
  static void _doFrame(JNIEnv *env, jobject context, jlong frameTimeNanos);
  static jlongArray _infinityHeartbeat(JNIEnv* env, jclass);
  static void _onInputDeviceAdded(JNIEnv *env, jobject context, jint deviceId);
  static void _onInputDeviceChanged(JNIEnv *env, jobject context, jint deviceId);
  static void _onInputDeviceRemoved(JNIEnv *env, jobject context, jint deviceId);
  static void _onVisibleBehindCanceled(JNIEnv *env, jobject context);

  // Infinity v4: matched source-built Java/JNI contract.
  static jboolean _infinityHasActiveVideo(JNIEnv* env, jobject context);
  static void _infinitySyncDisplayState(JNIEnv* env, jobject context);
  static jint _infinitySystemThemeMode(JNIEnv* env, jobject context);
  static jint _infinityWindowWidth(JNIEnv* env, jobject context);
  static jint _infinityWindowHeight(JNIEnv* env, jobject context);
  static jint _infinityBridgeVersion(JNIEnv* env, jobject context);
  static jboolean _infinityCanEnterPictureInPicture(JNIEnv* env, jobject context);
  static jfloat _infinityVideoAspectRatio(JNIEnv* env, jobject context);
  static jint _infinityWindowMode(JNIEnv* env, jobject context);
  static jlongArray _infinityGetState(JNIEnv* env, jobject context);
  int infinityGetSystemTheme() const;
  int infinityGetModeSnapshot() const;
  void infinityNotifyPlaybackChanged();
  uint64_t infinityGetWindowSize() const;
  bool infinityIsPictureInPicture() const;

  static void _callNative(JNIEnv *env, jobject context, jlong funcAddr, jlong variantAddr);
  static void runNativeOnUiThread(void (*callback)(void*), void* variant);
  static void registerMediaButtonEventReceiver();
  static void unregisterMediaButtonEventReceiver();

  CJNIRect getDisplayRect();

private:
  static CJNIMainActivity *m_appInstance;

protected:
  virtual void onNewIntent(CJNIIntent intent)=0;
  virtual void onActivityResult(int requestCode, int resultCode, CJNIIntent resultData)=0;
  virtual void onVolumeChanged(int volume)=0;
  virtual void doFrame(int64_t frameTimeNanos)=0;
  void onVisibleBehindCanceled() override = 0;

  virtual void onDisplayAdded(int displayId)=0;
  virtual void onDisplayChanged(int displayId)=0;
  virtual void onDisplayRemoved(int displayId)=0;

  virtual std::array<int64_t, 16> infinityGetState() const = 0;
  virtual bool infinityHasActiveVideo() const = 0;
  virtual void infinitySyncDisplayStateFromBridge() = 0;
  virtual int infinityWindowWidth() const = 0;
  virtual int infinityWindowHeight() const = 0;
  virtual bool infinityCanEnterPictureInPicture() const = 0;
  virtual float infinityVideoAspectRatio() const = 0;
};

} // namespace jni
