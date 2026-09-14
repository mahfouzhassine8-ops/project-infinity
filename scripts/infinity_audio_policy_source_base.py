#!/usr/bin/env python3
"""Cumulative v5 + native media + event-driven audio policy (source-built).

Run on a clean, pinned Kodi 21.3 source tree. Never binary-patches a native engine.
Policy config is read on new playback/stream boundaries, not via a polling service.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'patches/infinity-audio-policy'
VERSION_CODE = 2103120
VERSION_NAME = '1.0.8-Cumulative-Audio-Policy-1'
NATIVE_SHA = '179b66503666b2b2bdd0b35ffc1d22cd0e5654d1'
RESPONSIVE_SHA = '9407bd8e14b02b435f86333da2e4469467eaa151'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f'Expected one exact source anchor, got {text.count(old)}: {old[:180]!r}')
    return text.replace(old, new, 1)


def module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace('-', '_'), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prepare(source: Path, receipts: Path) -> None:
    receipts.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(ROOT/'scripts/infinity71.py'), 'source', '--source', str(source)], check=True)
    for script, receipt in (
        ('infinity_1_0_6_source.py', 'source-1.0.6.json'),
        ('infinity_1_0_7_compat_source.py', 'source-1.0.7.json'),
        ('infinity_diagnostics_source.py', 'exit-diagnostics.json'),
        ('infinity_1_0_8_refresh_source.py', 'source-1.0.8.json'),
        ('infinity_1_0_8_media_source.py', 'source-native-media.json'),
    ):
        subprocess.run([sys.executable, str(ROOT/'scripts'/script), str(source), '--receipt', str(receipts/receipt)], check=True)
    # The original v5 script includes an old Gradle-version transform. Import only
    # its THREE exact v4->v5 capability transforms; final versioning belongs here.
    v5 = module(ROOT/'scripts/infinity-responsive-v5.py')
    c = v5.load_contract()
    paths = [p for p in v5.TRANSFORMS if not p.endswith('build.gradle.in')]
    for rel in paths:
        if digest(source/rel) != c['preimage_files'][rel]:
            raise ValueError('Responsive preimage changed: '+rel)
    for rel in paths:
        path = source/rel
        path.write_text(v5.TRANSFORMS[rel](path.read_text()), encoding='utf-8')
    print('PASS: exact responsive v5 capability transforms applied over complete native-media stack')


def patch_audio(source: Path) -> list[str]:
    edits: dict[str, str] = {}
    def get(rel):
        return edits.get(rel, (source/rel).read_text())
    def put(rel, text):
        edits[rel] = text
    def change(rel, old, new):
        put(rel, once(get(rel), old, new))

    # Semantic media type travels WITH the stream. This avoids guessing HasVideo
    # from a global player before its streams are opened, and fixes same-PCM reuse.
    rel='xbmc/cores/AudioEngine/Utils/AEAudioFormat.h'
    change(rel, '  AEAudioFormat()\n', '''  // Infinity API 1 semantic content; PCM geometry remains independent.
  // 0=unspecified (music for streams), 2=music, 3=video/movie, 4=UI sounds.
  int m_infinityContentType{0};

  AEAudioFormat()
''')
    rel='xbmc/cores/VideoPlayer/Process/ProcessInfo.h'
    change(rel, '  // player video\n', '''#if defined(TARGET_ANDROID)
  // Published by selected-video-stream events, read by the audio decoder thread.
  void SetInfinityAudioHasVideo(bool value) { m_infinityAudioHasVideo.store(value); }
  bool InfinityAudioHasVideo() const { return m_infinityAudioHasVideo.load(); }
#endif

  // player video
''')
    change(rel, '  // player states\n  CCriticalSection m_stateSection;\n', '''#if defined(TARGET_ANDROID)
  std::atomic_bool m_infinityAudioHasVideo{false};
#endif

  // player states
  CCriticalSection m_stateSection;
''')
    rel='xbmc/cores/VideoPlayer/VideoPlayer.cpp'
    change(rel, '  // open audio stream\n  valid = false;\n', '''#if defined(TARGET_ANDROID)
  m_processInfo->SetInfinityAudioHasVideo(valid);
#endif

  // open audio stream
  valid = false;
''')
    change(rel, '  m_HasVideo = true;\n', '''  m_HasVideo = true;
#if defined(TARGET_ANDROID)
  m_processInfo->SetInfinityAudioHasVideo(true);
#endif
''')
    # Do not dereference processInfo in the constructor before it is allocated.
    change(rel, '  m_HasVideo = false;\n  m_HasAudio = false;\n\n  CLog::Log(LOGINFO, "VideoPlayer: finished waiting");', '''  m_HasVideo = false;
  m_HasAudio = false;
#if defined(TARGET_ANDROID)
  m_processInfo->SetInfinityAudioHasVideo(false);
#endif

  CLog::Log(LOGINFO, "VideoPlayer: finished waiting");''')
    rel='xbmc/cores/VideoPlayer/VideoPlayerAudio.cpp'
    change(rel, '    // we have successfully decoded an audio frame, setup renderer to match\n', '''#if defined(TARGET_ANDROID)
    // Do this BEFORE renderer validation; a TV->radio transition may keep the
    // same sample rate/channels but must not keep the old content classification.
    audioframe.format.m_infinityContentType = m_processInfo.InfinityAudioHasVideo() ? 3 : 2;
#endif

    // we have successfully decoded an audio frame, setup renderer to match
''')
    rel='xbmc/cores/VideoPlayer/AudioSinkAE.h'
    change(rel, '  AEDataFormat m_dataFormat;\n', '  int m_infinityContentType{0};\n  AEDataFormat m_dataFormat;\n')
    rel='xbmc/cores/VideoPlayer/AudioSinkAE.cpp'
    change(rel, '  m_dataFormat = audioframe.format.m_dataFormat;\n', '  m_infinityContentType = audioframe.format.m_infinityContentType;\n  m_dataFormat = audioframe.format.m_dataFormat;\n')
    change(rel, '  if (audioframe.passthrough != m_bPassthrough)\n', '''  if (m_infinityContentType != audioframe.format.m_infinityContentType)
    return false;

  if (audioframe.passthrough != m_bPassthrough)
''')

    # Reopen an AudioTrack through AE's EXISTING serialized Configure path, not
    # from a Java/UI callback and never inside AudioTrackWrite().
    rel='xbmc/cores/AudioEngine/Engines/ActiveAE/ActiveAE.cpp'
    change(rel, '#include "ActiveAE.h"\n', '''#include "ActiveAE.h"
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAudioPolicy.h"
#endif
''')
    old='  return inputFormat;\n}\n\nvoid CActiveAE::Configure'
    change(rel, old, '''#if defined(TARGET_ANDROID)
  int role = INFINITY_AUDIO::SONIFICATION;
  if (desiredFmt != nullptr)
    role = INFINITY_AUDIO::NormalizeStreamRole(desiredFmt->m_infinityContentType);
  else
  {
    bool selected = false;
    for (const auto* stream : m_streams)
      if (!stream->m_drain)
      {
        role = INFINITY_AUDIO::SelectStreamRole(role, stream->m_format.m_infinityContentType);
        selected = true;
      }
    // Preserve draining content until removed; do not switch a still-draining
    // video to GUI sound classification and flush its last samples.
    if (!selected && !m_streams.empty())
      role = INFINITY_AUDIO::NormalizeStreamRole(m_streams.front()->m_format.m_infinityContentType);
  }
  inputFormat.m_infinityContentType = role;
#endif
  return inputFormat;
}

void CActiveAE::Configure''')
    change(rel, '  m_sinkRequestFormat = inputFormat;\n', '''  m_sinkRequestFormat = inputFormat;
#if defined(TARGET_ANDROID)
  m_sinkRequestFormat.m_infinityContentType = INFINITY_AUDIO::Resolve(inputFormat.m_infinityContentType);
#endif
''')
    change(rel, '      m_currDevice.compare(dev.name) != 0 || m_settings.driver.compare(dev.driver) != 0)\n', '''      m_currDevice.compare(dev.name) != 0 || m_settings.driver.compare(dev.driver) != 0 ||
      m_sinkRequestFormat.m_infinityContentType != m_sinkFormat.m_infinityContentType)
''')
    change(rel, '  // create the stream\n  CActiveAEStream *stream;\n', '''#if defined(TARGET_ANDROID)
  INFINITY_AUDIO::Reload();
#endif
  // create the stream
  CActiveAEStream *stream;
''')
    start=get(rel).index('bool CActiveAE::NeedReconfigureSink()')
    end=get(rel).index('\nbool CActiveAE::InitSink()',start)
    body=get(rel)[start:end]
    body=once(body, '  ApplySettingsToFormat(newFormat, m_settings);\n', '''  ApplySettingsToFormat(newFormat, m_settings);
#if defined(TARGET_ANDROID)
  newFormat.m_infinityContentType = INFINITY_AUDIO::Resolve(newFormat.m_infinityContentType);
#endif
''')
    body=once(body, '  return !CompareFormat(newFormat, m_sinkFormat) ||', '''  return newFormat.m_infinityContentType != m_sinkFormat.m_infinityContentType ||
         !CompareFormat(newFormat, m_sinkFormat) ||''')
    text=get(rel);put(rel,text[:start]+body+text[end:])

    rel='xbmc/cores/AudioEngine/Sinks/AESinkAUDIOTRACK.h'
    change(rel, 'int encoding, int bufferSize);', 'int encoding, int bufferSize, int contentType = 2);')
    rel='xbmc/cores/AudioEngine/Sinks/AESinkAUDIOTRACK.cpp'
    change(rel, '#include "AESinkAUDIOTRACK.h"\n', '#include "AESinkAUDIOTRACK.h"\n#include "platform/android/activity/InfinityAudioPolicy.h"\n')
    change(rel, 'int encoding, int bufferSize)\n{', 'int encoding, int bufferSize, int contentType)\n{')
    change(rel, '    attrBuilder.setContentType(CJNIAudioAttributes::CONTENT_TYPE_MUSIC);', '''    attrBuilder.setContentType(INFINITY_AUDIO::ValidContent(contentType)
                                   ? contentType : CJNIAudioAttributes::CONTENT_TYPE_MUSIC);''')
    change(rel, '                                m_encoding, m_min_buffer_size);', '                                m_encoding, m_min_buffer_size, m_format.m_infinityContentType);')
    change(rel, '  format = m_format;\n', '  INFINITY_AUDIO::NoteTrack(m_format.m_infinityContentType);\n  format = m_format;\n')

    # Java-side focus adapter caches the exact AudioFocusRequest and uses Kodi's
    # existing native focus listener. JNI calls are checked by the Java preflight.
    rel='xbmc/platform/android/activity/XBMCApp.cpp'
    change(rel, '#include "XBMCApp.h"\n', '#include "XBMCApp.h"\n#include "InfinityAudioPolicy.h"\n')
    text=get(rel); start=text.index('bool CXBMCApp::AcquireAudioFocus()'); end=text.index('\nvoid CXBMCApp::RequestVisibleBehind',start)
    text=text[:start]+'''bool CXBMCApp::AcquireAudioFocus()
{
  const auto& components = CServiceBroker::GetAppComponents();
  const auto player = components.GetComponent<CApplicationPlayer>();
  const int content = INFINITY_AUDIO::Resolve(player->HasVideo() ? INFINITY_AUDIO::MOVIE : INFINITY_AUDIO::MUSIC);
  return m_mediaSession && m_mediaSession->acquireAudioFocus(content, m_audioFocusListener);
}

bool CXBMCApp::ReleaseAudioFocus()
{
  return !m_mediaSession || m_mediaSession->releaseAudioFocus();
}
''' + text[end:]
    put(rel,text)
    change(rel, 'void CXBMCApp::OnPlayBackStarted()\n{\n', 'void CXBMCApp::OnPlayBackStarted()\n{\n  if (m_playback_state == PLAYBACK_STATE_STOPPED)\n    INFINITY_AUDIO::Reload();\n')
    change(rel, '    m_mediaSession->updatePlaybackState(builder.build());\n', '''    const int content = INFINITY_AUDIO::Resolve(appPlayer->HasVideo() ? INFINITY_AUDIO::MOVIE : INFINITY_AUDIO::MUSIC);
    m_mediaSession->updateAudioPolicy(content);
    m_mediaSession->updatePlaybackState(builder.build());
    // OnPlay can precede stream discovery. Correct focus on the existing AV
    // state event when video becomes known, including live TV/radio transitions.
    if ((m_playback_state & PLAYBACK_STATE_PLAYING) &&
        ((oldPlayState ^ m_playback_state) & PLAYBACK_STATE_VIDEO))
      AcquireAudioFocus();
''')
    rel='xbmc/platform/android/activity/JNIXBMCMediaSession.h'
    change(rel, '  void activate(bool state);\n', '''  void activate(bool state);
  void updateAudioPolicy(int content);
  bool acquireAudioFocus(int content, const CJNIBase& listener);
  bool releaseAudioFocus();
''')
    rel='xbmc/platform/android/activity/JNIXBMCMediaSession.cpp'
    change(rel, 'void CJNIXBMCMediaSession::updatePlaybackState', '''void CJNIXBMCMediaSession::updateAudioPolicy(int content)
{
  call_method<void>(m_object, "updateAudioPolicy", "(I)V", static_cast<jint>(content));
}

bool CJNIXBMCMediaSession::acquireAudioFocus(int content, const CJNIBase& listener)
{
  return call_method<jboolean>(m_object, "acquireAudioFocus",
      "(ILandroid/media/AudioManager$OnAudioFocusChangeListener;)Z",
      static_cast<jint>(content), listener.get_raw());
}

bool CJNIXBMCMediaSession::releaseAudioFocus()
{
  return call_method<jboolean>(m_object, "releaseAudioFocus", "()Z");
}

void CJNIXBMCMediaSession::updatePlaybackState''')
    rel='xbmc/platform/android/activity/CMakeLists.txt'
    change(rel, 'set(SOURCES android_main.cpp\n', 'set(SOURCES android_main.cpp\n            InfinityAudioPolicy.cpp\n')
    change(rel, 'set(HEADERS AndroidFeatures.h\n', 'set(HEADERS AndroidFeatures.h\n            InfinityAudioPolicy.h\n')
    rel='xbmc/windowing/android/WinSystemAndroid.cpp'
    change(rel, '      home->SetProperty("Infinity.BridgeVersion", CInfinityBridgeState::VERSION);', '''      home->SetProperty("Infinity.AudioPolicyApi", 1);
      home->SetProperty("Infinity.CumulativeBuild", "1.0.8-Cumulative-Audio-Policy-1");
      home->SetProperty("Infinity.BridgeVersion", CInfinityBridgeState::VERSION);''')

    rel='tools/android/packaging/xbmc/src/XBMCMediaSession.java.in'
    change(rel, '  private MediaSession mSession = null;\n', '  private MediaSession mSession = null;\n  private final InfinityAudioFocusHook mInfinityFocus;\n')
    change(rel, '    this.mSession = new MediaSession(Main.MainActivity, "Infinity_media");\n', '    mInfinityFocus = new InfinityAudioFocusHook(Main.MainActivity);\n    this.mSession = new MediaSession(Main.MainActivity, "Infinity_media");\n')
    change(rel, '  public void activate(boolean state)\n', '''  public void updateAudioPolicy(int content)
  {
    InfinityPlatformHooks.onAudioPolicy(mSession, content);
  }
  public boolean acquireAudioFocus(int content, android.media.AudioManager.OnAudioFocusChangeListener listener)
  {
    return mInfinityFocus.acquire(content, listener);
  }
  public boolean releaseAudioFocus() { return mInfinityFocus.release(); }
  public void activate(boolean state)
''')
    # Publish the state/metadata to Android before building its notification.
    change(rel, '    mSession.setPlaybackState(state);\n', '    mSession.setPlaybackState(state);\n    InfinityPlatformHooks.onMediaSessionActive(mSession, mSession.isActive());\n')
    change(rel, '    mSession.setMetadata(data);\n', '    mSession.setMetadata(data);\n    InfinityPlatformHooks.onMediaSessionActive(mSession, mSession.isActive());\n')
    rel='tools/android/packaging/xbmc/src/InfinityPlatformHook.java.in'
    change(rel, '  void onMediaSessionCreated(MediaSession session) { }', '''  void onAudioPolicy(MediaSession session, int content) { }
  void onMediaSessionCreated(MediaSession session) { }''')
    rel='tools/android/packaging/xbmc/src/InfinityPlatformHooks.java.in'
    change(rel, '  static final int API_VERSION = 1;', '  static final int API_VERSION = 2;')
    change(rel, '  private static void failed(', '''  static void onAudioPolicy(MediaSession session, int content)
  {
    for (InfinityPlatformHook hook : HOOKS)
    {
      try { hook.onAudioPolicy(session, content); }
      catch (Throwable error) { failed(hook, "audio-policy", error); }
    }
  }

  private static void failed(''')
    rel='tools/android/packaging/xbmc/src/InfinitySystemMediaHook.java.in'
    change(rel, '        .setContentType(AudioAttributes.CONTENT_TYPE_MOVIE)', '        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)')
    change(rel, '    extras.putBoolean("com.projectinfinity.audio_eraser_compat_candidate", true);', '    extras.putInt("com.projectinfinity.audio_policy_api", 1);')
    change(rel, '  private void ensureChannel()\n', '''  @Override
  void onAudioPolicy(MediaSession session, int content)
  {
    int safe = content >= AudioAttributes.CONTENT_TYPE_SPEECH &&
        content <= AudioAttributes.CONTENT_TYPE_SONIFICATION
        ? content : AudioAttributes.CONTENT_TYPE_MUSIC;
    session.setPlaybackToLocal(new AudioAttributes.Builder()
        .setUsage(AudioAttributes.USAGE_MEDIA).setContentType(safe).build());
  }

  private void ensureChannel()
''')
    # Remove premature notification updates in decorators; XBMCMediaSession now
    # notifies only after committing the actual Android state.
    text=get(rel)
    text=once(text,'    playbackState = builder.build();\n    publish(session);','    playbackState = builder.build();')
    text=once(text,'    metadata = data;\n    publish(session);','    metadata = data;')
    put(rel,text)
    rel='cmake/scripts/android/Install.cmake'
    change(rel, '                  src/InfinitySystemMediaHook.java\n', '                  src/InfinitySystemMediaHook.java\n                  src/InfinityAudioFocusHook.java\n')
    rel='tools/android/packaging/xbmc/build.gradle.in'
    change(rel,'versionCode 2103109',f'versionCode {VERSION_CODE}')
    change(rel,'versionName "21.3-Infinity-1.0.8-Native-Media"',f'versionName "{VERSION_NAME}"')

    # Stage all transforms before mutating source; anchors must all match.
    for rel, text in edits.items():
        (source/rel).write_text(text, encoding='utf-8')
    new_files = {
        'xbmc/platform/android/activity/InfinityAudioPolicy.h': 'InfinityAudioPolicy.h',
        'xbmc/platform/android/activity/InfinityAudioPolicy.cpp': 'InfinityAudioPolicy.cpp',
        'tools/android/packaging/xbmc/src/InfinityAudioFocusHook.java.in': 'InfinityAudioFocusHook.java.in',
    }
    for rel, name in new_files.items():
        if (source/rel).exists(): raise ValueError('Unexpected existing policy owner: '+rel)
        (source/rel).write_bytes((PATCH/name).read_bytes())
    return sorted([*edits, *new_files])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('--receipts',type=Path,required=True)
    a=p.parse_args(); source=a.source.resolve(); receipts=a.receipts.resolve()
    prepare(source,receipts)
    changed=patch_audio(source)
    receipt={
      'schema':1,'release':VERSION_NAME,'versionCode':VERSION_CODE,
      'kodi_commit':'a3a448d26b8d560a65655dab2cd122994dc4e146',
      'responsive_base':RESPONSIVE_SHA,'native_media_base':NATIVE_SHA,
      'bridge_version':5,'platform_hook_api':2,'audio_policy_api':1,
      'single_media_session':True,'skin_redesign':False,
      'runtime_tested':False,'samsung_audio_eraser_eligibility':'unknown',
      'config':'special://profile/infinity-audio-policy.json',
      'config_applies':'new playback/stream; stop then play to apply a manual change',
      'audio_track_creation_hook':True,'audio_focus_adapter':True,
      'same_format_content_transitions_reconfigure_sink':True,
      'files':{rel:digest(source/rel) for rel in changed},
    }
    (receipts/'cumulative-source.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(f'PASS: {VERSION_NAME} source prepared; {len(changed)} audio/integration files; device test pending')

if __name__=='__main__': main()
