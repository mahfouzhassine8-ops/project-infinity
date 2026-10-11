# Android packaging

# Configure files into packaging environment.
configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/Makefile.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/Makefile @ONLY)
configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/gradle.properties
               ${CMAKE_BINARY_DIR}/tools/android/packaging/gradle.properties COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/build.gradle
               ${CMAKE_BINARY_DIR}/tools/android/packaging/build.gradle COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/gradlew
               ${CMAKE_BINARY_DIR}/tools/android/packaging/gradlew COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/settings.gradle
               ${CMAKE_BINARY_DIR}/tools/android/packaging/settings.gradle COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/gradle/wrapper/gradle-wrapper.jar
               ${CMAKE_BINARY_DIR}/tools/android/packaging/gradle/wrapper/gradle-wrapper.jar COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/gradle/wrapper/gradle-wrapper.properties
               ${CMAKE_BINARY_DIR}/tools/android/packaging/gradle/wrapper/gradle-wrapper.properties COPYONLY)
configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/jni/Android.mk
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/jni/Android.mk COPYONLY)
file(WRITE ${CMAKE_BINARY_DIR}/tools/depends/Makefile.include
     "$(PREFIX)/lib/${APP_NAME_LC}/lib${APP_NAME_LC}.so: ;\n")

string(REPLACE "." ";" APP_VERSION_CODE_LIST ${APP_VERSION_CODE})
list(GET APP_VERSION_CODE_LIST 0 major)
list(GET APP_VERSION_CODE_LIST 1 minor)
list(GET APP_VERSION_CODE_LIST 2 patch)
unset(APP_VERSION_CODE_LIST)
math(EXPR APP_VERSION_CODE_ANDROID "(${major} * 100 + ${minor}) * 1000 + ${patch}")
unset(major)
unset(minor)
unset(patch)

