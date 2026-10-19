#!/usr/bin/env python3
"""Group #6 exact System Hub Silent Mode ON/OFF and native Kodi toast gate.

Only the requested System Hub 1191 receives ONE existing-theme radiobutton.
Only CGUIDialogKaiToast::DoWork() receives an Infinity-skin-gated passive
notification presentation suppressor. The notification producers, logs,
interactive dialogs, sound engine, Cobra, addons and close path are unchanged.

This is source staging; not a compiled Android engine, APK or Fold result.
"""
from __future__ import annotations
from decimal import Decimal
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import hashlib
import json

P="assets/addons/skin.infinity.diggz/"
BASE_APK_SHA="778b84a5f0d8712f250c538bacfa3c01e1352a936e0b7b9aa79cbaada9b22dbb"
HUB="Custom_1191_InfinitySystemHub.xml"
HUB_LAYOUTS={"16x9","20x9","5x6","6x5","portrait","unified",
"responsive/base","responsive/landscape","responsive/portrait","responsive/square",
"responsive/tall","responsive/ultrawide","responsive/wide"}
BUTTON_IDS=("1191101","1191102","1191103","1191104","1191106","1191107","1191105")
SILENT_ID="1191108"
SETTING="Infinity.SilentMode"
NATIVE_FILE="xbmc/dialogs/GUIDialogKaiToast.cpp"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def require(cond,msg):
    if not cond:raise ValueError("Group6 preimage/scope: "+msg)

def dec(value):
    return Decimal(value.rstrip("%"))

def fmt(x,percent=False):
    s=format(x.quantize(Decimal('.0001')).normalize(),'f')
    if '.' in s:s=s.rstrip('0').rstrip('.')
    return s+('%' if percent else '')

def add_text(node,tag,value):
    ET.SubElement(node,tag).text=str(value)
    return node

def radio(*,left,width,top,height)->ET.Element:
    ctrl=ET.Element("control",{"type":"radiobutton","id":SILENT_ID})
    for tag,val in (("label","Silent Mode"),("description","Suppress passive notification banners, not dialogs"),
                    ("font","InfinitySmall"),("textcolor","$VAR[InfinityLegacyText]"),
                    ("focusedcolor","$VAR[InfinityLegacyText]"),
                    ("disabledcolor","$VAR[InfinityLegacyDisabled]"),
                    ("left",left),("top",top),("width",width),("height",height),
                    ("aligny","center"),("textoffsetx","24"),
                    ("radioheight","32"),("radiowidth","64"),
                    ("radioposx","0"),("radioposy","0"),
                    ("onclick","Skin.ToggleSetting("+SETTING+")"),
                    ("selected","Skin.HasSetting("+SETTING+")")):
        add_text(ctrl,tag,val)
    for tag,color,file in (
      ("texturefocus","$VAR[InfinityDrawerFocusWash]","infinity_polish/field.png"),
      ("texturenofocus","$VAR[InfinityDrawerQuietRow]","infinity_polish/field.png"),
      ("textureradiooffnofocus","$VAR[InfinityLegacySecondary]","infinity_legacy/switch_off.png"),
      ("textureradioofffocus","$VAR[InfinityLegacySecondary]","infinity_legacy/switch_off.png"),
      ("textureradioonnofocus","$VAR[InfinityLegacyAccent]","infinity_legacy/switch_on.png"),
      ("textureradioonfocus","$VAR[InfinityLegacyAccent]","infinity_legacy/switch_on.png")):
        tex=add_text(ctrl,tag,file);tex.set('colordiffuse',color)
        if tag in ('texturefocus','texturenofocus'):tex.set('border','20')
    return ctrl

def original_actions(root):
    return [(c.get('id'),c.findtext('label'),[x.text for x in c.findall('onclick')])
            for c in root.findall('.//control[@type="button"]')]

