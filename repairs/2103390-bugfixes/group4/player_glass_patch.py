#!/usr/bin/env python3
"""Group #4 exact approved video OSD / three-glass-menu source overlay.

Input must be the original immutable signed 2103390. This stages XML bytes
only: no native engine, Cobra, player session, Kodi dialog APIs or providers.
The native Video/Audio Settings dialogs remain native and their actual controls
are never replaced. This is SOURCE verification, not a Fold design lock.
"""
from __future__ import annotations
from copy import deepcopy
from decimal import Decimal
import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

BASE_SHA="778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb"
P="assets/addons/skin.infinity.diggz/"
LAYOUTS={"16x9","20x9","5x6","6x5","fallback","portrait","unified",
"responsive/base","responsive/landscape","responsive/portrait","responsive/square",
"responsive/tall","responsive/ultrawide","responsive/wide"}
GLASS="$VAR[InfinityGlassControlSurface]"
NATIVE_OSD_ONLY="Window.IsActive(10123) | Window.IsActive(10124)"
FILES=("VideoOSD.xml","Custom_1195_InfinityAudioSubtitles.xml","DialogSettings.xml")
ORIGINAL_MEMBER_COUNT=7430


def sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def tree(data: bytes):
    return ET.fromstring(data)


def serialize(root) -> bytes:
    return b"<?xml version='1.0' encoding='utf-8'?>\n"+ET.tostring(root,encoding="utf-8")


def expect(value, message):
    if not value:
        raise ValueError("Group4 approved scope/preimage failure: "+message)


def parent_of(root, child):
    for node in root.iter():
        if child in list(node):
            return node
    raise ValueError("Parent not found")


def nav_snapshot(root):
    return [(x.get('id'),x.findtext('label'),tuple(e.text for e in x.findall('onclick')))
            for x in root.findall('.//control[@type="button"]')]


def patch_osd(data: bytes, layout: str) -> bytes:
    root=tree(data)
    display=root.find('.//control[@id="255"]')
    row=root.find('.//control[@id="274"]')
    expect(display is not None and row is not None,"OSD control 255 / drawer row 274 "+layout)
    click=display.findall('onclick')
    expect(len(click)==1 and click[0].text=='Action(AspectRatio)' and
           'Display' in (display.findtext('description') or ''), "genuine Display icon")
    click[0].text="ActivateWindow(OSDVideoSettings)"
    expect(row.findtext('label')=='Video Settings' and
           [x.text for x in row.findall('onclick')]==['ActivateWindow(OSDVideoSettings)'],
           "original redundant row and native action")
    parent=parent_of(root,row)
    children=[c for c in parent if c.tag=='control']
    index=children.index(row)
    if layout=="unified":
        expect(parent.get('type')=='grouplist' and parent.get('id')=='291',"unified drawer")
        parent.remove(row)
        surface=[img.find('texture') for img in root.findall('.//control[@type="image"]')
                 if img.find('texture') is not None and
                 img.find('texture').get('colordiffuse')=='$VAR[InfinityDrawerPanel]']
        expect(len(surface)==1,"unified drawer glass surface")
        surface[0].set('colordiffuse',GLASS)
    else:
        expect(parent.get('type')=='group' and
               parent.findtext('visible')=='Skin.HasSetting(Infinity.PlayerDrawerOpen)',
               "legacy on-screen Playback popup")
        next_two=children[index+1:index+3]
        expect(len(next_two)==2 and next_two[0].get('type')=='image' and
               next_two[0].findtext('texture')=='infinity_ui/icons/settings.png' and
               next_two[1].get('type')=='label' and next_two[1].findtext('label')=='›',
               "only redundant row's adjacent icon and arrow")
        before_top=Decimal(row.findtext('top').replace('%',''))
        follow=parent.find('.//control[@id="275"]')
        expect(follow is not None,"optional Playback Speed row")
        next_top=Decimal(follow.findtext('top').replace('%',''))
        gap=next_top-before_top
        expect(Decimal('1')<gap<Decimal('200'),"native row step")
        percentage=row.findtext('top').endswith('%')
        parent.remove(row)
        parent.remove(next_two[0])
        parent.remove(next_two[1])
        remaining=[c for c in parent if c.tag=='control']
        # Remove the visual hole while preserving original relative row layout.
        for child in remaining[index:]:
            top=child.find('top')
            if top is not None and top.text:
                txt=top.text.strip()
                if txt.endswith('%')==percentage:
                    old=Decimal(txt.rstrip('%'))
                    new=old-gap
                    expect(new>=0,"shift cannot leave original drawer")
                    top.text=(format(new.normalize(),'f').rstrip('0').rstrip('.')
                              if new%1 else str(int(new)))+('%' if percentage else '')
        # Kodi explicitly links the two neighboring focus controls in legacy OSD.
        prev=parent.find('.//control[@id="272"]')
        expect(prev is not None and prev.findtext('ondown')=='274' and
               follow.findtext('onup')=='274',"redundant row focus graph")
        prev.find('ondown').text='275'
        follow.find('onup').text='272'
        mats=[img.find('texture') for img in parent.findall('./control[@type="image"]')
              if img.find('texture') is not None and
              img.find('texture').text=='$VAR[InfinityPlayerFooterTexture]']
        expect(len(mats)==1,"only original Playback drawer background")
        mats[0].text='infinity_polish/surface.png'
        mats[0].set('colordiffuse',GLASS)
    buttons=[(c.get('id'),c.findtext('label')) for c in root.findall('.//control[@type="button"]')]
    expect([x[1] for x in buttons if x[0] in ('270','272','275','276','277','278','279','281','282')]==
           ['Now Playing','Audio & Subtitles','Playback Speed','Chapters & Bookmarks',
            'Playlist','Go To Time','Player Settings','Playback Info','Close Player'] or
           ('Playback Diagnostics' in [x[1] for x in buttons]),
           "other Playback actions/preserved original wording")
    expect(root.find('.//control[@id="274"]') is None,"remove only redundant Video Settings row")
    return serialize(root)


