/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
#include <android/native_activity.h>

// Preserve the real NDK native_app_glue. This wrapper is selected only for
// Main through android.app.func_name. Declined entry starts no android_main
// thread and leaves NativeActivity's initially-null callbacks untouched, so
// Java can complete super.onCreate and safely return to the existing chooser.
extern "C" void ANativeActivity_onCreate(ANativeActivity*, void*, size_t);

extern "C" __attribute__((visibility("default")))
void InfinityNativeActivity_onCreate(ANativeActivity* activity, void* savedState,
                                    size_t savedStateSize)
{
  if (!activity || !activity->env || !activity->clazz) return;
  JNIEnv* env = activity->env;
  if (env->ExceptionCheck()) return;
  jclass type = env->GetObjectClass(activity->clazz);
  if (!type || env->ExceptionCheck())
  {
    if (env->ExceptionCheck()) env->ExceptionClear();
    if (type) env->DeleteLocalRef(type);
    return;
  }
  jmethodID method = env->GetMethodID(type, "infinityPrepareNativeTask", "()Z");
  if (!method || env->ExceptionCheck())
  {
    if (env->ExceptionCheck()) env->ExceptionClear();
    env->DeleteLocalRef(type);
    return;
  }
  jboolean admitted = env->CallBooleanMethod(activity->clazz, method);
  const bool failed = env->ExceptionCheck();
  if (failed) env->ExceptionClear();
  env->DeleteLocalRef(type);
  if (!failed && admitted == JNI_TRUE)
    ANativeActivity_onCreate(activity, savedState, savedStateSize);
}
