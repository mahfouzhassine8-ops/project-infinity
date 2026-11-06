"""Isolated skin candidate, never a runtime overlay or user installer.

Requires exact delivered input hashes. Active-device identity remains a gate
before applying it to the release overlay. Does not change actions or writers.
"""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SKIN = ROOT / 'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified'
EXPECTED = {
    'DialogVideoInfo.xml': '3e1323aec4af3121d4283d55bcb77f5b1d05dd892593854835e36e7b64b51460',
    'Includes_InfinityMediaLists.xml': 'a9e6ea83bb6aad8b598e6d559963097e47404dec98f7a0399b872e82e0f32896',
}


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    inventory = {}
    for name, expected in EXPECTED.items():
        raw = (SKIN / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected, 'DELIVERED_INPUT_CHANGED:' + name
        text = raw.decode()
        if name == 'DialogVideoInfo.xml':
            marker = '<control type="grouplist" id="9000">'
            start = text.index(marker)
            end = text.index('<control type="togglebutton" id="8">', start)
            section = text[start:end]
            assert section.count('<width>86%</width>') == 1
            text = text[:start] + section.replace('<width>86%</width>',
                '<width min="86%" max="86%">auto</width>') + text[end:]
            # Native groups check the last rendered child first. Preserve the
            # exact video rectangle/condition, but put buttons and Cast above it.
            video = re.search(r'    <control type="videowindow">.*?</control>\n', text, re.S)
            assert video is not None and len(re.findall('type="videowindow"', text)) == 1
            block = video.group()
            text = text[:video.start()] + text[video.end():]
            start = text.index('    ' + marker)
            text = text[:start] + block + text[start:]
        else:
            old = '<visible>ListItem.IsResumable | Integer.IsGreater(ListItem.PlayCount,0) | ListItem.IsPlaying</visible>'
            assert text.count(old) == 1
            text = text.replace(old, '<visible>ListItem.IsResumable | Integer.IsGreater(ListItem.PlayCount,0) | ListItem.IsPlaying | String.IsEqual(ListItem.Overlay,OverlayWatched.png) | String.IsEqual(ListItem.Property(Infinity.ResumeHub.Watched),true)</visible>')
        ET.fromstring(text)
        data = text.encode()
        (out / name).write_bytes(data)
        inventory[name] = dict(before_sha256=expected, candidate_sha256=hashlib.sha256(data).hexdigest())
    (out / 'CANDIDATE.json').write_text(json.dumps(dict(
        source_reference='0aa597f1ec152a89d291eef10b8627cd15bd421a',
        active_device_binding='UNVERIFIED', installer=False, runtime_overlay_modified=False,
        files=inventory, native_changed=False, authentication_changed=False,
        actions_changed=False, watched_writers_changed=False, Android='NOT_RUN'), indent=2) + '\n')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('out', type=Path)
    prepare(parser.parse_args().out)
