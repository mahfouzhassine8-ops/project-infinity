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
    require(set(BUTTON_IDS).issubset({i for i,_,_ in originals}),"all original action cards")
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
        positions=[]
        for id in BUTTON_IDS:
            row=root.find(f'.//control[@id="{id}"]')
            require(row is not None and row in nodes and row.get('type')=='button',
                    "original hub row "+id)
            index=nodes.index(row)
            require(len(nodes)>index+2 and nodes[index+1].get('type')=='image' and
                    nodes[index+2].get('type')=='label',"original decorated row triplet")
            positions.append((row,nodes[index+1],nodes[index+2]))
        first,second=positions[0][0],positions[1][0]
        footers=[c for c in nodes if c.get('type')=='label' and
                 (c.findtext('label') or '').startswith('Infinity system tools')]
        require(len(footers)==1,"existing informational footer preserved")
        footer=footers[0]
        start=dec(first.findtext('top'))
        second_top=dec(second.findtext('top'))
        footer_top=dec(footer.findtext('top'))
        pct=first.findtext('top').endswith('%')
        require(pct==second.findtext('top').endswith('%')==
                footer.findtext('top').endswith('%'),"same coordinate units")
        old_step=second_top-start
        old_height=dec(first.findtext('height'))
        require(old_step>0 and old_height>0 and footer_top>start,"positive original layout")
        safety=Decimal('1') if pct else Decimal('12')
        step=(footer_top-start-safety)/Decimal(8)
        require(step>0 and step<old_step,"eight rows must fit without touching footer")
        # Estimate px / native top-unit from the original element height/step.
        # For percent variants, top percentages and button heights are different
        # units; derive relative ratio from original sibling coordinates.
        scale=old_height/old_step
        new_height=min(old_height,(step*scale*Decimal('.91')))
        require(new_height>=Decimal('62'),"touch target too small")
        # All existing row actions, order and artwork remain exactly the same.
        # Only vertical geometry is compacted within original panel and footer.
        for i,(button,icon,label) in enumerate(positions):
            old=dec(button.findtext('top'))
            proposed=start+step*Decimal(i)
            factor=new_height/old_height
            button.find('top').text=fmt(proposed,pct)
            button.find('height').text=fmt(new_height)
            for associated in (icon,label):
                child_top=associated.find('top')
                child_height=associated.find('height')
                require(child_top is not None and child_height is not None,"decorations intact")
                offset=dec(child_top.text)-old
                child_top.text=fmt(proposed+offset*factor,pct)
                child_height.text=fmt(dec(child_height.text)*factor)
        # Move ONLY the existing Health orb with its preserved Health Center row.
        orb=[x for x in controls.findall('control[@type="image"]')
             if x.findtext('texture')=='infinity_experience/health-orb.png']
        require(len(orb)==1,"original Health Center status orb")
        oldhealth=start+old_step*Decimal(2)
        newhealth=start+step*Decimal(2)
        orb[0].find('top').text=fmt(dec(orb[0].findtext('top'))+newhealth-oldhealth,pct)
        # Append exactly ONE new toggle; all original buttons preserved.
        top=fmt(start+step*Decimal(7),pct)
        button=positions[-1][0]
        index=nodes.index(positions[-1][2])+1
        controls.insert(index,radio(left=button.findtext('left'),width=button.findtext('width'),
                                    top=top,height=fmt(new_height)))
        require(start+Decimal(7)*step+new_height/scale<footer_top,
                "new switch cannot collide with original footer")
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
