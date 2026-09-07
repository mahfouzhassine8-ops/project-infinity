from pathlib import Path

root = Path('kodi')
main = root / 'tools/android/packaging/xbmc/src/Main.java.in'
media = root / 'tools/android/packaging/xbmc/src/XBMCMediaSession.java.in'
state_src = Path('engine/src/InfinityEngineState.java.in')
state_dst = root / 'tools/android/packaging/xbmc/src/InfinityEngineState.java.in'

if not main.exists() or not media.exists() or not state_src.exists():
    raise SystemExit('Infinity Phase 1 preflight failed: expected source file missing')

main_text = main.read_text()
if 'import android.content.res.Configuration;' not in main_text:
    main_text = main_text.replace('import android.content.pm.ResolveInfo;\n', 'import android.content.pm.ResolveInfo;\nimport android.content.res.Configuration;\n')

anchor = '  @Override\n  public void onPause()\n'
method = '''  @Override\n  public void onConfigurationChanged(Configuration newConfig)\n  {\n    super.onConfigurationChanged(newConfig);\n    InfinityEngineState.updateWindow(this, newConfig);\n  }\n\n'''
if 'InfinityEngineState.updateWindow(this, newConfig);' not in main_text:
    if anchor not in main_text:
        raise SystemExit('Infinity Phase 1 failed: Main.java.in anchor changed')
    main_text = main_text.replace(anchor, method + anchor)

resume_anchor = '  public void onResume()\n  {\n    super.onResume();\n'
if 'InfinityEngineState.updateWindow(this, getResources().getConfiguration());' not in main_text:
    if resume_anchor not in main_text:
        raise SystemExit('Infinity Phase 1 failed: onResume anchor changed')
    main_text = main_text.replace(
        resume_anchor,
        resume_anchor + '\n    InfinityEngineState.updateWindow(this, getResources().getConfiguration());\n'
    )

main.write_text(main_text)

media_text = media.read_text()
old = '''  private void updatePlaybackState(PlaybackState mystate)\n  {\n    mSession.setPlaybackState(mystate);\n  }\n'''
new = '''  private void updatePlaybackState(PlaybackState mystate)\n  {\n    mSession.setPlaybackState(mystate);\n    InfinityEngineState.updatePlaybackState(mystate);\n  }\n'''
if 'InfinityEngineState.updatePlaybackState(mystate);' not in media_text:
    if old not in media_text:
        raise SystemExit('Infinity Phase 1 failed: XBMCMediaSession.java.in anchor changed')
    media_text = media_text.replace(old, new)
media.write_text(media_text)

state_dst.write_text(state_src.read_text())

# Hard checks: fail immediately instead of spending ~40 minutes compiling the wrong tree.
assert 'InfinityEngineState.updateWindow(this, newConfig);' in main.read_text()
assert 'InfinityEngineState.updatePlaybackState(mystate);' in media.read_text()
assert state_dst.exists()
print('Infinity Engine Phase 1 source patch applied and verified')