set(package_files strings.xml
                  colors.xml
                  searchable.xml
                  AndroidManifest.xml
                  build.gradle
                  src/Splash.java
                  src/InfinityExitCompletion.java
                                 src/InfinityCloseGuardService.java
                                 src/InfinityCloseNativeLease.java
                  src/InfinityCheckpointProtocol.java
                  src/InfinityCheckpointAddonInstaller.java
                  src/InfinityCheckpointController20Installer.java
                  src/InfinityCheckpointCompat82Installer.java
                  src/InfinityInstalledCheckpointInstaller.java
                  src/InfinityPowerControlActivity.java
                  src/InfinityCloseProgress.java
                  src/InfinityPowerMenuRoutes.java
                  src/InfinityKodiShutdown.java
                  src/InfinityKodiEntryActivity.java
                  src/InfinityStartupPreparation.java
                  src/InfinityStartupTrace.java
                  src/InfinityStartupTiming.java
                  src/InfinityHealthExport.java
                  src/InfinityInstalledCodeEvidence.java
                  src/InfinityAndroidKeyboard.java
                  src/InfinityResponsiveness.java
                  src/InfinityStartupHandoff.java
                  src/InfinityGlassChooser.java
                  src/InfinityCosmicArt.java
                  src/InfinityChooserWeather.java
                  src/InfinityGlassOptions.java
                  src/InfinityGlassHealth.java
                  src/InfinityGlassRecovery.java
                  src/InfinityGlassArt.java
                  src/Main.java
                  src/InfinityCoreBridge.java
                  src/InfinityDiagnosticFiles.java
                  src/InfinityExitDiagnostics.java
                  src/InfinityResponsiveTrace.java
                  src/InfinityRefreshController.java
                  src/InfinityPlatformHook.java
                  src/InfinityPlatformHooks.java
                  src/InfinitySystemMediaHook.java
                  src/InfinityAudioFocusHook.java
                  src/InfinityLiveActivity.java
                  src/CobraSportsPreferences.java
                  src/CobraSportsReminderJob.java
                  src/CobraProUi.java
                  src/CobraImmersiveAmbient.java
                  src/InfinityKodiAmbientGate.java
                  src/InfinityKodiSurfaceSampler.java
                  src/CobraEmbeddedCrop.java
                  src/InfinityCobraFeatureRuntime.java
                  src/CobraDiagnosticArchive.java
                  src/InfinityCobraDiagnostics.java
                  src/InfinityCobraDeviceBridge.java
                  src/InfinityCobraRecordingService.java
                  src/InfinityCobraReminderReceiver.java
                  src/InfinityCobraBootReceiver.java
                  src/InfinityExtendedBackgroundService.java
                  src/InfinityResumeHubInstaller.java
                  src/InfinityBackgroundControlActivity.java
                  src/XBMCBroadcastReceiver.java
                  src/XBMCInputDeviceListener.java
                  src/XBMCJsonRPC.java
                  src/XBMCMainView.java
                  src/XBMCMediaSession.java
                  src/XBMCRecommendationBuilder.java
                  src/XBMCSearchableActivity.java
                  src/XBMCSettingsContentObserver.java
                  src/XBMCProperties.java
                  src/XBMCVideoView.java
                  src/XBMCFile.java
                  src/XBMCTextureCache.java
                  src/XBMCURIUtils.java
                  src/channels/SyncChannelJobService.java
                  src/channels/SyncProgramsJobService.java
                  src/channels/model/XBMCDatabase.java
                  src/channels/model/Subscription.java
                  src/channels/util/SharedPreferencesHelper.java
                  src/channels/util/TvUtil.java
                  src/interfaces/XBMCAudioManagerOnAudioFocusChangeListener.java
                  src/interfaces/XBMCSurfaceTextureOnFrameAvailableListener.java
                  src/interfaces/XBMCNsdManagerResolveListener.java
                  src/interfaces/XBMCNsdManagerRegistrationListener.java
                  src/interfaces/XBMCNsdManagerDiscoveryListener.java
                  src/interfaces/XBMCMediaDrmOnEventListener.java
                  src/interfaces/XBMCDisplayManagerDisplayListener.java
                  src/interfaces/XBMCSpeechRecognitionListener.java
		  src/interfaces/XBMCConnectivityManagerNetworkCallback.java
                  src/model/TVEpisode.java
                  src/model/Movie.java
                  src/model/TVShow.java
                  src/model/File.java
                  src/model/Album.java
                  src/model/Song.java
                  src/model/MusicVideo.java
                  src/model/Media.java
                  src/content/XBMCFileContentProvider.java
                  src/content/XBMCMediaContentProvider.java
                  src/content/XBMCContentProvider.java
                  src/content/XBMCYTDLContentProvider.java
                  )
foreach(file IN LISTS package_files)
  configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/${file}.in
                 ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/${file} @ONLY)
endforeach()

# Copy files to the location expected by the Android packaging scripts.
add_custom_target(bundle
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/tools/android/packaging/media
                                               ${CMAKE_BINARY_DIR}/tools/android/packaging/media
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/res
                                               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/res
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${DEPENDS_PATH}/lib/python${PYTHON_VERSION} ${libdir}/python${PYTHON_VERSION}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${DEPENDS_PATH}/share/${APP_NAME_LC} ${datadir}/${APP_NAME_LC}
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:${APP_NAME_LC}>
                                     ${libdir}/${APP_NAME_LC}/$<TARGET_FILE_NAME:${APP_NAME_LC}>)
add_dependencies(bundle ${APP_NAME_LC})

