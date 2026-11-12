/*
 *  Copyright (C) 2005-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#include "AndroidBuiltins.h"

#include "ServiceBroker.h"
#include "application/Application.h"
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#include "settings/Settings.h"
#include "settings/SettingsComponent.h"
#include <androidjni/Context.h>
#include <androidjni/jutils-details.hpp>
#include "messaging/ApplicationMessenger.h"

/*! \brief Launch an android system activity.
 *  \param params The parameters.
 *  \details params[0] = package
 *           params[1] = intent (optional)
 *           params[2] = datatype (optional)
 *           params[3] = dataURI (optional)
 *           params[4] = flags (optional)
 *           params[5] = extras (optional)
 *           params[6] = action (optional)
 *           params[7] = category (optional)
 *           params[8] = className (optional)
 */
static int LaunchAndroidActivity(const std::vector<std::string>& params)
{
  CServiceBroker::GetAppMessenger()->PostMsg(TMSG_START_ANDROID_ACTIVITY, -1, -1, nullptr, "",
                                             params);

  return 0;
}

// Note: For new Texts with comma add a "\" before!!! Is used for table text.
//
/// \page page_List_of_built_in_functions
/// \section built_in_functions_2 Android built-in's
///
/// -----------------------------------------------------------------------------
///
/// \table_start
///   \table_h2_l{
///     Function,
///     Description }
///   \table_row2_l{
///     <b>`StartAndroidActivity(package\,[intent\,dataType\,dataURI\,flags\,extras\,action\,category\,className])`</b>
///     ,
///     Launch an Android native app with the given package name. Optional parms
///     (in order): intent\, dataType\, dataURI\, flags\, extras\, action\,
///     category\, className.
///     @param[in] package
///     @param[in] intent (optional)
///     @param[in] datatype (optional)
///     @param[in] dataURI (optional)
///     @param[in] flags (optional)
///     @param[in] extras (optional)
///     @param[in] action (optional)
///     @param[in] category (optional)
///     @param[in] className (optional)
///     <p><hr>
///     @skinning_v20 Added parameters `flags`\,`extras`\,`action`\,`category`\,`className`.
///     <p>
///   }
/// \table_end
///

static int OpenInfinityCast(const std::vector<std::string>& params)
{
  if (!params.empty() || g_application.IsStopping() || InfinityAndroidCheckpoint::IsActive() ||
      CServiceBroker::GetSettingsComponent()->GetSettings()->GetString("lookandfeel.skin") !=
          "skin.infinity.diggz")
    return 1;
  // A dialog on the existing Main activity avoids an Activity transition or
  // lifecycle pause before a receiver has accepted playback. No Main edit.
  using namespace jni;
  JNIEnv* env = xbmc_jnienv();
  if (!env) return 1;
  try
  {
    auto clazz = CJNIContext::getClassLoader().loadClass("com.projectinfinity.kodi.InfinityCastDialog");
    if (env->ExceptionCheck()) { env->ExceptionClear(); return 1; }
    call_static_method<void>(env, clazz, "open", "()V");
    if (env->ExceptionCheck()) { env->ExceptionClear(); return 1; }
    return 0;
  }
  catch (...) { if (env->ExceptionCheck()) env->ExceptionClear(); return 1; }
}

CBuiltins::CommandMap CAndroidBuiltins::GetOperations() const
{
  return {{"startandroidactivity",
           {"Launch an Android native app with the given package name.  Optional parms (in order): "
            "intent, dataType, dataURI, flags, extras, action, category, className.",
            1, LaunchAndroidActivity}},
          {"infinitycast", {"Open the Infinity-only Cast dialog", 0, OpenInfinityCast}}};
}
