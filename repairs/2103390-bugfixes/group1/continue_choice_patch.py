#!/usr/bin/env python3
"""Group #1/#03: stage *only* Infinity Home Continue Watching popup actions.

Makes movies panel 8830 and TV panel 8831 in each of the 14 original
Home XML variants call the preinstalled UI Repair popup for deliberate
Resume / Beginning. All original playback item metadata/URLs, UI routes,
and Kodi native/Cobra dialogs remain unaffected. Fail closed by digest.

Source-only patcher: never modifies signed original APK or user settings.
"""
from __future__ import annotations
import hashlib
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

SKIN = 'assets/addons/skin.infinity.diggz/'
RUNTIME = 'assets/addons/script.infinity.uirepair/runtime.py'
RUNTIME_SHA256 = 'c45b4aa5e13bac125b9b7722472d00b33769fec4961767025ef649b7e457f7fd'
HOME_HASHES = {
    'unified': '61fe23defed0536ce24f7c6d2d9b6beed5c0f3b8d04a33809a929a6b1f2532be',
    'standard': '9af19c34342b49ea160b60c90e4697fe36f3c0371ce257764de6cb82ca20e4f9',
    'responsive': '044475be12bd81055102d916a4674a074b8cb3d572a1254a0d1bf5a2fc46fb3a',
}
RUNTIME_ANCHOR = b'\ndef main(args):\n'
DISPATCH_BEFORE = b"        elif action == 'resume': resume_menu(token)\n"
DISPATCH_AFTER = (b"        elif action == 'resume': resume_menu(token)\n"
                  b"        elif action == 'home-choice': home_continue_choice(token, args[2] if len(args) > 2 else '')\n")

# The captured item key is a checked 64-hex string, not an arbitrary user URL.
ACTIONS = {
    '8830': b'      <onclick condition="System.AddonIsEnabled(script.infinity.uirepair)">RunScript(script.infinity.uirepair,home-choice,$INFO[ListItem.Property(Infinity.ResumeHub.Key)],movie)</onclick>\n',
    '8831': b'      <onclick condition="System.AddonIsEnabled(script.infinity.uirepair)">RunScript(script.infinity.uirepair,home-choice,$INFO[ListItem.Property(Infinity.ResumeHub.Key)],tv)</onclick>\n'
}

HELPER = r'''

def _continue_choice_clock(seconds):
    seconds = max(0, int(seconds))
    minutes, remain = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return ('%d:%02d:%02d' % (hours, minutes, remain)) if hours else ('%d:%02d' % (minutes, remain))


def home_continue_choice(key, media):
    """Home Continue Watching ONLY. Never write progress or choose a new source.

    The existing popup uses a modal vertical two-row Kodi control with large
    touch targets. The original Command Center creates the ListItem, so
    identity, watched checkmark, video info and saved offset are reused.
    Changing media selection never mutates persisted state or Cobra.
    """
    from controller_access import load
    if media not in ('movie', 'tv'):
        return
    controller = load()
    if not controller.hub.KEY_RE.fullmatch(str(key)):
        return
    def current():
        data = controller.hub.load_view(controller.PROFILE)
        entry = data.get('items', {}).get(key)
        if not isinstance(entry, dict) or entry.get('media') != media or entry.get('synthetic_next'):
            return None, None, '', None
        identity = controller.hub.entry_identity(entry)
        if not identity:
            return None, None, '', None
        target = controller._target(entry, data.get('sources', {}))
        return data, entry, target, identity
    data, entry, target, identity = current()
    if entry is None or not target:
        xbmcgui.Dialog().ok('Infinity Resume Hub',
            'This source is unavailable or has expired. Open the title in your provider to resolve a fresh source. Resume Hub kept your local state.')
        return
    pos = max(0.0, controller.number(entry.get('position')))
    duration = max(0.0, controller.number(entry.get('duration')))
    resume_allowed = pos > 0 and (duration <= 0 or pos < duration)
    label = str(entry.get('label') or entry.get('title') or 'Title')
    options = ([('Resume from ' + _continue_choice_clock(pos), 'resume')]
               if resume_allowed else [])
    options.append(('Play from beginning', 'begin'))
    selected = choose('Continue Watching — ' + label, options)
    if selected not in ('resume', 'begin'):
        return
    # A modal can outlive asynchronous playback progress/source updates.
    # The original identity & path must still match before launching.
    live_data, live, live_target, live_identity = current()
    if (live is None or not live_target or live_identity != identity or live_target != target or
            live.get('updated') != entry.get('updated') or
            live.get('position') != entry.get('position') or
            live.get('duration') != entry.get('duration')):
        xbmcgui.Dialog().notification('Infinity Resume Hub', 'Item changed. Open it again.', time=2500)
        return
    if selected == 'resume' and not resume_allowed:
        return
    _, item = controller._list_item(live, live_data, 'continue')
    offset = pos if selected == 'resume' else 0
    item.setProperty('ResumeTime', str(offset))
    item.setProperty('StartOffset', str(offset))
    # Preserve Kodi's original URL/listitem playback path and selected
    # saved offset; no provider search, data reset, synthetic source or
    # global PlayMedia/DialogSelect rewrite.
    xbmc.Player().play(target, item)
'''

