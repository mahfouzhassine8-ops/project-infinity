"""Validate actual built full ZIP, original action parity, preserved controls."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET

def check(parent,candidate):
    with zipfile.ZipFile(parent) as before,zipfile.ZipFile(candidate) as after:
        prefix='skin.infinity.diggz/'
        old=ET.fromstring(before.read(prefix+'unified/VideoOSD.xml'))
        new=ET.fromstring(after.read(prefix+'unified/VideoOSD.xml'))
        control=new.find('.//control[@id="263"]');assert control is not None
        clicks=[n.text for n in control.findall('onclick')]
        assert clicks==['StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.PLAYER_ROTATION_UNLOCKED)',
                       'StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.PLAYER_ROTATION_FOLLOW_DEVICE)',
                       'Skin.ToggleSetting(Infinity.PlayerRotationUnlocked)']
        assert 'Repeat' not in ET.tostring(control,encoding='unicode')
        states={}
        for c in new.findall('.//control[@type="image"]'):
            if c.findtext('texture')=='infinity_reference/rotate.png':
                states[c.findtext('visible')]=c.find('texture').get('colordiffuse')
        assert states['!Skin.HasSetting(Infinity.PlayerRotationUnlocked)']=='FFFFFFFF'
        assert states['Skin.HasSetting(Infinity.PlayerRotationUnlocked)']=='FF00D9FF'
        for c in old.findall('.//control[@type="button"]'):
            cid=c.get('id')
            if cid in ('265','280'):continue
            changed=new.find('.//control[@type="button"][@id="'+cid+'"]')
            assert changed is not None
            assert [ET.tostring(x) for x in c.findall('onclick')]==[ET.tostring(x) for x in changed.findall('onclick')],cid
        for name in after.namelist():
            if name.endswith('/VideoOSD.xml'):
                assert b'<label>Display Mode</label>' not in after.read(name)
                parsed=ET.fromstring(after.read(name))
                for direction in ('onup','ondown','onleft','onright'):
                    assert all(n.text!='280' for n in parsed.iter(direction)), (name,direction)
        for name in ('unified/PlayerControls.xml','unified/Custom_1197_InfinityDisplayMode.xml',
                     'unified/DialogContextMenu.xml','unified/FileBrowser.xml'):
            assert before.read(prefix+name)==after.read(prefix+name),name
        version=ET.fromstring(after.read(prefix+'addon.xml')).get('version')
        if version == '1.0.5.227':
            original=ET.fromstring(before.read(prefix+'unified/Custom_1193_InfinityBrowse.xml'))
            browse=ET.fromstring(after.read(prefix+'unified/Custom_1193_InfinityBrowse.xml'))
            old_grid=original.find('.//control[@id="50"]'); grid=browse.find('.//control[@id="50"]')
            for key in ('left','top','width','bottom','itemlayout','focusedlayout'):
                assert ET.tostring(grid.find(key))==ET.tostring(old_grid.find(key)),key
            navigation=grid.findall('ondown')
            assert len(navigation)==2 and [x.text for x in navigation]==['50','13']
            assert navigation[0].get('condition')=='!['+navigation[1].get('condition')+']'
            label='INFINITY BROWSE • PICK UP WHERE YOU LEFT OFF'
            footer=next(c for c in browse.findall('./controls/control') if c.findtext('label')==label)
            assert footer.findtext('visible')==navigation[0].get('condition')
            assert browse.find('.//control[@id="13"]/visible').text==navigation[1].get('condition')
        assert after.testzip() is None
    result=dict(passed=True,artifact=Path(candidate).name,sha256=hashlib.sha256(Path(candidate).read_bytes()).hexdigest(),
                original_rotation_actions=True,white_cyan_states=True,other_playback_actions_preserved=True,
                display_popup_entry_absent=True,aspect_controls_retained=True,physical_fold_verified=False)
    print(json.dumps(result,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--candidate',required=True)
    a=p.parse_args();check(a.parent,a.candidate)
