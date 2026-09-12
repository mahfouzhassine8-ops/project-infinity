#!/usr/bin/env python3
"""Actual Android API/JNI compile + native policy-unit and source-contract gates.

Compile-only unrelated Android collaborators are identified below. This gate does
not run Android or Samsung, decode media, or prove Audio Eraser eligibility.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def run(command, **kwargs):
    return subprocess.run([str(v) for v in command], check=True, **kwargs)


def check_source(source):
    def text(path): return (source/path).read_text()
    required = {
        'tools/android/packaging/xbmc/build.gradle.in': ['versionCode 2103120', '1.0.8-Cumulative-Audio-Policy-1'],
        'tools/android/packaging/xbmc/AndroidManifest.xml.in': ['android:appCategory="video"'],
        'tools/android/packaging/xbmc/src/InfinityCoreBridge.java.in': ['static final int VERSION = 5', 'Published responsive v5'],
        'xbmc/platform/android/activity/InfinityBridgeState.h': ['static constexpr int VERSION = 5'],
        'xbmc/windowing/android/WinSystemAndroid.cpp': ['Infinity.NativeDeviceMode', 'Infinity.NativeWidthDp', 'Infinity.NativeHeightDp', 'Infinity.NativeDisplayRevision', 'Infinity.AudioPolicyApi'],
        'xbmc/cores/VideoPlayer/VideoPlayerAudio.cpp': ['audioframe.format.m_infinityContentType = m_processInfo.InfinityAudioHasVideo() ? 3 : 2'],
        'xbmc/cores/VideoPlayer/AudioSinkAE.cpp': ['m_infinityContentType = audioframe.format.m_infinityContentType', 'm_infinityContentType != audioframe.format.m_infinityContentType'],
        'xbmc/cores/AudioEngine/Engines/ActiveAE/ActiveAE.cpp': ['INFINITY_AUDIO::Reload()', 'INFINITY_AUDIO::Resolve(inputFormat.m_infinityContentType)', 'm_sinkRequestFormat.m_infinityContentType != m_sinkFormat.m_infinityContentType', 'newFormat.m_infinityContentType != m_sinkFormat.m_infinityContentType'],
        'xbmc/cores/AudioEngine/Sinks/AESinkAUDIOTRACK.cpp': ['INFINITY_AUDIO::ValidContent(contentType)', 'm_encoding, m_min_buffer_size, m_format.m_infinityContentType', 'INFINITY_AUDIO::NoteTrack'],
        'xbmc/platform/android/activity/XBMCApp.cpp': ['m_mediaSession->acquireAudioFocus(content, m_audioFocusListener)', 'm_mediaSession->releaseAudioFocus()', 'm_mediaSession->updateAudioPolicy(content)'],
        'tools/android/packaging/xbmc/src/InfinityPlatformHooks.java.in': ['static final int API_VERSION = 2', 'void onAudioPolicy'],
        'cmake/scripts/android/Install.cmake': ['src/InfinityAudioFocusHook.java', 'src/InfinitySystemMediaHook.java', 'src/InfinityRefreshController.java'],
        'xbmc/platform/android/activity/CMakeLists.txt': ['InfinityAudioPolicy.cpp', 'InfinityAudioPolicy.h'],
    }
    for path, needles in required.items():
        data = text(path)
        for needle in needles:
            assert needle in data, (path, needle)
    session = text('tools/android/packaging/xbmc/src/XBMCMediaSession.java.in')
    assert session.count('new MediaSession(') == 1
    assert 'audio_eraser_compat_candidate' not in text('tools/android/packaging/xbmc/src/InfinitySystemMediaHook.java.in')
    cpp = text('xbmc/platform/android/activity/XBMCApp.cpp')
    section = cpp[cpp.index('bool CXBMCApp::AcquireAudioFocus()'):cpp.index('void CXBMCApp::RequestVisibleBehind')]
    assert 'audioFocusBuilder' not in section
    vp = text('xbmc/cores/VideoPlayer/VideoPlayer.cpp')
    assert vp.index('SetInfinityAudioHasVideo(valid)') < vp.index('  // open audio stream')
    focus = text('tools/android/packaging/xbmc/src/InfinityAudioFocusHook.java.in')
    assert 'Api26.abandon(manager, request)' in focus and 'synchronized boolean' in focus
    assert 'new Thread' not in focus and 'postDelayed' not in focus
    policy = text('xbmc/platform/android/activity/InfinityAudioPolicy.cpp')
    assert 'length <= 4096' in policy and 'API_VERSION' in policy
    print('PASS: cumulative v5/media/audio source connections, config bounds and transition routing')


def compile_java(source, android_jar, out):
    src = out/'src/com/projectinfinity/kodi';src.mkdir(parents=True,exist_ok=True)
    root = source/'tools/android/packaging/xbmc/src'
    names = ['Main','InfinityCoreBridge','InfinityRefreshController','InfinityExitDiagnostics',
             'InfinityDiagnosticFiles','XBMCMainView','XBMCInputDeviceListener','XBMCSettingsContentObserver',
             'XBMCMediaSession','InfinityPlatformHook','InfinityPlatformHooks','InfinitySystemMediaHook','InfinityAudioFocusHook']
    for name in names:
        data = (root/(name+'.java.in')).read_text()
        for key,val in {'@APP_PACKAGE@':'com.projectinfinity.kodi','@APP_NAME_LC@':'kodi','@APP_NAME@':'Infinity'}.items():
            data = data.replace(key,val)
        assert '@APP_' not in data, name
        (src/(name+'.java')).write_text(data)
    (src/'CompileOnlyStubs.java').write_text('''package com.projectinfinity.kodi;
// Unchanged TV/JSON-RPC collaborators and generated resource integers only.
class R {
 public static final class layout { public static final int activity_main=1; }
 public static final class id { public static final int VideoLayout=2; }
 public static final class drawable { public static final int notif_icon=3; }
}
class XBMCJsonRPC { public void updateLeanback(android.content.Context c) {} }
class XBMCProperties { public static int getIntProperty(String n,int d) {return d;} }
class XBMCBroadcastReceiver extends android.content.BroadcastReceiver {
 public void onReceive(android.content.Context c,android.content.Intent i) {}
}
''')
    tv=src/'channels/util';tv.mkdir(parents=True,exist_ok=True)
    (tv/'TvUtil.java').write_text('''package com.projectinfinity.kodi.channels.util;
public final class TvUtil {
 public static void scheduleSyncingChannel(android.content.Context c) {}
 public static void cancelAllScheduledJobs(android.content.Context c) {}
}
''')
    classes=out/'classes';classes.mkdir(exist_ok=True)
    run(['javac','-source','8','-target','8','-Xlint:unchecked','-cp',android_jar,'-d',classes,*src.rglob('*.java')])
    descriptors={}
    for owner in ['Main','XBMCMediaSession','InfinityAudioFocusHook']:
        result=run(['javap','-s','-p','-classpath',classes,'com.projectinfinity.kodi.'+owner],capture_output=True,text=True)
        (out/(owner+'.javap.txt')).write_text(result.stdout)
        descriptors[owner]=result.stdout
    actual={m[1]:m[2] for m in re.finditer(r'\bnative\s+\S+\s+(_infinity\w+)\([^)]*\);\s*descriptor:\s*(\S+)',descriptors['Main'])}
    expected=json.loads((ROOT/'patches/infinity-7.1-audited/contract.json').read_text())['jni']
    assert actual==expected, actual
    for method,descriptor in [('updateAudioPolicy','(I)V'),('acquireAudioFocus','(ILandroid/media/AudioManager$OnAudioFocusChangeListener;)Z'),('releaseAudioFocus','()Z')]:
        pattern=r'\b'+method+r'\([^)]*\);\s*descriptor:\s*(\S+)'
        assert re.search(pattern,descriptors['XBMCMediaSession'])[1]==descriptor,method
        assert '"'+descriptor+'"' in (source/'xbmc/platform/android/activity/JNIXBMCMediaSession.cpp').read_text()
    with zipfile.ZipFile(out/'compile-check.jar','w') as z:
        for f in classes.rglob('*.class'): z.write(f,f.relative_to(classes))
    print('PASS: full cumulative Android owners compile against API 34; old native ABI and new audio JNI descriptors match')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--android-jar',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    check_source(a.source)
    compile_java(a.source,a.android_jar,a.out/'java')
    exe=a.out/'policy-unit'
    run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-I'+str(ROOT/'patches/infinity-audio-policy'),ROOT/'tests/infinity_audio/test_policy.cpp','-o',exe])
    run([exe.resolve()])
    run([sys.executable,ROOT/'tests/infinity_audio/test_focus.py','--out',a.out/'focus-behavior'])
    run([sys.executable,ROOT/'tests/infinity_audio/test_addon.py'])
    (a.out/'validation.json').write_text(json.dumps({'source_connections':True,'android_api_compile':True,'jni_descriptor_check':True,'policy_unit_tests':True,'mock_focus_lifecycle_tests':True,'mock_addon_tests':True,'real_android_tested':False,'samsung_audio_eraser_eligibility':'unknown'},indent=2)+'\n')


if __name__=='__main__': main()