def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def home_type(path):
    if not path.startswith(SKIN) or not path.endswith('/Home.xml'):
        return None
    section = path[len(SKIN):].rsplit('/', 1)[0]
    if section == 'unified': return 'unified'
    if section.startswith('responsive/'): return 'responsive'
    if section in ('16x9', '20x9', '5x6', '6x5', 'fallback', 'portrait'): return 'standard'
    return None

def patch_home(path: str, raw: bytes) -> bytes:
    typ = home_type(path)
    if not typ or digest(raw) != HOME_HASHES[typ]:
        raise ValueError('Unexpected Home source (refusing): ' + path)
    changed = raw
    for ident, command in ACTIONS.items():
        start = b'<control type="panel" id="' + ident.encode() + b'">'
        pattern = re.compile(re.escape(start) + rb'.*?</control>', flags=re.DOTALL)
        matches = list(pattern.finditer(changed))
        if len(matches) != 1: raise ValueError('Missing/duplicate scoped panel '+ident)
        block = matches[0].group()
        anchor = b'      </control>'
        if not block.endswith(anchor): raise ValueError('Bad panel terminator')
        if b'<onclick' in block or b'<orientation>horizontal</orientation>' not in block:
            raise ValueError('Unexpected click action or orientation')
        if command in changed: raise ValueError('Already applied')
        revised = block[:-len(anchor)] + command + anchor
        changed = changed[:matches[0].start()] + revised + changed[matches[0].end():]
    if changed.count(b'<onclick condition="System.AddonIsEnabled(script.infinity.uirepair)">RunScript(script.infinity.uirepair,home-choice,') != 2:
        raise ValueError('Invalid scoped action count')
    root = ET.fromstring(changed)
    for ident in ACTIONS:
        control = root.find('.//control[@id="'+ident+'"]')
        if control is None or len(control.findall('onclick')) != 1:
            raise ValueError('Invalid Home action binding')
    return changed

def patch_runtime(raw: bytes) -> bytes:
    if digest(raw) != RUNTIME_SHA256: raise ValueError('Unknown UI Repair runtime source')
    if raw.count(RUNTIME_ANCHOR) != 1 or raw.count(DISPATCH_BEFORE) != 1:
        raise ValueError('Unexpected UI Repair runtime anchors')
    changed = raw.replace(RUNTIME_ANCHOR, HELPER.encode('utf-8') + RUNTIME_ANCHOR, 1)
    changed = changed.replace(DISPATCH_BEFORE, DISPATCH_AFTER, 1)
    compile(changed.decode(), RUNTIME, 'exec')
    return changed

def proposed_members(apk_path: Path) -> dict[str, bytes]:
    """Refuse unfamiliar signed source; never create a candidate APK."""
    with ZipFile(apk_path) as z:
        names = [n for n in z.namelist() if home_type(n)]
        if len(names) != 14: raise ValueError('Unexpected number of Home variants')
        result = {n: patch_home(n,z.read(n)) for n in names}
        result[RUNTIME] = patch_runtime(z.read(RUNTIME))
        return result

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('original_apk',type=Path)
    args=parser.parse_args()
    staged=proposed_members(args.original_apk)
    print('Read-only / no APK output; scoped members:',len(staged))
