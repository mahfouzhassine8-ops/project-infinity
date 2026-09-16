#!/usr/bin/env python3
"""Source-only background/resume delta over the successful Candidate 2 run 40.

Does not reconstruct, recompile, or patch Kodi's native engine or the installed skin.
The packager pairs this Android source with the exact run-40 native engine bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = Path('tools/android/packaging/xbmc')
MAIN = ANDROID / 'src/Main.java.in'
LIVE = ANDROID / 'src/InfinityLiveActivity.java.in'
MANIFEST = ANDROID / 'AndroidManifest.xml.in'
GRADLE = ANDROID / 'build.gradle.in'
INSTALL = Path('cmake/scripts/android/Install.cmake')
SERVICE = ANDROID / 'src/InfinityExtendedBackgroundService.java.in'
VERSION_CODE = 2103136
RELEASE = '1.0.9-Cobra-Background-Resume-RC1'
BASE_COMMIT = '2674c05e605afbf19a2fe54bdab1a552e76ec394'
BASE_APK_SHA256 = '8ef45e9c54a79e2295e295ce1fcdd3430322a0049c7ff5227804c15aed6b4c57'
BASE_ENGINE_SHA256 = '9783527356ec108fb3bdd61213dc6c7af9b227da3b81051163aa893a9fa358d0'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError('Unexpected source preimage: ' + repr(old[:100]))
    return text.replace(old, new, 1)


BACKGROUND_METHODS = '''  private void startCobraPlayer(ExoPlayer player) {
    if (mBackgroundStopped && !isCobraInPictureInPicture()) {
      mBackgroundResumePlayers.put(player, Boolean.TRUE);
      player.pause();
    } else {
      player.play();
    }
  }

  private void rememberAndPauseCobraPlayer(ExoPlayer player) {
    if (player == null) return;
    try {
      int state = player.getPlaybackState();
      // isPlaying() is false while buffering, even when playback is requested.
      if (player.getPlayWhenReady() && state != Player.STATE_IDLE && state != Player.STATE_ENDED) {
        mBackgroundResumePlayers.put(player, Boolean.TRUE);
        player.pause();
      }
    } catch (Exception ignored) {}
  }

  private boolean isCurrentCobraPlayer(ExoPlayer player) {
    if (player == mPlayer) return true;
    if (mMultiPlayers != null) {
      for (ExoPlayer current : mMultiPlayers) if (current == player) return true;
    }
    return false;
  }

  private void pauseCobraForBackground() {
    mBackgroundStopped = true;
    mMain.removeCallbacks(mStallWatchdog);
    mBufferingSince = 0L;
    rememberAndPauseCobraPlayer(mPlayer);
    if (mMultiPlayers != null) {
      for (ExoPlayer player : mMultiPlayers) rememberAndPauseCobraPlayer(player);
    }
  }

  private void resumeCobraAfterBackground() {
    mBackgroundStopped = false;
    if (isCobraInPictureInPicture()) return;
    ArrayList<ExoPlayer> paused = new ArrayList<>(mBackgroundResumePlayers.keySet());
    mBackgroundResumePlayers.clear();
    if (isFinishing()) return;
    for (ExoPlayer player : paused) {
      if (!isCurrentCobraPlayer(player)) continue;
      try {
        int state = player.getPlaybackState();
        if (state != Player.STATE_IDLE && state != Player.STATE_ENDED && !player.getPlayWhenReady()) {
          player.play();
        }
      } catch (Exception ignored) {}
    }
    if (mPlayer != null && mPlayer.getPlayWhenReady()
        && mPlayer.getPlaybackState() == Player.STATE_BUFFERING) {
      mMain.removeCallbacks(mStallWatchdog);
      mMain.postDelayed(mStallWatchdog, 4000L);
    }
  }

'''


def apply(source: Path, receipt: Path) -> None:
    paths = (MAIN, LIVE, MANIFEST, GRADLE, INSTALL)
    original = {p: (source / p).read_bytes() for p in paths}
    baseline = json.loads((ROOT / 'stability/background-resume-preimage.json').read_text())
    for path, data in original.items():
        if sha(data) != baseline[str(path)]:
            raise ValueError('Not the exact reconstructed run-40 source: ' + str(path))
    text = {p: b.decode('utf-8') for p, b in original.items()}
    text[MAIN] = once(text[MAIN], '    infinityApplyPlayerRotation("resume");\n',
                     '    infinityApplyPlayerRotation("resume");\n    InfinityExtendedBackgroundService.sync(this);\n')
    text[MAIN] = once(text[MAIN], '    mInfinityDestroyed = true;\n',
                     '    if (isFinishing()) InfinityExtendedBackgroundService.stopForExit(this);\n    mInfinityDestroyed = true;\n')
    java = text[LIVE]
    java = once(java, '    super.onResume();\n',
                '    super.onResume();\n    InfinityExtendedBackgroundService.sync(this);\n')
    java = once(java, '  private boolean mPausedForBackground = false;\n',
                '  private boolean mBackgroundStopped = false;\n'
                '  private final java.util.IdentityHashMap<ExoPlayer, Boolean> mBackgroundResumePlayers =\n'
                '      new java.util.IdentityHashMap<>();\n')
    java = once(java, '    if (!isCobraInPictureInPicture() && hasCobraVideo()) pauseCobraForBackground();',
                '    if (!isCobraInPictureInPicture()) pauseCobraForBackground();')
    start = java.index('  private void pauseCobraForBackground() {')
    end = java.index('  private void rebuildCobraShellIfNeeded() {', start)
    java = java[:start] + BACKGROUND_METHODS + java[end:]
    java = once(java, '      if (mPlayer != null && mPlayer.getPlaybackState() == Player.STATE_BUFFERING) {',
                '      if ((mBackgroundStopped && !isCobraInPictureInPicture())\n'
                '          || mPlayer == null || !mPlayer.getPlayWhenReady()) {\n'
                '        mBufferingSince = 0L; return;\n'
                '      }\n'
                '      if (mPlayer.getPlaybackState() == Player.STATE_BUFFERING) {')
    java = once(java, '      mPlayer.prepare();\n      mPlayer.play();',
                '      mPlayer.prepare();\n      startCobraPlayer(mPlayer);')
    java = once(java, 'player.setMediaItem(mediaItem(mMultiChannels[index].primaryUrl)); player.prepare(); player.play();',
                'player.setMediaItem(mediaItem(mMultiChannels[index].primaryUrl)); player.prepare(); startCobraPlayer(player);')
    java = once(java, '  private void releaseSinglePlayer() {\n    if (mPlayer != null) {',
                '  private void releaseSinglePlayer() {\n    if (mPlayer != null) {\n      mBackgroundResumePlayers.remove(mPlayer);')
    java = once(java, '      ExoPlayer player = mMultiPlayers[i]; if (player == null) continue;\n',
                '      ExoPlayer player = mMultiPlayers[i]; if (player == null) continue;\n      mBackgroundResumePlayers.remove(player);\n')
    # Only this settings pane gets a scrolling container, so the extra control is
    # reachable on cover-screen landscape. Existing settings actions are retained.
    settings_start = java.index('  private void showSettings() {')
    settings_end = java.index('  private void editCustomEpg() {', settings_start)
    settings = java[settings_start:settings_end]
    button = '''    Button extendedBackground = action(
        InfinityExtendedBackgroundService.isEnabled(this)
            ? "EXTENDED BACKGROUND MODE • ON" : "EXTENDED BACKGROUND MODE • OFF");
    extendedBackground.setOnClickListener(v -> {
      boolean enable = !InfinityExtendedBackgroundService.isEnabled(this);
      if (enable && !InfinityExtendedBackgroundService.notificationsAllowed(this)) {
        new AlertDialog.Builder(this).setTitle("Allow Infinity notifications")
            .setMessage("Extended Background Mode needs its visible notification and Turn off control. Allow Infinity notifications in Android, then enable this mode again.")
            .setPositiveButton("OPEN SETTINGS", (d, w) ->
                InfinityExtendedBackgroundService.openNotificationSettings(this))
            .setNegativeButton("Cancel", null).show();
        return;
      }
      boolean accepted = InfinityExtendedBackgroundService.setEnabled(this, enable);
      toast(!accepted ? "Android refused background mode. No change was made."
          : enable ? "Background mode requested • the notification confirms activity"
          : "Background mode off");
      showSettings();
    });

'''
    settings = once(settings, '    TextView themeInfo = text(\n', button + '    TextView themeInfo = text(\n')
    settings = once(settings, '    list.addView(chooser, new LinearLayout.LayoutParams(\n',
                    '    list.addView(extendedBackground, new LinearLayout.LayoutParams(\n'
                    '        LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));\n'
                    '    list.addView(chooser, new LinearLayout.LayoutParams(\n')
    settings = once(settings,
                    '    mStage.addView(list, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));',
                    '    ScrollView settingsScroll = new ScrollView(this);\n'
                    '    settingsScroll.setFillViewport(true);\n'
                    '    settingsScroll.addView(list);\n'
                    '    mStage.addView(settingsScroll, new LinearLayout.LayoutParams(\n        LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));')
    assert 'import android.widget.ScrollView;' in java
    text[LIVE] = java[:settings_start] + settings + java[settings_end:]
    text[GRADLE] = once(text[GRADLE], 'versionCode 2103134', f'versionCode {VERSION_CODE}')
    text[GRADLE] = once(text[GRADLE], 'versionName "1.0.9-Cobra-Full-Feature-Candidate-2"', f'versionName "{RELEASE}"')
    text[INSTALL] = once(text[INSTALL], '                  src/InfinityCobraBootReceiver.java\n',
                         '                  src/InfinityCobraBootReceiver.java\n                  src/InfinityExtendedBackgroundService.java\n')
    text[MANIFEST] = once(text[MANIFEST], '<uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />\n',
                          '<uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />\n'
                          '<uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />\n')
    text[MANIFEST] = once(text[MANIFEST], '        <service\n            android:name=".InfinityCobraRecordingService"\n',
                          '        <service android:name=".InfinityExtendedBackgroundService"\n'
                          '            android:exported="false" android:stopWithTask="false"\n'
                          '            android:foregroundServiceType="specialUse">\n'
                          '            <property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"\n'
                          '                android:value="User-enabled Infinity media session continuity with visible stop control; ends on explicit task removal." />\n'
                          '        </service>\n'
                          '        <service\n            android:name=".InfinityCobraRecordingService"\n')
    ET.fromstring(text[MANIFEST])
    text[SERVICE] = (ROOT / 'patches/infinity-background/InfinityExtendedBackgroundService.java.in').read_text()
    for path, value in text.items():
        (source / path).write_text(value, encoding='utf-8')
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({
        'schema': 1, 'base_source_commit': BASE_COMMIT,
        'base_apk_sha256': BASE_APK_SHA256, 'native_engine_sha256': BASE_ENGINE_SHA256,
        'version_code': VERSION_CODE, 'version_name': RELEASE,
        'default_enabled': False, 'wake_lock': False,
        'native_source_modified': False, 'skin_modified': False,
        'rotation_policy_preserved': True, 'cobra_handoff_preserved': True,
        'per_player_resume': True, 'buffering_background_guard': True,
        'runtime_device_tested': False,
        'files': {str(p): {'before': sha(original[p]) if p in original else None,
                           'after': sha(value.encode())} for p, value in text.items()}
    }, indent=2, sort_keys=True) + '\n')
    print('PASS: exact-source Android background/resume delta applied; native engine/skin unchanged')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    apply(args.source, args.receipt)

if __name__ == '__main__':
    main()
