set(SOURCES android_main.cpp
            InfinityVideoLock.cpp
            InfinityCastNative.cpp
            InfinityAndroidCheckpoint.cpp
            InfinityScriptCheckpointContracts.cpp
            InfinityInstalledModules.cpp
            InfinityModuleManifest.cpp
            InfinityPlaybackCheckpoint.cpp
            InfinityAudioPolicy.cpp
            AndroidFeatures.cpp
            AndroidJoyStick.cpp
            AndroidKey.cpp
            AndroidKeyboard.cpp
            AndroidMouse.cpp
            AndroidTouch.cpp
            EventLoop.cpp
            JNIMainActivity.cpp
            JNIXBMCMainView.cpp
            JNIXBMCMediaSession.cpp
            JNIXBMCVideoView.cpp
            JNIXBMCAudioManagerOnAudioFocusChangeListener.cpp
            JNIXBMCSurfaceTextureOnFrameAvailableListener.cpp
            JNIXBMCNsdManagerDiscoveryListener.cpp
            JNIXBMCNsdManagerRegistrationListener.cpp
            JNIXBMCNsdManagerResolveListener.cpp
            JNIXBMCJsonHandler.cpp
            JNIXBMCFile.cpp
            JNIXBMCTextureCache.cpp
            JNIXBMCURIUtils.cpp
            JNIXBMCDisplayManagerDisplayListener.cpp
            JNIXBMCSpeechRecognitionListener.cpp
            JNIXBMCConnectivityManagerNetworkCallback.cpp
            JNIXBMCBroadcastReceiver.cpp
            ${NDKROOT}/sources/android/native_app_glue/android_native_app_glue.c
            ${NDKROOT}/sources/android/cpufeatures/cpu-features.c)

set(HEADERS AndroidFeatures.h
            InfinityAndroidCheckpoint.h
            InfinityInstalledModules.h
            InfinityModuleManifest.h
            InfinityPlaybackCheckpoint.h
            InfinityCheckpointFile.h
            InfinityCheckpointXml.h
            InfinityAudioPolicy.h
            AndroidJoyStick.h
            AndroidKey.h
            AndroidKeyboard.h
            AndroidMouse.h
            AndroidTouch.h
            EventLoop.h
            IActivityHandler.h
            JNIMainActivity.h
            JNIXBMCMainView.h
            JNIXBMCMediaSession.h
            JNIXBMCVideoView.h
            JNIXBMCAudioManagerOnAudioFocusChangeListener.h
            JNIXBMCSurfaceTextureOnFrameAvailableListener.h
            JNIXBMCNsdManagerDiscoveryListener.h
            JNIXBMCNsdManagerRegistrationListener.h
            JNIXBMCNsdManagerResolveListener.h
            JNIXBMCJsonHandler.h
            JNIXBMCFile.h
            JNIXBMCTextureCache.h
            JNIXBMCURIUtils.h
            JNIXBMCDisplayManagerDisplayListener.h
            JNIXBMCSpeechRecognitionListener.h
            JNIXBMCConnectivityManagerNetworkCallback.h
            JNIXBMCBroadcastReceiver.h
            XBMCApp.h)

core_add_library(platform_android_activity)
target_include_directories(${CORE_LIBRARY} SYSTEM
                           PRIVATE ${NDKROOT}/sources/android/native_app_glue
                                   ${NDKROOT}/sources/android/cpufeatures)

