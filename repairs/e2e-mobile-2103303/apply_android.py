#!/usr/bin/env python3
"""Narrow first repair tranche. Apply only to the verified 2103302 Android shell.

This is not the complete user brief and must not be advertised as an installable
end-to-end candidate. No version bump/signing/native mutation happens here.
"""
from pathlib import Path
import argparse, hashlib, json, shutil

HERE = Path(__file__).resolve().parent
JAVA = Path('tools/android/packaging/xbmc/src')

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Unexpected source preimage: ' + old[:100])
    return text.replace(old, new, 1)

def apply(root):
    java = root / JAVA
    before = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in root.rglob('*') if p.is_file()}
    # Exact exported source from successful 2103302 CI; refuse unrelated shells.
    expected = json.loads((HERE / 'baseline-source-sha256.json').read_text())
    for path, digest in expected.items():
        if before.get(path) != digest:
            raise ValueError('Not the verified 2103302 source: ' + path)

    p = java / 'InfinityGlassChooser.java.in'; text = p.read_text()
    text = once(text, 'hmCopy=label("hm-copy","BUILT DIFFERENT\\nFOR A HIGHER",9,ink,0,Gravity.CENTER);',
                'hmCopy=label("hm-copy","",9,ink,0,Gravity.CENTER);hmCopy.setVisibility(GONE);')
    text = once(text, '"TWO UNIVERSES. ONE HIGHER STANDARD."', '"TWO UNIVERSES."')
    text = once(text, 'tagline.setTag(cobra?"cobra-tagline":"infinity-tagline");addView(tagline);',
                'tagline.setTag(cobra?"cobra-tagline":"infinity-tagline");tagline.setText("");tagline.setVisibility(GONE);addView(tagline);')
    text = once(text, 'setContentDescription(cobra?"Cobra. Faster. Bolder. Relentless. Open Cobra.":"Infinity. Cleaner. Smarter. Higher. Open Infinity.");',
                'setContentDescription(cobra?"Cobra. Open Cobra.":"Infinity. Open Infinity.");')
    p.write_text(text)

    p = java / 'InfinityStartupTrace.java.in'; text = p.read_text()
    text = once(text, '  private long firstDraw=-1;',
                '  private long firstDraw=-1;\n  private final InfinityStartupTiming timing=new InfinityStartupTiming(began);')
    text = once(text, '    long elapsed=Math.max(0,SystemClock.elapsedRealtime()-began);',
                '    long now=SystemClock.elapsedRealtime();\n    timing.observe(name,now);\n    long elapsed=Math.max(0,now-began);')
    text = once(text, '    if((name.equals("splash.firstFrame")||name.equals("chooser.firstFrame")||name.equals("main.afterSuper"))&&elapsed>=5000)\n      row+=" DELAYED_STARTUP";',
                '    if(name.startsWith("handoff.")||name.startsWith("main."))\n      row+=" handoff_ms="+timing.handoffMillis(now)+" chooser_visible_ms="+timing.chooserMillis(now);\n    if(timing.slow(name,now)) row+=" SLOW_STARTUP_MILESTONE";')
    text = once(text, 'DELAYED_STARTUP marks observed first-frame/Main milestones >=5000ms; not an ANR verdict.',
                'SLOW_STARTUP_MILESTONE marks first frame >=5000ms or Main initialization >=5000ms after an actual Kodi handoff request; not an ANR verdict. Chooser visible duration is separate and may include user/background time. handoff_ms=-1 means no request captured. Historical DELAYED_STARTUP rows used the older, inaccurate chooser-inclusive clock.')
    p.write_text(text)
    shutil.copy2(HERE / 'InfinityStartupTiming.java.in', java / 'InfinityStartupTiming.java.in')
    shutil.copy2(HERE / 'InfinityHealthExport.java.in', java / 'InfinityHealthExport.java.in')
    p = root / 'cmake/scripts/android/Install.cmake'; text=p.read_text()
    text=once(text, '                  src/InfinityStartupTrace.java',
              '                  src/InfinityStartupTrace.java\n                  src/InfinityStartupTiming.java\n                  src/InfinityHealthExport.java')
    p.write_text(text)
    p=java/'Splash.java.in';text=p.read_text()
    text=once(text, '    infinityQueueMainRequest(intent);',
              '    mInfinityStartupTrace.event("handoff.requested");\n    infinityQueueMainRequest(intent);')
    text=once(text, ':"Responsive/Fold trace\\n=====================\\n"+InfinityResponsiveTrace.latestSummary(this)+"\\n";',
              ':"Historical completed Responsive/Fold trace\\n=========================================\\nThis retained trace has its own session/date below. It is not a measurement of this launch.\\n"+InfinityResponsiveTrace.latestSummary(this)+"\\n";')
    from health_export import repair_health_export
    text=repair_health_export(text)
    text=once(text, 'StringBuilder out=new StringBuilder();\n    if(Build.VERSION.SDK_INT<30){',
              'StringBuilder out=new StringBuilder("Exit records are historical. The current APK version does not identify the version that produced each older exit.\\n");\n    if(Build.VERSION.SDK_INT<30){')
    p.write_text(text)
    from android_keyboard import apply as apply_keyboard
    apply_keyboard(root)
    from android_health import apply as apply_health
    apply_health(root)
    from exit_recovery import apply as apply_exit_recovery
    apply_exit_recovery(root)
    after={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in root.rglob('*') if p.is_file()}
    changes=[{'path':p,'before':before.get(p),'after':after.get(p)} for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)]
    return changes

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    changes=apply(a.source)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps({'complete_brief':False,'apk_produced':False,'changes':changes},indent=2)+'\n')
    print('Applied first Android tranche:',len(changes),'files; remaining brief is not implemented.')