def patch_audio(data: bytes, layout: str) -> bytes:
    root=tree(data)
    expect(root.get('id')=='1195',"Infinity audio/subtitles modal id")
    buttons={x.get('id'):x for x in root.findall('.//control[@type="button"]')}
    expect(all(k in buttons for k in ('5199','5101','5102','5103')),"real audio/subtitle controls")
    expect(buttons['5101'].findtext('onclick')=='ActivateWindow(OSDAudioSettings)' and
           buttons['5102'].findtext('onclick')=='ActivateWindow(OSDSubtitleSettings)' and
           buttons['5103'].findtext('onclick')=='ActivateWindow(10153)',
           "native audio/subtitle/service actions kept")
    surfaces=[x.find('texture') for x in root.findall('.//control[@type="image"]')
              if x.find('texture') is not None and
              x.find('texture').get('colordiffuse')=='$VAR[InfinityLegacySurface]' and
              x.find('texture').text=='infinity_glass/surface.png']
    expect(len(surfaces)==1,"audio original surface")
    surfaces[0].set('colordiffuse',GLASS)
    scrims=[x.find('texture') for x in root.findall('.//control[@type="image"]')
            if x.find('texture') is not None and x.find('texture').get('colordiffuse')=='C8000000'
            and x.find('texture').text=='infinity_reference/white.png']
    expect(len(scrims)==1,"audio original video background dim")
    scrims[0].set('colordiffuse','66000000')
    return serialize(root)