# This function is used to prepare a prefix expected by the Android packaging
# scripts. It creates a bundle_files command that is added to the bundle target.
function(add_bundle_file file destination relative)
  if(NOT TARGET bundle_files)
    file(REMOVE ${CMAKE_BINARY_DIR}/${CORE_BUILD_DIR}/BundleFiles.cmake)
    add_custom_target(bundle_files COMMAND ${CMAKE_COMMAND} -P ${CMAKE_BINARY_DIR}/${CORE_BUILD_DIR}/BundleFiles.cmake)
    add_dependencies(bundle bundle_files)
    add_dependencies(bundle_files ${APP_NAME_LC})
  endif()

  if(TARGET ${file})
    # Add support for IMPORTED lib targets
    # If we need specific properties from other target types later, we can add them
    # here with some validity checks
    get_target_property(imploc_file ${file} IMPORTED_LOCATION)
    if(imploc_file)
      set(file ${imploc_file})
    else()
      return()
    endif()
  endif()

  string(REPLACE "${relative}/" "" outfile ${file})
  get_filename_component(file ${file} REALPATH)
  get_filename_component(outdir ${outfile} DIRECTORY)
  file(APPEND ${CMAKE_BINARY_DIR}/${CORE_BUILD_DIR}/BundleFiles.cmake
       "file(COPY \"${file}\" DESTINATION \"${destination}/${outdir}\")\n")
  if(file MATCHES "\\.so\\..+$")
    get_filename_component(srcfile "${file}" NAME)
    string(REGEX REPLACE "\\.so\\..+$" "\.so" destfile ${srcfile})
    file(APPEND ${CMAKE_BINARY_DIR}/${CORE_BUILD_DIR}/BundleFiles.cmake
         "file(RENAME \"${destination}/${outdir}/${srcfile}\" \"${destination}/${outdir}/${destfile}\")\n")
  endif()
endfunction()

# Copy files into prefix
foreach(file IN LISTS XBT_FILES install_data)
  string(REPLACE "${CMAKE_BINARY_DIR}/" "" file ${file})
  add_bundle_file(${CMAKE_BINARY_DIR}/${file} ${datarootdir}/${APP_NAME_LC} ${CMAKE_BINARY_DIR})
endforeach()

# libdvdnav is currently the only LIBRARY_FILES item remaining for android
foreach(library IN LISTS LIBRARY_FILES)
  add_bundle_file(${library} ${libdir}/${APP_NAME_LC} ${CMAKE_BINARY_DIR})
endforeach()

if(TARGET Shairplay::Shairplay)
  add_bundle_file(Shairplay::Shairplay ${libdir} "")
endif()

# Main targets from Makefile.in
if(CPU MATCHES i686)
  set(CPU x86)
endif()
foreach(target apk apk-clean)
  add_custom_target(${target}
      COMMAND env PATH=${NATIVEPREFIX}/bin:$ENV{PATH} ${CMAKE_MAKE_PROGRAM} -j1
              -C ${CMAKE_BINARY_DIR}/tools/android/packaging
              CMAKE_SOURCE_DIR=${CMAKE_SOURCE_DIR}
              CC=${CMAKE_C_COMPILER}
              CPU=${CPU}
              HOST=${HOST}
              TOOLCHAIN=${TOOLCHAIN}
              PREFIX=${prefix}
              DEPENDS_PATH=${DEPENDS_PATH}
              NDKROOT=${NDKROOT}
              SDKROOT=${SDKROOT}
              STRIP=${CMAKE_STRIP}
              ${target}
      WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/tools/android/packaging
      VERBATIM
  )
  if(NOT target STREQUAL apk-clean)
    add_dependencies(${target} bundle)
  endif()
endforeach()

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraVisualTheme.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraVisualTheme.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraVisualRenderer.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraVisualRenderer.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraImmersiveAmbient.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraImmersiveAmbient.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraVisualScene.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraVisualScene.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraVisualGeometry.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraVisualGeometry.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraVisualCatalog.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraVisualCatalog.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraEmblem.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraEmblem.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraPresentationEffects.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraPresentationEffects.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraPresentationSafety.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraPresentationSafety.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraSmartReturn.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraSmartReturn.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraQuickPeekSession.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraQuickPeekSession.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraNetworkIntelligence.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraNetworkIntelligence.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/CobraEmbeddedCrop.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/CobraEmbeddedCrop.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/InfinityKodiAmbientGate.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/InfinityKodiAmbientGate.java @ONLY)

configure_file(${CMAKE_SOURCE_DIR}/tools/android/packaging/xbmc/src/InfinityKodiSurfaceSampler.java.in
               ${CMAKE_BINARY_DIR}/tools/android/packaging/xbmc/src/InfinityKodiSurfaceSampler.java @ONLY)
