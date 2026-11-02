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
        resume.source()
        if saved is None:q.open_video('Open C','blue','c.mp4')
        else:resume.offer('Open C',saved)
        q.strip_to('Pause');q.strip_to('Unmute');q.await_text('Unmute');advancing()
        (q.out/'call-default-media.player.txt').write_text(q.shell('dumpsys','media.player'))
        q.screenshot('call-default-muted');q.record('call_default_muted_video',mode=mode,observation='Unmute UI and real decoding; no acoustic audio assertion')
        q.tap('Unmute');q.await_text('Mute');advancing();q.screenshot('call-manual-unmute');q.record('call_manual_unmute_video',platform_audio='Android may enforce media muting')
        (q.out/'call-unmuted-media.player.txt').write_text(q.shell('dumpsys','media.player'))
        q.adb('emu','gsm','cancel',number);started=False;advancing();q.source_return();q.record('call_end_keeps_video')
    finally:
        if started:q.adb('emu','gsm','cancel',number)
        resume.source()
def body(a):
    a.segment='remaining';resume.setup(a)
    q.open_video('Open A','red','a.mp4');advancing();skip(10);skip(-10)
    q.record('seek_actions_preserved')
    control('Auto rotate');q.await_text('Rotation locked');q.check(q.find(q.nodes(),'Rotation locked').attrib.get('selected')=='false','Auto highlight must clear while locked')
    q.tap('Rotation locked');q.await_text('Auto rotate');q.check(q.find(q.nodes(),'Auto rotate').attrib.get('selected')=='true','Auto highlight must persist after release')
    q.record('real_rotation_selected_state');q.screenshot('rotation-active')
    q.check(q.find(q.nodes(),'Volume') is None,'Duplicate Volume button remains')
    q.record('duplicate_volume_removed')
    for viewport,density in [('1080x2520','420'),('1600x1680','320'),('2520x1080','420'),('1080x960','420')]:
        q.shell('wm','size',viewport);q.shell('wm','density',density);q.await_text('a.mp4')
        for theme in ('Dark','Light'):
            appearance(theme);q.strip_to('Pause');screenshot_geometry(viewport+'-'+theme.lower(),theme=='Light');advancing()
            tree=q.nodes();surface=[n for n in tree.iter('node') if n.attrib.get('class')=='android.view.SurfaceView' and n.attrib.get('package')==q.P][0]
            video=q.bounds(surface);seek=q.bounds(q.find(tree,'Seek video'));q.check(seek[1]-video[3]<160,'Timeline must stay adjacent to actual video')
        q.record('responsive_landscape_media',viewport=viewport)
    q.shell('wm','size','1080x2520');q.shell('wm','density','420');q.await_text('a.mp4');q.strip_to('Pause')
    tree=q.nodes();v=q.bounds([n for n in tree.iter('node') if n.attrib.get('class')=='android.view.SurfaceView' and n.attrib.get('package')==q.P][0]);visible_surface_tap()
    q.check(q.find(q.nodes(),'Close') is None,'Chrome did not hide');q.screenshot('video-unobstructed')
    hidden=q.bounds([n for n in q.nodes().iter('node') if n.attrib.get('class')=='android.view.SurfaceView' and n.attrib.get('package')==q.P][0]);q.check(hidden[2]-hidden[0]>=v[2]-v[0] and hidden[3]-hidden[1]>=v[3]-v[1],'Hidden chrome must free viewport')
    visible_surface_tap();q.await_text('Pause');q.record('hidden_chrome_releases_viewport')
    q.strip_to('Player volume');tree=q.nodes();b=q.bounds(q.find(tree,'Player volume'));x=b[0]+(b[2]-b[0])*0.4;y=(b[1]+b[3])//2;q.shell('input','tap',str(int(x)),str(y));q.screenshot('inline-volume')
    dump=q.shell('dumpsys','media.player');(q.out/'inline-volume-media.player.txt').write_text(dump)
    values=re.findall(r'left - right volume\((\d+\.\d+), (\d+\.\d+)\)',dump);q.check(any(0<float(x)<.8 and x==y for x,y in values),'Inline slider must change actual player volume');q.record('real_inline_volume')
    q.source_return()
    for label,name,ratio in [('Open B','b',360/640),('Open C','c',1)]:
        q.open_video(label,'green' if name=='b' else 'blue',name+'.mp4');advancing();q.strip_to('Pause');tree=q.nodes();b=q.bounds([n for n in tree.iter('node') if n.attrib.get('class')=='android.view.SurfaceView' and n.attrib.get('package')==q.P][0]);q.check(abs((b[2]-b[0])/(b[3]-b[1])-ratio)<.02,'Actual media ratio must drive frame');q.screenshot(name+'-actual-aspect');q.record('actual_media_aspect',name=name,ratio=ratio,bounds=b);q.source_return()
    q.final_cleanup();logs=q.shell('logcat','-d','-v','threadtime');(q.out/'logcat.txt').write_text(logs);q.check('FATAL EXCEPTION' not in logs,'Android crash');q.record('selected_layout_controls_complete')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True);q.out=a.out;status='FAIL'
    try:body(a);status='PASS'
    except Exception:
        (a.out/'FAILURE.txt').write_text(traceback.format_exc())
        try:q.screenshot('failure');(a.out/'failure-logcat.txt').write_text(q.shell('logcat','-d','-v','threadtime'))
        except Exception:pass
        raise
    finally:
        resume.stop_observer();(a.out/'RESULT.json').write_text(json.dumps(dict(status=status,checks=q.steps,source_build=json.loads((a.prepared/'BUILD.json').read_text()),physical_Fold='NOT_TESTED',shutdown='NOT_RUN'),indent=2)+'\n')