# Keep only the lock and observer correction's newly emitted helpers private. Do not change compiler
# visibility: shared COMDAT definitions may also supply existing Kodi exports.
set(infinity_lock_exports "${CMAKE_CURRENT_BINARY_DIR}/InfinityVideoLock.exports.map")
file(WRITE "${infinity_lock_exports}" [=[
{
  local:
    _ZN17InfinityVideoLock4Gate4PackEjjb;
    _ZN17InfinityVideoLock4Gate5BeginEjj;
    _ZN17InfinityVideoLock4Gate6CommitEjm;
    _ZN17InfinityVideoLock4Gate6RetireEj;
    _ZN17InfinityVideoLock4Gate7AdvanceEjb;
    _ZN17InfinityVideoLock4Gate7SessionEm;
    _ZN3jni11call_methodIvNS_7jholderIP7_jclassEEJRlEEET_P7_JNIEnvRKT0_P10_jmethodIDDpOT1_;
    _ZN3jni11call_methodIvNS_7jholderIP7_jclassEEJRlRiEEET_P7_JNIEnvRKT0_P10_jmethodIDDpOT1_;
    _ZN3jni11call_methodIvNS_7jholderIP7_jclassEEJRlS5_S5_S5_EEET_P7_JNIEnvRKT0_P10_jmethodIDDpOT1_;
    _ZN3jni18call_static_methodIvJRlEEET_P7_JNIEnvRKNS_7jholderIP7_jclassEEPKcSC_DpOT0_;
    _ZN3jni18call_static_methodIvJRlRiEEET_P7_JNIEnvRKNS_7jholderIP7_jclassEEPKcSD_DpOT0_;
    _ZN3jni18call_static_methodIvJRlS1_S1_S1_EEET_P7_JNIEnvRKNS_7jholderIP7_jclassEEPKcSC_DpOT0_;
    _ZN3jni7details10jni_helperIvE11call_methodINS_7jholderIP7_jclassEEJRlEEEvP7_JNIEnvRKT_P10_jmethodIDDpOT0_;
    _ZN3jni7details10jni_helperIvE11call_methodINS_7jholderIP7_jclassEEJRlRiEEEvP7_JNIEnvRKT_P10_jmethodIDDpOT0_;
    _ZN3jni7details10jni_helperIvE11call_methodINS_7jholderIP7_jclassEEJRlS8_S8_S8_EEEvP7_JNIEnvRKT_P10_jmethodIDDpOT0_;
    _ZN3jni7details7forwardIRiEEOT_RNS0_16remove_referenceIS3_E4typeE;
    _ZN3jni7details7forwardIRlEEOT_RNS0_16remove_referenceIS3_E4typeE;
    _ZNK17CGUIWindowManager9GetWindowI10CGUIDialogLPv0EEEPT_i;
    _ZNK17InfinityVideoLock4Gate5ValueEv;
    _ZNKSt6__ndk110shared_ptrI9CFileItemE12owner_beforeIS1_EEbRKNS_8weak_ptrIT_EE;
    _ZNKSt6__ndk18weak_ptrI9CFileItemE12owner_beforeIS1_EEbRKNS_10shared_ptrIT_EE;
    _ZNKSt6__ndk18weak_ptrIN4KODI9MESSAGING21CApplicationMessengerEE4lockEv;
    _ZNSt6__ndk18weak_ptrIN4KODI9MESSAGING21CApplicationMessengerEEC2IS3_EERKNS_10shared_ptrIT_EENS_9enable_ifIXsr14is_convertibleIPS7_PS3_EE5valueEPNS_5__natEE4typeE;
    _ZNSt6__ndk18weak_ptrIN4KODI9MESSAGING21CApplicationMessengerEED2Ev;
    _ZNSt6__ndk18weak_ptrIN4KODI9MESSAGING21CApplicationMessengerEEaSIS3_EENS_9enable_ifIXsr14is_convertibleIPT_PS3_EE5valueERS4_E4typeERKNS_10shared_ptrIS7_EE;
    _ZNSt6__ndk110unique_ptrI8CXBMCAppNS_14default_deleteIS1_EEEC2ILb1EvEEPS1_;
    _ZNSt6__ndk117__compressed_pairIP8CXBMCAppNS_14default_deleteIS1_EEEC2IRS2_Lb1EEEOT_;
    _ZNSt6__ndk122__compressed_pair_elemIP8CXBMCAppLi0ELb0EEC2IRS2_vEEOT_;
};
]=])
# lib${APP_NAME_LC} already exists; its interface reaches the final Android
# shared target created after this subdirectory. No global linker flag changes.
set_property(TARGET lib${APP_NAME_LC} APPEND PROPERTY
             INTERFACE_LINK_OPTIONS "-Wl,--version-script=${infinity_lock_exports}")
set_property(TARGET lib${APP_NAME_LC} APPEND PROPERTY
             INTERFACE_LINK_DEPENDS "${infinity_lock_exports}")
