"""Project only missing responsive features for an isolated upstream renderer.

No APK, production native build, phone, original profile or shutdown invocation.
The projection is disclosed: this cannot establish Android/Fold acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as E
import prepare
from test_browser import expand

HERE=Path(__file__).resolve().parent
QA=Path('/tmp/infinity-browser-render-20261105')
OLD=Path('/tmp/kodi-ui-runtime-qa/root/usr/share/kodi')
ENGINE=Path('/tmp/kodi-ui-runtime-qa/root')
SOURCE=prepare.ROOT/prepare.MEMBER
BASE_SKIN=Path('/tmp/kodi453-ui-baseline/assets/addons/skin.infinity.diggz')


def replace(path, data):
    # Never write through a hard link into an existing fixture or source.
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.browser-tmp')
    temp.write_bytes(data)
    temp.replace(path)


def native_geometry(node, parent_w, parent_h, records):
    """Fixture projection of frozen responsive axes; never production code."""
    def value(text, extent):
        if text.endswith('%'):return float(text[:-1])*extent/100
        if text.endswith('r'):return extent-float(text[:-1])
        return float(text)
    bounds=[]
    for start,end,center,size,extent in [('left','right','centerleft','width',parent_w),
                                          ('top','bottom','centertop','height',parent_h)]:
        s=node.findtext(start);e=node.findtext(end);c=node.findtext(center);dimension=node.find(size)
        if dimension is not None:
            text=dimension.text
            length=value(dimension.get('max','0'),extent) if text=='auto' else value(text,extent)
            if text!='auto' and dimension.get('max'):length=min(length,value(dimension.get('max'),extent))
        else:length=extent-value(s or '0',extent)-value(e or '0',extent)
        position=value(s,extent) if s is not None else (value(c,extent)-length/2 if c is not None else
                    extent-value(e,extent)-length if e is not None else 0)
        for tag in (start,end,center,size):
            for child in list(node.findall(tag)):node.remove(child)
        E.SubElement(node,start).text=str(position)
        new=E.SubElement(node,size)
        if dimension is not None and dimension.text=='auto':
            new.text='auto';new.set('min',str(value(dimension.get('min','1'),extent)));new.set('max',str(length))
        else:new.text=str(max(1,length))
        bounds.append(max(1,length))
    w,h=bounds
    records.append({'type':node.get('type'),'id':node.get('id'),'width':w,'height':h})
    for child in node.findall('control'):native_geometry(child,w,h,records)
    for layout in list(node.findall('itemlayout'))+list(node.findall('focusedlayout')):
        width=layout.get('width','0');height=layout.get('height','0')
        rh=value(height,h) or h
        if width=='auto':
            ratio=float(layout.get('aspectratio','0'));rw=min(w,rh*ratio) if ratio>0 else w
            if ratio>0:rh=rw/ratio
        else:rw=value(width,w) or w
        layout.set('width',str(rw));layout.set('height',str(rh))
        for child in layout.findall('control'):native_geometry(child,rw,rh,records)


def setup(width,height,actions,attempt,slim=False):
    share=QA/'share'
    if not share.exists():
        shutil.copytree(OLD,share,copy_function=os.link,
            ignore=shutil.ignore_patterns('portable_data','skin.infinity.diggz','script.infinityuiqa',
                                         'plugin.video.infinityuiqa.a','plugin.video.infinityuiqa.b'))
        shutil.copytree(BASE_SKIN,share/'addons/skin.infinity.diggz',copy_function=os.link)
        # This is only the earlier disposable synthetic profile, never phone data.
        shutil.copytree(OLD/'portable_data',share/'portable_data',copy_function=shutil.copy2)
        for name in ('poster.png','fanart.png'):
            shutil.copy2(Path('/tmp/kodi-ui-runtime-qa')/name,QA/name)
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=20',
                        '-t','6','-an','-c:v','mpeg4','-y',str(QA/'silent-test.mp4')],check=True)
    skin=share/'addons/skin.infinity.diggz'
    overlay=prepare.ROOT/'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz'
    for src in overlay.rglob('*'):
        if src.is_file():
            replace(skin/src.relative_to(overlay),src.read_bytes())
    # Frozen native Skin.cpp uses a1080 short axis and an8-unit long-axis quantum.
    ratio=width/height
    logical_w=1080 if ratio<1 else ((round(1080*ratio)+4)//8)*8
    logical_h=((round(1080/ratio)+4)//8)*8 if ratio<1 else 1080
    addon=E.parse(skin/'addon.xml').getroot()
    res=addon.find("extension[@point='xbmc.gui.skin']/res")
    res.set('width',str(logical_w));res.set('height',str(logical_h));res.set('aspect','%d:%d'%(logical_w,logical_h))
    replace(skin/'addon.xml',E.tostring(addon,encoding='utf-8',xml_declaration=True))
    doc=E.parse(SOURCE).getroot()
    projected=[]
    for name in ('InfinityMedia_VideoList','InfinityMedia_SlimVideoList'):
        original=doc.find("include[@name='%s']"%name)
        expanded=expand(doc,original)
        native_geometry(expanded.find('control'),logical_w,logical_h,projected)
        index=list(doc).index(original);doc.remove(original);doc.insert(index,expanded)
    guide=doc.find("include[@name='InfinityMedia_TouchGuide']/definition/control")
    native_geometry(guide,logical_w,logical_h,projected)
    replace(skin/'unified/Includes_InfinityMediaLists.xml',E.tostring(doc,encoding='utf-8',xml_declaration=True))
    for aid,point,script,provides in [('script.infinitybrowserqa','xbmc.service','runtime_probe.py',''),
                                    ('plugin.video.infinitybrowserqa','xbmc.python.pluginsource','fixture_directory.py','<provides>video</provides>')]:
        dest=share/'addons'/aid
        xml=('<addon id="%s" name="Finite browser QA" version="1.0.0" provider-name="Local QA">'
             '<requires><import addon="xbmc.python" version="3.0.0"/></requires>'
             '<extension point="%s" library="entry.py">%s</extension></addon>')%(aid,point,provides)
        replace(dest/'addon.xml',xml.encode())
        # Resolve QA configuration outside the share tree without changing runtime globals.
        content=(HERE/script).read_text().replace("Path(__file__).resolve().parents[1]",repr(str(QA)))
        content=content.replace('base = '+repr(str(QA)), 'base = Path('+repr(str(QA))+')')
        content=content.replace('BASE = '+repr(str(QA)), 'BASE = Path('+repr(str(QA))+')')
        replace(dest/'entry.py',content.encode())
    presentation=prepare.ROOT/'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/script.infinity.commandcenter/media_view.py'
    replace(share/'addons/script.infinitybrowserqa/candidate_media_view.py',presentation.read_bytes())
    # The earlier QA root lists its synthetic add-ons as mandatory built-ins.
    # Replace those fixture identities, not any production manifest or guard.
    manifest=E.parse(share/'system/addon-manifest.xml').getroot()
    for node in list(manifest):
        if node.text in ('script.infinityuiqa','plugin.video.infinityuiqa.a','plugin.video.infinityuiqa.b'):
            manifest.remove(node)
    present={n.text for n in manifest}
    for aid in ('script.infinitybrowserqa','plugin.video.infinitybrowserqa'):
        if aid not in present:E.SubElement(manifest,'addon').text=aid
    replace(share/'system/addon-manifest.xml',E.tostring(manifest,encoding='utf-8',xml_declaration=True))
    case='%dx%d%s'%(width,height,('-'+attempt) if attempt else '')
    out=HERE/'results/linux'/case
    out.mkdir(parents=True,exist_ok=True)
    assert not (out/'RESULT.json').exists(),'Preserve previous run evidence'
    config={'viewport':[width,height],'logical':[logical_w,logical_h],'output':str(out),
            'actions':actions,'slim':slim,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'presentation_sha256':hashlib.sha256(presentation.read_bytes()).hexdigest()}
    (QA/'config.json').write_text(json.dumps(config))
    (out/'PROJECTION.json').write_text(json.dumps({'source_sha256':config['source_sha256'],
        'fixture_only':['skin addon.xml resolution','native recursive coordinates/itemlayout sizes projected in existing two List includes and touch guide','synthetic QA add-on identities in copied Linux manifest'],
        'logical':[logical_w,logical_h],'viewport':[width,height],
        'layouts':projected,'Android':'NOT_RUN','native_engine_executed':False},indent=2)+'\n')
    return share,out


def main():
    p=argparse.ArgumentParser();p.add_argument('--width',type=int,required=True);p.add_argument('--height',type=int,required=True)
    p.add_argument('--actions',action='store_true');p.add_argument('--attempt',default='')
    p.add_argument('--slim',action='store_true');a=p.parse_args()
    share,out=setup(a.width,a.height,a.actions,a.attempt,a.slim)
    env=os.environ.copy()
    env.update(DISPLAY=':94',LD_LIBRARY_PATH=str(ENGINE/'usr/lib/x86_64-linux-gnu')+':'+str(ENGINE/'usr/lib/x86_64-linux-gnu/samba'),
        KODI_HOME=str(share),KODI_BIN_HOME=str(ENGINE/'usr/lib/x86_64-linux-gnu/kodi'),
        LIBGL_ALWAYS_SOFTWARE='1',PYTHONDONTWRITEBYTECODE='1')
    x=subprocess.Popen([str(ENGINE/'usr/bin/Xvfb'),':94','-screen','0','%dx%dx24'%(a.width,a.height),'-nolisten','tcp'],env=env,
                       stdout=(out/'xvfb.log').open('w'),stderr=subprocess.STDOUT)
    time.sleep(.4)
    process=subprocess.Popen([str(ENGINE/'usr/lib/x86_64-linux-gnu/kodi/kodi.bin'),'--portable','--windowing=x11','--audio-backend=alsa','--debug'],
        env=env,stdout=(out/'console.log').open('w'),stderr=subprocess.STDOUT)
    (out/'PROCESS-START.json').write_text(json.dumps({'kodi_pid':process.pid,'xvfb_pid':x.pid,'disposable_profile':str(share/'portable_data')}))
    try:
        until=time.monotonic()+140
        while time.monotonic()<until and process.poll() is None:
            if (out/'RESULT.json').exists():
                print((out/'RESULT.json').read_text())
                return 0 if json.loads((out/'RESULT.json').read_text())['status'].startswith('PASS') else 1
            time.sleep(.5)
        print('Fixture observation unavailable; no Android or visual PASS claimed.')
        return 2
    finally:
        # Dispose only the two finite Linux QA processes created by this script.
        if process.poll() is None:process.kill();process.wait()
        if x.poll() is None:x.terminate();x.wait()
        (out/'PROCESS-END.json').write_text(json.dumps({'exit':process.returncode,'disposed_QA_only':True,
            'application_shutdown_invoked':False,'result_recorded':(out/'RESULT.json').exists()},indent=2)+'\n')


if __name__=='__main__':
    raise SystemExit(main())
