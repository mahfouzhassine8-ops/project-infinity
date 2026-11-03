"""Actual public-input Preview chrome/call observations on a disposable emulator.

Reuse the previously corrected immediate observer, grants, notice handling and
resize-snapshot input guard. No private Activity invocation or production hooks.
"""
import argparse,base64,importlib.util,json,re,time,traceback
from pathlib import Path
from immersive_prompt import locate as tutorial_target
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
        tree=q.nodes();nodes=[n for n in tree.iter('node') if n.attrib.get('class')=='android.view.SurfaceView' and n.attrib.get('package')==q.P and n.attrib.get('enabled')=='true']
        q.check(len(nodes)==1,'One actual clickable video surface required');b=list(map(int,re.findall(r'-?\d+',nodes[0].attrib['bounds'])));viewport=list(map(int,re.findall(r'-?\d+',tree.find('node').attrib['bounds'])))
        b=[max(b[0],viewport[0]),max(b[1],viewport[1]),min(b[2],viewport[2]),min(b[3],viewport[3])];q.check(b[2]>b[0] and b[3]>b[1],'Visible cropped video intersection required')
        if b==previous:q.shell('input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));q.record('real_video_surface_tap',bounds=b);return
        previous=b;time.sleep(.1)
    raise AssertionError('Stable visible video touch bounds unavailable')
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
def panel_mode(name):
    control('Display');q.await_text('Best Fit');q.tap(name);q.tap('Done');q.await_text('Seek video')
def panel_theme(name):
    control('Display');q.await_text('Best Fit');q.tap('Appearance');q.await_text('Preview appearance');q.tap(name);q.await_text('Best Fit');q.tap('Done');q.await_text('Seek video')
def bars_snapshot(name):
    data=q.shell('dumpsys','window','windows');(q.out/(name+'-window.txt')).write_text(data)
    im=q.screenshot(name);q.record('actual_window_bar_observation',name=name);return im
def hidden_video_progress():
    def sample():
        dump=q.shell('dumpsys','media.player');clients=[c for c in re.split(r'(?m)^ Client\n',dump) if 'packageName: '+q.P+',' in c and 'mime(video/' in c];q.check(len(clients)==1,'One actual owned video decoder required');c=clients[0]
        q.check('renderer(paused(0)' in c and 'state(5)' in c,'Actual decoder must remain playing in fullscreen')
        connection=re.search(r'connId\((\d+)\)',c);frames=re.search(r'mime\(video/[^)]+\).*?numFramesTotal\((\d+)\)',c,re.S);q.check(connection and frames,'Actual decoder counters unavailable');return connection[1],int(frames[1]),dump
    conn,before,dump=sample();deadline=q.feature_time()+4
    while q.feature_time()<deadline:
        current,after,dump=sample();q.check(current==conn,'Fullscreen must not replace the decoder')
        if after>before:
            (q.out/('fullscreen-player-'+str(len(q.steps))+'.txt')).write_text(dump);q.record('actual_hidden_video_progress',connection=conn,before=before,after=after);return
        time.sleep(.2)
    raise AssertionError('Real fullscreen decoder frames did not advance')
def immersive_education():
    dump=q.shell('dumpsys','window','windows')
    rows=[r for r in re.split(r'(?m)^  Window #\d+ ',dump) if 'ImmersiveModeConfirmation}' in r.split('\n')[0] and 'isVisible=true' in r]
    if not rows:return False
    (q.out/'platform-immersive-education-window.txt').write_text(dump);q.screenshot('platform-immersive-education')
    deadline=q.feature_time()+8;previous=None
    while q.feature_time()<deadline:
        q.sequence+=1;q.observer.stdin.write(('SYSTEM '+str(q.sequence)+'\n').encode());q.observer.stdin.flush()
        raw=base64.b64decode(q.observer_line('EXTERNAL_'+str(q.sequence)+' '),validate=True);tree=q.ET.fromstring(raw)
        (q.out/'platform-immersive-education.xml').write_bytes(raw)
        node=next((q.find(tree,label) for label in ('Got it','GOT IT') if q.find(tree,label) is not None),None)
        target=(tree.attrib.get('window-id'),q.bounds(node)) if node is not None and node.attrib.get('package')=='com.android.systemui' else None
        observation='OS_accessibility'
        if target is None:
            # This API37 SystemUI tutorial is visible but absent from getWindows.
            # Measure its actual blue Got it button and recognize its text, only
            # inside the current trusted OS window's reported touchable region.
            current=q.shell('dumpsys','window','windows')
            visible=[r for r in re.split(r'(?m)^  Window #\d+ ',current) if 'ImmersiveModeConfirmation}' in r.split('\n')[0] and 'isVisible=true' in r]
            q.check(len(visible)==1,'Only the currently visible OS immersive tutorial may be acknowledged')
            region=re.search(r'touchable region=SkRegion\(\((-?\d+),(-?\d+),(-?\d+),(-?\d+)\)\)',visible[0]);q.check(region,'Actual OS tutorial touchable bounds required')
            region=list(map(int,region.groups()));im=q.screenshot('platform-immersive-target-'+str(q.sequence))
            try:target=('ImmersiveModeConfirmation',tutorial_target(im,region),region)
            except AssertionError:
                # The OS tutorial itself slides in; its reported touch region
                # can still be negative or not yet contain the visible button.
                # Observe a real stable target within the existing eight seconds.
                previous=None;time.sleep(.1);continue
            observation='current_screenshot_OCR_and_OS_window'
        if target is not None and target==previous:
            b=target[1];q.shell('input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));q.record('platform_immersive_education_acknowledged',window=target[0],bounds=b,observation=observation)
            break
        previous=target;time.sleep(.1)
    else:raise AssertionError('Observed OS immersive tutorial has no stable accessibility target')
    while q.feature_time()<deadline:
        dump=q.shell('dumpsys','window','windows')
        if not any('ImmersiveModeConfirmation}' in r.split('\n')[0] and 'isVisible=true' in r for r in re.split(r'(?m)^  Window #\d+ ',dump)):return True
        time.sleep(.1)
    raise AssertionError('Acknowledged OS immersive tutorial did not close')
def unobscured_bars_snapshot():
    # The tutorial may arrive between the pre-capture OS dump and screenshot.
    # Check after capture, acknowledge only the exact observed OS overlay, and
    # recapture once. Never retry or relax a genuine video/pixel assertion.
    for attempt in range(2):
        im=bars_snapshot('immersive-'+str(len(q.steps)))
        if not immersive_education():return im
    raise AssertionError('Unexpected repeated OS immersive tutorials')
def enter_fullscreen():
    control('Fullscreen');started=q.feature_time();deadline=started+3.5;stable=0
    # Public input returns before Android publishes the new accessibility frame.
    # Observe two complete hidden-chrome frames within the original short input
    # deadline; never accept the partially updated tree immediately after tap.
    while q.feature_time()<deadline:
        tree=q.nodes();surface=[n for n in tree.iter('node') if n.attrib.get('class')=='android.view.SurfaceView' and n.attrib.get('package')==q.P]
        hidden=q.find(tree,'Close') is None and q.find(tree,'Seek video') is None and len(surface)==1
        stable=stable+1 if hidden else 0
        if stable>=2:break
        time.sleep(.1)
    else:raise AssertionError('Fullscreen header/toolbar did not become hidden within existing input deadline')
    elapsed=q.feature_time()-started;q.check(elapsed<3.5,'Fullscreen observation exceeded existing input deadline')
    q.record('actual_fullscreen_chrome_hidden',seconds=elapsed,consecutive_frames=stable)
    hidden_video_progress();im=unobscured_bars_snapshot()
    title=[c['title'] for c in q.steps if c['check']=='actual_video_decoded'][-1];color={'a.mp4':'red','b.mp4':'green','c.mp4':'blue'}[title];w,h=im.size;matches=0
    for x in (.03,.1,.9,.97):
        for y in (.03,.1,.9,.97):
            r,g,b=im.getpixel((int(w*x),int(h*y)))
            if (color=='red' and r>70 and r>g*2 and r>b*2) or (color=='green' and g>50 and g>r*2 and g>b*2) or (color=='blue' and b>70 and b>r*2 and b>g*2):matches+=1
    q.check(matches>=12,'Fullscreen must cover viewport edges with proportion-preserving crop');q.record('actual_fullscreen_edge_pixels',matches=matches,total=16,color=color)
def exit_fullscreen():
    visible_surface_tap();q.await_text('Seek video');control('Exit fullscreen');q.await_text('Close');advancing();bars_snapshot('restored-'+str(len(q.steps)));q.record('fullscreen_reversible_without_restart')
def magenta_ratio(name):
    from PIL import ImageChops
    im=q.screenshot(name);r,g,b=im.split()[:3];mask=ImageChops.multiply(ImageChops.multiply(r.point(lambda x:255 if x>150 else 0),b.point(lambda x:255 if x>150 else 0)),g.point(lambda x:255 if x<90 else 0));bounds=mask.getbbox();q.check(bounds is not None,'Decoded scaling patch must be visible');ratio=(bounds[2]-bounds[0])/(bounds[3]-bounds[1]);q.record('actual_decoded_patch_ratio',name=name,bounds=bounds,ratio=ratio);return ratio
def body(a):
    a.segment='remaining';resume.setup(a)
    q.open_video('Open A','red','a.mp4');advancing()
    for theme in ('Light','Dark'):
        panel_theme(theme);control('Display');q.await_text('Show the entire video with no cropping.');q.screenshot('display-'+theme.lower());q.tap('Done');enter_fullscreen();exit_fullscreen()
    # Back first leaves immersive mode; the source is reached only on normal Back.
    enter_fullscreen();q.shell('input','keyevent','4');q.await_text('Close');advancing();q.record('fullscreen_back_exits_only_mode');resume.seek(.2);advancing();first_a_position=resume.pause();q.source_return()
    q.open_video('Open B','green','b.mp4');advancing()
    for viewport,density in [('1080x2520','420'),('1600x1680','320'),('2520x1080','420'),('1680x1600','320')]:
        q.shell('wm','size',viewport);q.shell('wm','density',density);q.await_text('b.mp4');panel_mode('Best Fit');q.strip_to('Pause');screenshot_geometry(viewport+'-fit',False);advancing()
        tree=q.nodes();surface=[n for n in tree.iter('node') if n.attrib.get('class')=='android.view.SurfaceView' and n.attrib.get('package')==q.P][0];rect=q.bounds(surface);q.check(abs((rect[2]-rect[0])/(rect[3]-rect[1])-360/640)<.02,'Portrait video must remain proportioned in landscape/inner');enter_fullscreen();visible_surface_tap();q.await_text('Seek video');control('Display');q.await_text('Best Fit');q.screenshot(viewport+'-fullscreen-display');q.tap('Done');control('Exit fullscreen');advancing();q.record('actual_viewport_fullscreen_fit',viewport=viewport)
    q.shell('wm','size','2520x1080');q.shell('wm','density','420');q.await_text('b.mp4')
    for name in ('Best Fit','Fill (crop)','Stretch'):
        panel_mode(name);advancing();ratio=magenta_ratio('actual-scale-'+name.replace(' ','-'))
        q.check(.65<ratio<1.5 if name!='Stretch' else ratio>3,'Best Fit/Fill must preserve source geometry; Stretch alone distorts')
        enter_fullscreen();visible_surface_tap();q.await_text('Seek video');control('Display');q.await_text('Fill (crop) selection');q.check(q.find(q.nodes(),'Fill (crop) selection').attrib.get('checked')=='true','Fullscreen must temporarily select Fill');q.screenshot('retained-'+name.replace(' ','-'));q.tap('Done');control('Exit fullscreen');advancing();control('Display');q.await_text(name+' selection');q.check(q.find(q.nodes(),name+' selection').attrib.get('checked')=='true','Exit must restore previous Display mode');q.tap('Done');q.record('actual_display_mode_restored',mode=name)
    panel_mode('Best Fit');q.record('actual_bestfit_fill_stretch_decoding');q.source_return()
    q.shell('wm','size','1600x1680');q.shell('wm','density','320');q.open_video('Open C','blue','c.mp4');advancing();enter_fullscreen();exit_fullscreen();q.source_return()
    q.shell('wm','size','1080x2520');q.shell('wm','density','420');resume.offer('Open A',first_a_position);advancing();saved=resume.pause();q.source_return();resume.offer('Open A',saved,'Start Over');advancing();q.source_return();q.record('existing_resume_retained')
    q.final_cleanup();logs=q.shell('logcat','-d','-v','threadtime');(q.out/'logcat.txt').write_text(logs);q.check('FATAL EXCEPTION' not in logs,'Android crash');q.record('selected_fullscreen_display_functional_complete')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True);q.out=a.out;status='FAIL'
    try:body(a);status='PASS'
    except Exception:
        (a.out/'FAILURE.txt').write_text(traceback.format_exc())
        try:q.screenshot('failure');(q.out/'failure-window.txt').write_text(q.shell('dumpsys','window','windows'))
        except Exception:pass
        raise
    finally:
        resume.stop_observer();(a.out/'RESULT.json').write_text(json.dumps(dict(status=status,checks=q.steps,source_build=json.loads((a.prepared/'BUILD.json').read_text()),physical_Fold='NOT_TESTED',approved_visual_reference='NOT_ACCESSIBLE_MATCH_PENDING',shutdown='NOT_RUN'),indent=2)+'\n')