def patch_native_dialog(data: bytes, layout: str) -> bytes:
    root=tree(data)
    expect(root.tag=='window' and root.find('.//control[@id="5"]') is not None,
           "generic native settings UI resource")
    controls=root.find('controls')
    expect(controls is not None,"native controls")
    # Make ONLY 10123/10124 use the translucent material. Every other Kodi
    # settings window keeps its byte-for-byte original selected controls,
    # labels, handlers and its original opaque material when the condition is false.
    imgs=[]
    if layout=="unified":
        panel=root.find('.//control[@id="9900"]')
        expect(panel is not None,"unified full native dialog group")
        for c in panel.findall('./control[@type="image"]'):
            tex=c.find('texture')
            if tex is not None and tex.get('colordiffuse')=='$VAR[InfinityUIRepairSurface]':
                imgs.append((panel,c,tex))
        expect(len(imgs)==1,"unified native glass panel")
        zoom=ET.Element('animation',{'effect':'zoom','start':'80','end':'80',
                          'time':'0','condition':NATIVE_OSD_ONLY})
        zoom.text='Conditional'
        panel.insert(0,zoom)
    else:
        for c in controls.findall('./control[@type="image"]'):
            tex=c.find('texture')
            if tex is not None and tex.get('colordiffuse')=='$VAR[InfinityLegacySurface]' \
               and tex.text=='infinity_glass/surface.png':
                imgs.append((controls,c,tex))
        expect(len(imgs)==1,"original native dialog panel")
    for par,c,tex in imgs:
        expect(c.find('visible') is None,"native panel already conditionally shown")
        idx=list(par).index(c)
        clone=deepcopy(c)
        clone.find('texture').set('colordiffuse',GLASS)
        ET.SubElement(clone,'visible').text=NATIVE_OSD_ONLY
        ET.SubElement(c,'visible').text='!['+NATIVE_OSD_ONLY+']'
        par.insert(idx+1,clone)
    return serialize(root)


PATCHES={"VideoOSD.xml":patch_osd,
         "Custom_1195_InfinityAudioSubtitles.xml":patch_audio,
         "DialogSettings.xml":patch_native_dialog}


def proposed(original_apk:Path)->dict[str,bytes]:
    if sha(Path(original_apk).read_bytes())!=BASE_SHA:
        raise ValueError("signed parent not 2103390; no guessing")
    out={}
    with ZipFile(original_apk) as zip:
        names=zip.namelist()
        expect(len(names)==ORIGINAL_MEMBER_COUNT and len(set(names))==len(names),
               "original immutable APK member count")
        layouts={n[len(P):].rsplit('/',1)[0] for n in names
                 if n.startswith(P) and n.endswith('/VideoOSD.xml')}
        expect(layouts==LAYOUTS,"actual 14 original OSD variants")
        for layout in sorted(layouts):
            for name in FILES:
                path=P+layout+'/'+name
                if path not in names:
                    expect(name=="Custom_1195_InfinityAudioSubtitles.xml" and
                           layout=="fallback","unexpected missing original target")
                    continue
                after=PATCHES[name](zip.read(path),layout)
                expect(after!=zip.read(path),"expected change for "+path)
                out[path]=after
    return out


def inventory(original_apk:Path)->dict:
    edited=proposed(original_apk)
    with ZipFile(original_apk) as zip:
        return {"base_sha256":BASE_SHA,"original_members":len(zip.namelist()),
            "proposed_modified_members":len(edited),
            "proposed_untouched_original_members":len(zip.namelist())-len(edited),
            "proposed_added_members":0,"proposed_removed_members":0,
            "changed":[{"path":p,"before":sha(zip.read(p)),"after":sha(b)}
                       for p,b in sorted(edited.items())],
            "native_video_audio_dialogs_original_actions_preserved":True,
            "physical_fold_verified":False,"signed_apk_built":False}


def stage(original_apk:Path,dest:Path)->dict:
    original_apk=Path(original_apk).resolve()
    dest=Path(dest).resolve()
    if dest==original_apk.parent or original_apk.is_relative_to(dest):
        raise ValueError("Refusing to overwrite signed original")
    edited=proposed(original_apk)
    for path,body in edited.items():
        out=dest/path
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes(body)
    return inventory(original_apk)

if __name__=="__main__":
    import argparse,json
    p=argparse.ArgumentParser()
    p.add_argument("signed_original",type=Path)
    p.add_argument("--stage-to",type=Path)
    args=p.parse_args()
    print(json.dumps(stage(args.signed_original,args.stage_to) if args.stage_to
                     else inventory(args.signed_original),indent=2))
