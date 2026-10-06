#!/usr/bin/env python3
"""Exact 3312 parent -> tested 3315 close route + Infinity-only busy arc."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'android-task-close-2103315'))
import android_task_close as close315

PREFIX = 'tools/android/packaging/xbmc/src/'
GEAR = PREFIX + 'InfinityGlassChooser.java.in'
SPLASH = PREFIX + 'Splash.java.in'
ALLOWED = sorted([close315.TARGET, GEAR, SPLASH])
replace_once = close315.replace_once
sha = close315.sha
snapshot = close315.snapshot


def transform_gear(text):
    start = text.index('    private final RectF closeArc=new RectF();')
    end = text.index('    @Override protected void onAttachedToWindow()', start)
    text = text[:start] + (HERE / 'gear-progress.java.fragment').read_text() + text[end:]
    start = text.index('        float sweep=displayedCloseSweep(SystemClock.uptimeMillis());')
    end = text.index('        p.setStrokeCap(Paint.Cap.BUTT);', start)
    text = text[:start] + '''        long now=SystemClock.uptimeMillis();
        float sweep=displayedCloseSweep(now);
        closeArc.set(cx-radius,cy-radius,cx+radius,cy+radius);
        p.setColor(closeFailed?0xffffac45:(light?0xff079de8:0xff39caff));
        if(sweep>0)c.drawArc(closeArc,displayedCloseStart(now),sweep,false,p);
''' + text[end:]
    return text


def transform_splash(text):
    text = replace_once(text, '''  protected void startXBMC()
  {
    if (isFinishing() || isDestroyed() || mInfinityLaunchQueued) return;
''', '''  // Cobra owns its own Android/player lifecycle. A remembered Cobra launch
  // bypasses Kodi state, preparation and shutdown, but never overrides a choice.
  private boolean infinityLaunchPreferredCobra() {
    if(mInfinityChooserVisible || mInfinityPendingMain!=null || mInfinityLaunchQueued)return false;
    Intent incoming=getIntent();
    if(incoming!=null && incoming.getAction()!=null && !Intent.ACTION_MAIN.equals(incoming.getAction()))return false;
    if(!"live".equals(getSharedPreferences(INFINITY_EXPERIENCE_PREFS,MODE_PRIVATE)
        .getString(INFINITY_EXPERIENCE_DEFAULT,"")))return false;
    launchInfinityExperience("live",false,false);return true;
  }

  protected void startXBMC()
  {
    if (isFinishing() || isDestroyed() || mInfinityLaunchQueued) return;
    if (infinityLaunchPreferredCobra()) return;
''')
    text = replace_once(text, '''  private void launchInfinityExperience(String experience,boolean explicit,boolean safe)
  {
    if (isFinishing() || isDestroyed() || mInfinityLaunchQueued) return;
    if (InfinityKodiShutdown.pending()) {''', '''  private void launchInfinityExperience(String experience,boolean explicit,boolean safe)
  {
    if (isFinishing() || isDestroyed() || (!"live".equals(experience) && mInfinityLaunchQueued)) return;
    if (!"live".equals(experience) && InfinityKodiShutdown.pending()) {''')
    text = replace_once(text, '''      // Preserve Cobra's original routing and flags exactly.
      intent.addFlags(Intent.FLAG_ACTIVITY_PREVIOUS_IS_TOP);''', '''      // Cancel only this chooser's queued Kodi handoff; never close Cobra or
      // signal the Kodi process. Preserve Cobra's routing, extras and flags.
      mInfinityPendingMain=null;mInfinityLaunchQueued=false;mInfinityKodiLaunchToken="";
      if(mInfinityHandoff!=null)mInfinityHandoff.close();
      intent.addFlags(Intent.FLAG_ACTIVITY_PREVIOUS_IS_TOP);''')
    text = replace_once(text, '''  private void infinityInitializeStartup() {
    if (isFinishing() || isDestroyed()) return;
    if(!mInfinityKodiStateReady)return;''', '''  private void infinityInitializeStartup() {
    if (isFinishing() || isDestroyed()) return;
    if(infinityLaunchPreferredCobra())return;
    if(!mInfinityKodiStateReady)return;''')
    return text


def apply(source, proof, receipt):
    parent = json.loads(proof.read_text())['after']
    if len(parent) != close315.SOURCE_COUNT or sha(json.dumps(parent, sort_keys=True, separators=(',', ':')).encode()) != close315.PARENT_MAP:
        raise ValueError('Not the complete exact locked 2103312 source proof')
    before = snapshot(source)
    if before != parent:
        raise ValueError('Source differs from locked 2103312')
    for name, transform in [(close315.TARGET, close315.transform), (GEAR, transform_gear), (SPLASH, transform_splash)]:
        target = source / name
        target.write_text(transform(target.read_text()))
    after = snapshot(source)
    changed = sorted(n for n in before if before[n] != after[n])
    if changed != ALLOWED or before.keys() != after.keys():
        raise ValueError('Unexpected source delta')
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({'base_source_map': close315.PARENT_MAP, 'before': before, 'after': after,
        'changed': changed, 'native_engine_changed': False, 'locked': False, 'device_verified': False}, indent=2, sort_keys=True) + '\n')


def verify(source, receipt):
    proof = json.loads(receipt.read_text())
    if snapshot(source) != proof['after'] or proof['changed'] != ALLOWED or proof['native_engine_changed']:
        raise ValueError('Source changed after validation')
    gear = (source / GEAR).read_text()
    if 'completedCloseStages' in gear or 'closeTargetSweep' in gear or 'sameClose && state.complete && observed' not in gear:
        raise ValueError('Arc must be indeterminate until matching confirmed completion')
    splash = (source / SPLASH).read_text()
    if 'if (!"live".equals(experience) && InfinityKodiShutdown.pending())' not in splash:
        raise ValueError('Cobra inherits the Kodi shutdown gate')
    normal = (source / close315.TARGET).read_text()
    normal = normal[normal.index('static boolean requestNormal'):normal.index('static void afterStop')]
    if 'owner.finishAndRemoveTask();' not in normal or 'request_string(QUIT)' in normal:
        raise ValueError('Tested 3315 task-removal route changed')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['apply', 'verify'])
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--proof', type=Path)
    p.add_argument('--receipt', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'apply':
        if not a.proof: p.error('apply requires --proof')
        apply(a.source, a.proof, a.receipt)
    verify(a.source, a.receipt)
    print('PASS: exact 3312 + tested 3315 close route; Infinity busy arc and independent Cobra dispatch')


if __name__ == '__main__': main()
