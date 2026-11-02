"""Actual public-input Preview chrome/call observations on a disposable emulator.

Reuse the previously corrected immediate observer, grants, notice handling and
resize-snapshot input guard. No private Activity invocation or production hooks.
"""
import argparse,importlib.util,json,re,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parents[1];R=H.parents[1]
spec=importlib.util.spec_from_file_location('resume_fixture',R/'repairs/infinity-preview-2103447-resume/android-qa/run.py')
resume=importlib.util.module_from_spec(spec);spec.loader.exec_module(resume);q=resume.q
def clock():
    for n in q.nodes().iter('node'):
        m=re.fullmatch(r'Elapsed time (\d+:\d\d(?::\d\d)?)',n.attrib.get('content-desc',''))
        if m:return resume.seconds(m[1])
    raise AssertionError('Actual cinematic elapsed-time node unavailable')
resume.clock=clock
def control(label):q.strip_to(label);q.tap(label)
def skip(delta):
    before=clock();control('−10 s' if delta<0 else '+10 s');deadline=q.feature_time()+18
    while q.feature_time()<deadline:
        actual=clock()
        if abs(actual-(before+delta))<=2:
            q.record('real_skip_completed',delta=delta,before=before,after=actual);return
        time.sleep(.2)
    raise AssertionError('Seek completion did not reach the ten-second target')