def patch_hub(raw:bytes,layout:str)->bytes:
    root=ET.fromstring(raw)
    require(root.get('id')=='1191' and root.get('type')=='dialog',"native System Hub")
    require(root.find('.//control[@id="'+SILENT_ID+'"]') is None,"Silent Mode already exists")
    originals=original_actions(root)
    required=BUTTON_IDS[:-1] if layout=="unified" else BUTTON_IDS
    require(set(required).issubset({i for i,_,_ in originals}),"all original action cards")
    if layout=="unified":
        list_control=root.find('.//control[@id="1191888"]')
        require(list_control is not None and list_control.get('type')=='grouplist' and
                list_control.findtext('orientation')=='vertical',"existing unified scroll layout")
        entry=ET.Element('control',{'type':'group'})
        add_text(entry,'width','100%');add_text(entry,'height','112')
        entry.append(radio(left='0',width='100%',top='0',height='112'))
        list_control.append(entry)
    else:
        controls=root.find('controls')
        require(controls is not None,"original static hub controls")
        nodes=list(controls)
        original_rows=[]
        for id in BUTTON_IDS:
            row=root.find(f'.//control[@id="{id}"]')
            require(row is not None and row in nodes and row.get('type')=='button',
                    "original hub row "+id)
            original_rows.append(row)
        footer=[c for c in nodes if c.get('type')=='label' and
                 (c.findtext('label') or '').startswith('Infinity system tools')]
        require(len(footer)==1,"original informational footer")
        footer=footer[0]
        first, second, last=original_rows[0],original_rows[1],original_rows[-1]
        first_top, second_top, last_top, footer_top=(
            dec(c.findtext('top')) for c in (first,second,last,footer))
        step=second_top-first_top
        pct=first.findtext('top').endswith('%')
        require(all(c.findtext('top').endswith('%')==pct
                    for c in (first,second,last,footer)),
                "original row and footer coordinate units must agree")
        require(step>0 and first_top+step*6==last_top or
                (step>0 and abs(first_top+step*6-last_top)<Decimal('.001')),
                "original seven-row layout has unexpected spacing")
        # Keep *every original action row, focus area and decoration untouched*.
        # The eighth row sits immediately after POWER OPTIONS, using the same
        # documented row spacing. Move ONLY the passive footer downward one row
        # and enlarge ONLY the two existing glass background images to contain
        # the new control; no original button is moved or resized.
        next_top=last_top+step
        height=dec(last.findtext('height'))
        surfaces=[c for c in nodes if c.get('type')=='image' and
                  c.findtext('texture') in ('infinity_glass/surface.png',
                                             'infinity_glass/rim.png')]
        require(len(surfaces)==2,"exact original System Hub glass surfaces")
        for surface in surfaces:
            size=surface.find('height')
            require(size is not None and size.text.endswith('%')==pct,
                    "native System Hub background layout coordinates")
            size.text=fmt(dec(size.text)+step,pct)
        footer.find('top').text=fmt(footer_top+step,pct)
        # Validate bottom bounds in original base canvas units for every layout.
        if pct:
            top=dec(surfaces[0].findtext('top'))
            final=top+dec(surfaces[0].findtext('height'))
            require(final<=Decimal('100'),"cannot extend glass beyond Fold safe area")
            require(footer_top+step<Decimal('100'),"footer outside screen")
        else:
            full_screen=[c for c in nodes if c.get('type')=='image' and
                         c.findtext('texture')=='infinity_ui/contract_white.png' and
                         c.findtext('left')=='0' and c.findtext('top')=='0']
            require(len(full_screen)>=1,"original fullscreen backdrop")
            cap=dec(full_screen[0].findtext('height'))
            final=dec(surfaces[0].findtext('top'))+dec(surfaces[0].findtext('height'))
            require(final<=cap,"cannot extend glass beyond Fold safe area")
            require(footer_top+step+dec(footer.findtext('height'))<=cap,
                    "footer outside screen")
        require(next_top>last_top and footer_top+step>next_top,
                "new switch must sit after last original row, before footer")
        controls.insert(nodes.index(footer),radio(
            left=last.findtext('left'),
            width=last.findtext('width'),
            top=fmt(next_top,pct),
            height=last.findtext('height')))
    after=original_actions(root)
    require(after==originals,"pre-existing hub actions/IDs/labels unchanged")
    silent=root.find(".//control[@id='"+SILENT_ID+"']")
    require(len(root.findall(".//control[@id='"+SILENT_ID+"']"))==1 and
            silent.get('type')=='radiobutton' and silent.findtext('label')=="Silent Mode" and
            silent.findtext('selected')=="Skin.HasSetting(Infinity.SilentMode)" and
            silent.findtext('onclick')=="Skin.ToggleSetting(Infinity.SilentMode)",
            "one persistent toggle only")
    return b"<?xml version='1.0' encoding='utf-8'?>\n"+ET.tostring(root,encoding='utf-8')


