/*
 *  Copyright (C) 2012-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "AndroidTouch.h"

#include "CompileInfo.h"
#include "input/touch/generic/GenericTouchActionHandler.h"
#include "input/touch/generic/GenericTouchInputHandler.h"
#include "platform/android/activity/XBMCApp.h"

#include <algorithm>
#include <cmath>
#include <mutex>
#include <string>

namespace
{
// INFINITY_WINDOW_INPUT_V1: InputQueue coordinates belong to the Android window;
// Kodi hit testing belongs to XBMCMainView. This is a translation, not a resize
// engine. In particular, the window's position on the phone is NOT subtracted.
struct InputViewport
{
  int left{0};
  int top{0};
  int width{0};
  int height{0};
  bool known{false};
  bool live{false};
  uint64_t serial{0};
};

std::mutex viewportMutex;
InputViewport viewport;
unsigned int viewportTraceCount{0};

void PublishViewport(InputViewport next)
{
  std::lock_guard<std::mutex> lock(viewportMutex);
  if (next.left == viewport.left && next.top == viewport.top &&
      next.width == viewport.width && next.height == viewport.height &&
      next.known == viewport.known && next.live == viewport.live)
    return;
  next.serial = viewport.serial + 1;
  viewport = next;
  if (viewportTraceCount++ < 64)
    CXBMCApp::android_printf(
        "Infinity input viewport: window_origin=%d,%d surface=%dx%d live=%d serial=%llu",
        next.left, next.top, next.width, next.height, next.live,
        static_cast<unsigned long long>(next.serial));
}

InputViewport ReadViewport()
{
  std::lock_guard<std::mutex> lock(viewportMutex);
  return viewport;
}
} // namespace

CAndroidTouch::CAndroidTouch()
{
  CGenericTouchInputHandler::GetInstance().RegisterHandler(&CGenericTouchActionHandler::GetInstance());
}

CAndroidTouch::~CAndroidTouch()
{
  CGenericTouchInputHandler::GetInstance().UnregisterHandler();
}

void CAndroidTouch::RefreshInputViewport(JNIEnv* env, jobject activity)
{
  // Called only by Main's UI-thread Choreographer callback. The input thread
  // consumes an immutable value snapshot; it never calls Android View methods.
  if (env == nullptr || activity == nullptr || env->ExceptionCheck())
    return;

  static jfieldID mainViewField{nullptr};
  static jfieldID currentActivityField{nullptr};
  static jfieldID createdField{nullptr};
  static jmethodID locationMethod{nullptr};
  static jmethodID widthMethod{nullptr};
  static jmethodID heightMethod{nullptr};
  static jmethodID visibilityMethod{nullptr};
  static bool lookupErrorLogged{false};
  if (env->PushLocalFrame(8) < 0)
  {
    // Preserve a pending allocation exception rather than masking it.
    return;
  }

  jobject view{nullptr};
  jclass activityClass = env->GetObjectClass(activity);
  if (mainViewField == nullptr)
  {
    const std::string signature = std::string("L") + CCompileInfo::GetClass() + "/XBMCMainView;";
    if (activityClass != nullptr)
      mainViewField = env->GetFieldID(activityClass, "mMainView", signature.c_str());
  }
  if (!env->ExceptionCheck() && activityClass != nullptr && currentActivityField == nullptr)
  {
    const std::string signature = std::string("L") + CCompileInfo::GetClass() + "/Main;";
    currentActivityField = env->GetStaticFieldID(activityClass, "MainActivity", signature.c_str());
  }
  if (!env->ExceptionCheck() && currentActivityField != nullptr)
  {
    jobject currentActivity = env->GetStaticObjectField(activityClass, currentActivityField);
    if (!env->ExceptionCheck() && !env->IsSameObject(activity, currentActivity))
    {
      // Main's inherited frame callback can outlive an Activity. Only the
      // current Activity may replace the input viewport of its live surface.
      env->PopLocalFrame(nullptr);
      return;
    }
  }
  if (!env->ExceptionCheck() && mainViewField != nullptr)
    view = env->GetObjectField(activity, mainViewField);

  if (!env->ExceptionCheck() && view != nullptr && locationMethod == nullptr)
  {
    jclass viewClass = env->GetObjectClass(view);
    if (viewClass != nullptr)
    {
      createdField = env->GetFieldID(viewClass, "mIsCreated", "Z");
      if (!env->ExceptionCheck())
        widthMethod = env->GetMethodID(viewClass, "getWidth", "()I");
      if (!env->ExceptionCheck())
        heightMethod = env->GetMethodID(viewClass, "getHeight", "()I");
      if (!env->ExceptionCheck())
        visibilityMethod = env->GetMethodID(viewClass, "getWindowVisibility", "()I");
      if (!env->ExceptionCheck())
        locationMethod = env->GetMethodID(viewClass, "getLocationInWindow", "([I)V");
    }
  }

  InputViewport next;
  if (!env->ExceptionCheck() && view != nullptr && locationMethod != nullptr)
  {
    next.known = true;
    const bool created = env->GetBooleanField(view, createdField) == JNI_TRUE;
    const int visibility = !env->ExceptionCheck() ? env->CallIntMethod(view, visibilityMethod) : -1;
    if (!env->ExceptionCheck())
      next.width = env->CallIntMethod(view, widthMethod);
    if (!env->ExceptionCheck())
      next.height = env->CallIntMethod(view, heightMethod);
    jintArray location = !env->ExceptionCheck() ? env->NewIntArray(2) : nullptr;
    if (!env->ExceptionCheck() && location != nullptr)
    {
      env->CallVoidMethod(view, locationMethod, location);
      jint origin[2]{0, 0};
      if (!env->ExceptionCheck())
        env->GetIntArrayRegion(location, 0, 2, origin);
      next.left = origin[0];
      next.top = origin[1];
      next.live = created && visibility == 0 && next.width > 0 && next.height > 0;
    }
  }
  else if (!env->ExceptionCheck() && mainViewField != nullptr && view == nullptr)
    next.known = true; // A destroyed/not-yet-attached view cannot receive taps.

  if (env->ExceptionCheck())
  {
    // Optional geometry lookup must not poison the existing frame callback.
    env->ExceptionClear();
    mainViewField = nullptr;
    currentActivityField = nullptr;
    locationMethod = nullptr;
    next = ReadViewport();
    if (next.known)
      next.live = false;
    if (!lookupErrorLogged)
    {
      lookupErrorLogged = true;
      CXBMCApp::android_printf("Infinity input viewport: optional view lookup unavailable");
    }
  }
  PublishViewport(next);
  env->PopLocalFrame(nullptr);
}

bool CAndroidTouch::onTouchEvent(AInputEvent* event)
{
  if (event == nullptr)
    return false;

  const int32_t eventAction = AMotionEvent_getAction(event);
  const int32_t action = eventAction & AMOTION_EVENT_ACTION_MASK;
  const int64_t time = AMotionEvent_getEventTime(event);
  auto& handler = CGenericTouchInputHandler::GetInstance();
  const auto abortGesture = [&]() {
    m_gestureActive = false;
    return handler.HandleTouchInput(TouchInputAbort, 0.0f, 0.0f, time, 0);
  };

  // Cancellation need not have any pointers. Never read pointer zero first.
  if (action == AMOTION_EVENT_ACTION_CANCEL || action == AMOTION_EVENT_ACTION_OUTSIDE)
  {
    const bool passToAndroid = m_streamRejected;
    const bool handled = abortGesture();
    return passToAndroid ? false : handled;
  }
  const size_t count = AMotionEvent_getPointerCount(event);
  if (count == 0)
    return abortGesture();
  const size_t pointer = (eventAction & AMOTION_EVENT_ACTION_POINTER_INDEX_MASK) >>
                         AMOTION_EVENT_ACTION_POINTER_INDEX_SHIFT;
  if (pointer >= count)
    return abortGesture();
  if (pointer >= CGenericTouchInputHandler::MAX_POINTERS)
    return true; // Preserve Kodi's existing two-pointer gesture limit.

  const InputViewport current = ReadViewport();
  if (action == AMOTION_EVENT_ACTION_DOWN)
  {
    m_streamRejected = false;
    if (m_gestureActive)
      abortGesture();
    m_gestureViewportSerial = current.serial;
  }
  else if (!m_gestureActive)
    return !m_streamRejected; // Keep caption-owned streams routed to Android.
  else if (m_gestureViewportSerial != current.serial)
  {
    abortGesture();
    return true; // Do not turn a resize/caption change into an accidental tap.
  }
  if (current.known && !current.live)
  {
    if (m_gestureActive)
      abortGesture();
    m_streamRejected = action == AMOTION_EVENT_ACTION_DOWN;
    return false;
  }

  const float x = AMotionEvent_getX(event, pointer) - current.left;
  const float y = AMotionEvent_getY(event, pointer) - current.top;
  if (!std::isfinite(x) || !std::isfinite(y))
    return abortGesture();
  if (action == AMOTION_EVENT_ACTION_DOWN && current.known &&
      (x < 0.0f || y < 0.0f || x >= current.width || y >= current.height))
  {
    m_streamRejected = true;
    return false; // Return the whole caption stream to Android, never clamp it.
  }

  TouchInput touchEvent = TouchInputAbort;
  switch (action)
  {
    case AMOTION_EVENT_ACTION_DOWN:
    case AMOTION_EVENT_ACTION_POINTER_DOWN:
      touchEvent = TouchInputDown;
      break;
    case AMOTION_EVENT_ACTION_UP:
    case AMOTION_EVENT_ACTION_POINTER_UP:
      touchEvent = TouchInputUp;
      break;
    case AMOTION_EVENT_ACTION_MOVE:
      touchEvent = TouchInputMove;
      break;
    default:
      return abortGesture();
  }

  // Validate the complete event before modifying the generic gesture state.
  const size_t used = std::min(count, static_cast<size_t>(CGenericTouchInputHandler::MAX_POINTERS));
  for (size_t i = 0; i < used; ++i)
    if (!std::isfinite(AMotionEvent_getX(event, i)) || !std::isfinite(AMotionEvent_getY(event, i)))
      return abortGesture();
  for (size_t i = 0; i < used; ++i)
    handler.UpdateTouchPointer(i, AMotionEvent_getX(event, i) - current.left,
                               AMotionEvent_getY(event, i) - current.top, time);

  if (action == AMOTION_EVENT_ACTION_DOWN)
  {
    m_gestureActive = true;
    if (m_downTraceCount++ < 24)
      CXBMCApp::android_printf(
          "Infinity input down: window=%.1f,%.1f surface=%.1f,%.1f origin=%d,%d serial=%llu",
          AMotionEvent_getX(event, pointer), AMotionEvent_getY(event, pointer), x, y,
          current.left, current.top, static_cast<unsigned long long>(current.serial));
  }
  if (touchEvent == TouchInputDown)
    CGenericTouchActionHandler::GetInstance().QuerySupportedGestures(x, y);
  const bool handled = handler.HandleTouchInput(touchEvent, x, y, time, pointer);
  if (action == AMOTION_EVENT_ACTION_UP)
    m_gestureActive = false;
  return handled;
}

void CAndroidTouch::setDPI(uint32_t dpi)
{
  if (dpi != 0)
  {
    m_dpi = dpi;
    CGenericTouchInputHandler::GetInstance().SetScreenDPI(m_dpi);
  }
}