def visible_surface_tap():
    previous=None;deadline=q.feature_time()+3.5
    while q.feature_time()<deadline:
        nodes=[n for n in q.nodes().iter('node') if n.attrib.get('class')=='android.view.SurfaceView' and n.attrib.get('package')==q.P and n.attrib.get('enabled')=='true']
        q.check(len(nodes)==1,'One actual clickable video surface required');b=q.bounds(nodes[0])
        if b==previous:
            q.shell('input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));q.record('real_video_surface_tap',bounds=b);return
        previous=b;time.sleep(.1)
    raise AssertionError('Stable video touch bounds unavailable')
def appearance(choice):
    control('Display');q.await_text('Best Fit');q.tap('APPEARANCE');q.await_text('Preview appearance');q.tap(choice);q.await_text('Seek video')
def screenshot_geometry(name,light):
    tree=q.nodes();q.check(q.find(tree,'Close') is not None,'Close remains visible')
    q.check(q.find(tree,'Seek video') is not None,'Timeline remains independently accessible')
    surfaces=[n for n in tree.iter('node') if n.attrib.get('class')=='android.view.SurfaceView' and n.attrib.get('package')==q.P]
    q.check(len(surfaces)==1,'One video surface, no duplicate player');video=q.bounds(surfaces[0]);seek=q.bounds(q.find(tree,'Seek video'));close=q.bounds(q.find(tree,'Close'))
    q.check(close[3]<=video[1] and video[3]<=seek[1],'Header, video and timeline overlap')
    im=q.screenshot(name);w,h=im.size
    # Background margin, outside video/controls/status bars; selected theme must
    # actually render. Static screenshots alone are not decoder evidence.
    r,g,b=im.getpixel((max(3,w//100),h//2))
    q.check((min(r,g,b)>180) if light else (max(r,g,b)<90),'Rendered palette differs from selected appearance')
    (q.out/(name+'.xml')).write_bytes(q.ET.tostring(tree))
    q.record('actual_theme_geometry',name=name,light=light,viewport=[w,h],video=video,seek=seek,close=close,background_rgb=[r,g,b])
def advancing():
    before=clock();deadline=q.feature_time()+4
    while q.feature_time()<deadline:
        after=clock()
        if after>=before+1:q.record('actual_media_clock_advances',before=before,after=after);return
        time.sleep(.2)
    raise AssertionError('Real decoder did not advance')
def synthetic_call(a,saved):
    # Emulator modem only. No number is dialed on a real device or network.
    q.check(q.shell('getprop','ro.kernel.qemu').strip()=='1','Emulator call observation only')
    number='5550109';started=False
    try:
        answer=q.adb('emu','gsm','call',number).decode();q.check('OK' in answer,'Emulated incoming call rejected');started=True
        answer=q.adb('emu','gsm','accept',number).decode();q.check('OK' in answer,'Emulated call acceptance rejected')
        deadline=q.feature_time()+12;mode=''
        while q.feature_time()<deadline:
            dump=q.shell('dumpsys','audio');(q.out/'call-audio-policy.txt').write_text(dump)
            # Require observed platform mode, not just modem's fictional call.
            m=re.search(r'^\s*(?:-\s*)?(?:mMode|Actual mode)\s*(?:=|:)\s*(MODE_IN_CALL|MODE_IN_COMMUNICATION|2|3)\b',dump,re.M)
            if m:mode=m[0];break
            time.sleep(.3)
        if not mode:
            q.record('synthetic_call_platform_limit',reason='Emulator modem call did not publish active call/communication AudioManager mode; no runtime call PASS claimed',modem=q.adb('emu','gsm','list').decode());return
        resume.source();resume.offer('Open C',saved);q.strip_to('Pause');q.strip_to('Unmute');q.await_text('Unmute');advancing()
        q.screenshot('call-default-muted');q.record('call_default_muted_video',mode=mode,observation='Unmute UI and real decoding; no acoustic audio assertion')
        q.tap('Unmute');q.await_text('Mute');advancing();q.screenshot('call-manual-unmute');q.record('call_manual_unmute_video',platform_audio='Android may enforce media muting')
        q.adb('emu','gsm','cancel',number);started=False;advancing();q.source_return();q.record('call_end_keeps_video')
    finally:
        if started:q.adb('emu','gsm','cancel',number)
        resume.source()
def body(a):
    a.segment='remaining';resume.setup(a)
    q.open_video('Open A','red','a.mp4');advancing();p=resume.pause();time.sleep(1.1);q.check(clock()==p,'User pause did not hold position');control('Play');advancing()
    resume.pause();resume.seek(.2);skip(-10);skip(10);control('Play');advancing()
    control('Mute');q.await_text('Unmute');q.tap('Unmute');q.await_text('Mute');q.record('real_mute_toggle')
    control('Audio');track=q.await_prefix('Audio 2');q.screenshot('audio-menu');q.tap(track);q.record('existing_audio_choice',track=track)
    control('Subtitles');track=q.await_prefix('Subtitle 1');q.tap(track);q.await_text('External subtitle fixture');q.screenshot('subtitle-rendered');q.record('subtitle_actually_rendered')
    control('Display');q.await_text('Fill (crop)');q.tap('Fill (crop)');control('Display');q.tap('Best Fit');q.record('display_modes_preserved')
    control('Auto rotate');q.await_text('Rotation locked');q.tap('Rotation locked');q.await_text('Auto rotate');q.record('rotation_preserved')
    control('Volume');q.await_text('Player volume');q.tap('DONE');q.record('original_volume_dialog_preserved')
    q.strip_to('Pause');visible_surface_tap();q.check(q.find(q.nodes(),'Close') is None,'Video tap did not hide chrome');visible_surface_tap();q.await_text('Close');q.await_text('Pause');q.record('actual_video_tap_hide_and_show')
    saved=resume.pause();q.source_return('Close');resume.offer('Open A',saved);saved=resume.pause();q.source_return();resume.offer('Open A',saved,'Start Over');q.source_return('Stop');q.record('new_chrome_resume_and_start_over_preserved')
    q.open_video('Open B','green','b.mp4')
    for viewport,density in [('1080x2520','420'),('1600x1680','320'),('2520x1080','420'),('1080x960','420')]:
        q.shell('wm','size',viewport);q.shell('wm','density',density);q.await_text('b.mp4')
        for theme in ('Dark','Light'):
            appearance(theme);q.strip_to('Pause');screenshot_geometry(viewport+'-'+theme.lower(),theme=='Light');advancing()
            # Every visible size retains the far-end controls by actual swipes.
            control('Volume');q.await_text('Player volume');q.tap('DONE');q.strip_to('Pause')
        q.record('viewport_controls_and_decoding',viewport=viewport)
    appearance('System')
    for night in ('yes','no'):
        q.shell('cmd','uimode','night',night);q.await_text('b.mp4');q.strip_to('Pause');screenshot_geometry('system-night-'+night,night=='no')
    q.source_return();q.shell('wm','size','1080x2520');q.shell('wm','density','420');resume.source()
    # Preserve rapid request replacement and retained resume store. The store's
    # persistence/reboot/identity evidence from 448 is reused, not rerun.
    q.open_video('Rapid A B C','blue','c.mp4');resume.seek(.03);call_saved=resume.pause();q.source_return();q.record('rapid_replacement_still_latest_request')
    q.tap('Open BAD');q.await_text('Retry');q.check('Loading' not in q.text(q.nodes()),'Error left stale loading');q.screenshot('error-ui');q.source_return();q.record('error_and_retry_preserved')
    synthetic_call(a,call_saved)
    q.final_cleanup();logs=q.shell('logcat','-d','-v','threadtime');(q.out/'logcat.txt').write_text(logs);q.check('FATAL EXCEPTION' not in logs,'Android crash in selected journey');q.record('selected_chrome_journey_complete')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True);q.out=a.out;status='FAIL'
    try:body(a);status='PASS'
    except Exception:
        (a.out/'FAILURE.txt').write_text(traceback.format_exc())
        try:q.screenshot('failure');(a.out/'failure-logcat.txt').write_text(q.shell('logcat','-d','-v','threadtime'))
        except Exception:pass
        raise
    finally:
        resume.stop_observer();(a.out/'RESULT.json').write_text(json.dumps(dict(status=status,checks=q.steps,source_build=json.loads((a.prepared/'BUILD.json').read_text()),physical_Fold='NOT_TESTED',call_audio='Host policy plus separately reported emulator observation; physical carrier/VoIP audio pending',shutdown='NOT_RUN'),indent=2)+'\n')