TOAST_INSERT=r'''  // GROUP6_SILENT_MODE_V1: user-selected, skin-scoped presentation gate only.
  // Run on the existing GUI toast worker BEFORE holding its notification lock.
  // Actual event logs, producing add-on jobs and interactive dialogs are untouched.
  auto* infinityGui = CServiceBroker::GetGUI();
  auto infinitySettings = CServiceBroker::GetSettingsComponent()->GetSettings();
  if (infinityGui && infinitySettings &&
      infinitySettings->GetString(CSettings::SETTING_LOOKANDFEEL_SKIN) ==
          "skin.infinity.diggz" &&
      infinityGui->GetInfoManager().EvaluateBool(
          "Skin.HasSetting(Infinity.SilentMode)", WINDOW_HOME))
  {
    // Discard only pending passive Kodi KaiToast messages. This also suppresses
    // their toast sound/haptic, not playback/media or Android system audio.
    std::unique_lock<CCriticalSection> silentLock(m_critical);
    while (!m_notifications.empty())
      m_notifications.pop();
    silentLock.unlock();
    if (IsActive())
      Close(); // Immediately dismiss only an already-visible modeless toast.
    return false; // Never replay a suppressed backlog on switching Off.
  }
'''


def patch_toast_cpp(raw:bytes)->bytes:
    text=raw.decode('utf-8')
    if 'GROUP6_SILENT_MODE_V1' in text:
        raise ValueError("Silent Mode native toast patch already applied")
    anchor='bool CGUIDialogKaiToast::DoWork()\n{\n  std::unique_lock<CCriticalSection> lock(m_critical);'
    if text.count(anchor)!=1 or text.count("SetSound(toast.withSound);")!=1 or \
       text.count("CServiceBroker::GetPeripherals().OnUserNotification();")!=1:
        raise ValueError("Unexpected actual native Kodi toast renderer preimage")
    for inc in ['#include "GUIInfoManager.h"',
                '#include "guilib/GUIComponent.h"',
                '#include "guilib/WindowIDs.h"',
                '#include "settings/Settings.h"',
                '#include "settings/SettingsComponent.h"']:
        if inc not in text:
            head='#include "ServiceBroker.h"'
            if text.count(head)!=1:raise ValueError("C++ includes drift")
            text=text.replace(head,head+'\n'+inc,1)
    text=text.replace(anchor,'bool CGUIDialogKaiToast::DoWork()\n{\n'+TOAST_INSERT+
                      '  std::unique_lock<CCriticalSection> lock(m_critical);',1)
    return text.encode('utf-8')


def skin_inventory(signed_apk:Path)->dict:
    signed_apk=Path(signed_apk)
    if sha(signed_apk.read_bytes())!=BASE_APK_SHA:
        raise ValueError("Unknown 2103390 original; do not patch")
    out={}
    with ZipFile(signed_apk) as z:
        names=z.namelist()
        if len(names)!=7430 or len(set(names))!=7430:
            raise ValueError("Original signed member inventory unknown")
        layouts={x[len(P):].rsplit('/',1)[0] for x in names if x.startswith(P)
                 and x.endswith('/'+HUB)}
        require(layouts==HUB_LAYOUTS,"13 actual original System Hub variants")
        for layout in sorted(layouts):
            path=P+layout+'/'+HUB
            old=z.read(path);new=patch_hub(old,layout)
            require(old!=new,path)
            out[path]=new
    return out


def inventory(signed_apk:Path)->dict:
    out=skin_inventory(signed_apk)
    with ZipFile(signed_apk) as z:
        return {"signed_parent_sha256":BASE_APK_SHA,"original_members":len(z.namelist()),
            "changed_skin_members":len(out),
            "unchanged_original_members":len(z.namelist())-len(out),
            "native_toast_source_overlay":NATIVE_FILE,
            "native_toast_compiled":False,
            "signed_apk_created":False,
            "physical_fold_verified":False,
            "silent_mode_default":"OFF",
            "new_system_hub_controls":1,
            "new_services":0,"new_databases":0,
            "changed":[{"path":p,"before_sha256":sha(z.read(p)),
                        "after_sha256":sha(b)} for p,b in sorted(out.items())]}


def stage(signed_apk:Path,output_dir:Path)->dict:
    signed_apk=Path(signed_apk).resolve();output_dir=Path(output_dir).resolve()
    if output_dir==signed_apk.parent or signed_apk.is_relative_to(output_dir):
        raise ValueError("Refuse overwrite of signed original")
    out=skin_inventory(signed_apk)
    for p,body in out.items():
        dest=output_dir/p
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(body)
    return inventory(signed_apk)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("signed_original",type=Path)
    a.add_argument("--stage-to",type=Path)
    args=a.parse_args()
    print(json.dumps(stage(args.signed_original,args.stage_to) if args.stage_to
                     else inventory(args.signed_original),indent=2))
