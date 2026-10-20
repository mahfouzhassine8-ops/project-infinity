#!/usr/bin/env python3
"""Scoped Fold corrections, exclusively from the immutable signed 2103392 APK.

No profile writes, provider migrations, Cobra changes or weakened native admission.
The complete parent hash and the committed member ledger are mandatory build inputs.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = 'd4ae792898b26bbea47b97310244b31304f972f062e692c1562edef3ac0bbd58'
COMMIT = '27d5f2fdfb64818134f988caf327f20b33160e1c'
CC = 'script.infinity.commandcenter'
UI = 'script.infinity.uirepair'
WB = 'script.infinity.watchedbridge'
SKIN = 'skin.infinity.diggz'
PACKAGES = ((CC, '0.3.5.22', '0.3.5.23'), (WB, '1.0.3', '1.0.4'),
            (UI, '0.1.4', '0.1.5'), ('script.infinity.rails', '0.2.7', '0.2.7'),
            (SKIN, '1.0.5.229', '1.0.5.230'))
POSTERS = {8101:'movies', 8102:'tvshows', 8601:'movies', 8602:'tvshows',
           8701:'movies', 8702:'tvshows', 8801:'movies', 8802:'tvshows'}

def require(value, reason):
    if not value:
        raise ValueError('2103393 correction refused: ' + reason)

def sha(value):
    return hashlib.sha256(value).hexdigest()

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def once(raw, old, new):
    require(raw.count(old) == 1, 'missing/ambiguous source anchor ' + repr(old[:100]))
    return raw.replace(old, new, 1)

def retag(raw, addon, old, new):
    root = ET.fromstring(raw)
    require(root.get('id') == addon and root.get('version') == old, 'wrong manifest ' + addon)
    if old == new:
        return raw
    match = re.search(rb'<addon\b[^>]*>', raw)
    tag = once(match.group(), ('version="'+old+'"').encode(), ('version="'+new+'"').encode())
    return raw[:match.start()] + tag + raw[match.end():]

def controller_plugin(raw):
    old = b'''        if number(preference.get('failures')) < 2:
            # Validate stored preferences and the entry's independently captured
            # stable source separately. A stale/invalid preferred URL must not
            # mask an already verified, still installed fallback plugin route.
            choices = ((preference.get('route'), entry.get('stable_source'))
                       if entry.get('media') == 'tv' else
                       (preference.get('route') or entry.get('stable_source'),))
            for saved in choices:
                route = stable_route(saved)
                if not route:
                    continue
                host = route.split('/')[2] if route.startswith('plugin://') else ''
                if not host or _has_addon(host, render):
                    return route
'''
    new = b'''        # Movie and TV entries both retain an independent captured route.
        # A stale preference must not mask it. Do not retry the very same
        # failed preferred route after two recorded failures.
        preferred = preference.get('route')
        failed = number(preference.get('failures')) >= 2
        choices = ([] if failed else [preferred])
        captured = entry.get('stable_source')
        if captured != preferred or not failed:
            choices.append(captured)
        for saved in choices:
            route = stable_route(saved)
            if not route:
                continue
            host = route.split('/')[2] if route.startswith('plugin://') else ''
            if not host or _has_addon(host, render):
                return route
'''
    raw = once(raw, old, new)
    anchor = b"def listing(media='all', bucket='continue', list_name=''):\n"
    title = '''def _category(media, bucket='', list_name=''):
    title = 'Movies' if media == 'movie' else ('TV Shows' if media == 'tv' else 'Resume Hub')
    names = {'continue': 'Continue Playing', 'next': 'Next Episodes',
             'progress': 'Progress Shows', 'watchlist': 'Watchlist',
             'collection': 'Collection', 'history': 'Watched History',
             'watched': 'Watched History', 'ratings': 'Ratings',
             'custom-lists': 'Custom Lists', 'list': list_name or 'Custom List'}
    return title + ' — ' + names[bucket] if bucket in names else 'Infinity ' + title


'''.encode()
    raw = once(raw, anchor, title + anchor + b'    xbmcplugin.setPluginCategory(HANDLE, _category(media, bucket, list_name))\n')
    raw = once(raw, b"title = 'Infinity Movies' if media == 'movie' else 'Infinity TV'", b'title = _category(media)')
    raw = once(raw, b"xbmcplugin.setPluginCategory(HANDLE, 'Infinity Custom Lists')", b"xbmcplugin.setPluginCategory(HANDLE, _category(media, 'custom-lists'))")
    return raw

def ui_plugin(raw):
    # Legacy saved records are still local records. Their management menu
    # must not depend on a resolved stream or additive verified media IDs.
    return once(raw, b"if plugin.hub.KEY_RE.fullmatch(key) and plugin.hub.entry_identity(entry):",
                b"if plugin.hub.KEY_RE.fullmatch(key) and not entry.get('synthetic_next'):")

def controller_access(raw):
    raw = once(raw, b"if not entry or not plugin.hub.entry_identity(entry) or entry.get('synthetic_next'):",
               b"if not entry or entry.get('key') != key or entry.get('synthetic_next'):")
    raw = once(raw, b"        rows.append((label, op))", b'''        # Unverified legacy identity permits local record management only.
        # Do not manufacture watched/episode identities for Kodi library sync.
        if not plugin.hub.entry_identity(entry) and op in ('mark-watched', 'mark-unwatched'):
            continue
        rows.append((label, op))''')
    raw = once(raw, b"        if not current or not hub.same_identity(hub.entry_identity(original), hub.entry_identity(current)):\n            return False",
        b'''        if not current:
            return False
        original_identity, current_identity = hub.entry_identity(original), hub.entry_identity(current)
        if original_identity or current_identity:
            if not hub.same_identity(original_identity, current_identity):
                return False
        elif (original.get('key') != key or current.get('key') != key or
              original != current or op in ('mark-watched', 'mark-unwatched')):
            # A legacy record has no verified media identity. Require its
            # exact saved snapshot under the existing writer gate instead.
            return False''')
    return raw

def option_b(raw):
    raw = once(raw, b"CONTROLS = {8101: 'movies', 8102: 'tvshows'}",
               ('CONTROLS = ' + repr(POSTERS)).encode())
    raw = once(raw, b"if len(args) != 3 or args[0] not in ('8101', '8102'):",
                b"if len(args) != 3 or args[0] not in tuple(str(value) for value in CONTROLS):")
    # Kodi serializes an empty favourites vector as null. Keep the popup's
    # existing Favorite action usable for the first favourite too.
    return once(raw,b"for fav in current.get('favourites',[]):",b"for fav in (current.get('favourites') or []):")

def silent_row(raw):
    # Replace ONLY the existing tappable row; independent Health Center
    # image and all other System Hub controls retain their original bytes.
    match = re.search(rb'<control type="radiobutton" id="1191108"[^>]*>.*?</control>', raw, re.S)
    require(match is not None, 'missing original Silent Mode row')
    old = match.group()
    root = ET.fromstring(old)
    require(root.findtext('label') == 'Silent Mode' and
            root.findtext('onclick') == 'Skin.ToggleSetting(Infinity.SilentMode)', 'wrong silent action')
    # Preserve actual row bounds and all navigation inherited from its group.
    bounds = ''.join('<'+k+'>'+root.findtext(k)+'</'+k+'>' for k in ('left','top','width','height'))
    # Match the Health Center dot's right/top/size in THIS layout.
    tree = ET.fromstring(raw)
    health = tree.find('.//control[@id="1191103"]')
    owner = next(p for p in tree.iter() if health in list(p))
    dots = [c for c in owner.findall('control') if c.findtext('texture') == 'infinity_experience/health-orb.png']
    require(len(dots) == 1, 'missing/ambiguous independent Health Center dot')
    dot = dots[0]
    geo = ''.join('<'+k+'>'+dot.findtext(k)+'</'+k+'>' for k in ('left','right','top','width','height') if dot.findtext(k) is not None)
    new = ('''<control type="button" id="1191108"><label>Silent Mode</label>
<font>InfinitySmall</font><align>left</align><aligny>center</aligny>
<textoffsetx>84</textoffsetx><textoffsety>0</textoffsety>
<textcolor>$VAR[InfinityLegacyText]</textcolor><focusedcolor>$VAR[InfinityLegacyText]</focusedcolor>
<texturefocus border="20" colordiffuse="$VAR[InfinityDrawerFocusWash]">infinity_polish/field.png</texturefocus>
<texturenofocus border="20" colordiffuse="$VAR[InfinityDrawerQuietRow]">infinity_polish/field.png</texturenofocus>
<onclick>Skin.ToggleSetting(Infinity.SilentMode)</onclick>''' + bounds + '''</control>
<control type="image">''' + bounds + '''<texture border="20" colordiffuse="4024A8FF">infinity_polish/field.png</texture>
<visible>Skin.HasSetting(Infinity.SilentMode)</visible></control>
<control type="image">''' + geo + '''<texture border="0" colordiffuse="FF24A8FF">infinity_experience/health-orb.png</texture>
<visible>Skin.HasSetting(Infinity.SilentMode)</visible></control>''').encode()
    return raw[:match.start()] + new + raw[match.end():]

def browser(raw):
    # A textbox in a Kodi item layout does not implement ListItem label
    # truncation. Use Kodi's actual bounded list label, with a reserved arrow
    # gutter. Native metadata and every selectable action remain untouched.
    changed = 0
    def replace(m):
        nonlocal changed
        b = m.group()
        if b'$INFO[ListItem.Label]' not in b:
            return b
        changed += 1
        b = b.replace(b'type="textbox"', b'type="label"', 1)
        for tag in ('right','width','bottom','height','autoscroll','wrapmultiline','scroll','aligny'):
            b = re.sub(rb'\s*<'+tag.encode()+rb'\b[^>]*>.*?</'+tag.encode()+rb'>',b'',b,flags=re.S)
        b = re.sub(rb'<left>.*?</left>', b'<left>22%</left>', b, count=1, flags=re.S)
        b = re.sub(rb'<top>.*?</top>', b'<top>12%</top>', b, count=1, flags=re.S)
        b = b.replace(b'<font>InfinitySmall</font>', b'<font>InfinityTiny</font>')
        return b.replace(b'</control>', b'<width>64%</width><height>76%</height><aligny>center</aligny><scroll>false</scroll></control>', 1)
    raw = re.sub(rb'<control type="(?:textbox|label)">.*?</control>', replace, raw, flags=re.S)
    require(changed == 2, 'browser must have exactly two label templates')
    return raw

def osd_contrast(raw):
    # The existing Play/Pause disc is dark blue in every theme. Its dynamic
    # light-theme text tint painted a dark glyph on that dark disc. Rotation
    # has the inverse problem: a permanently white glyph on the light footer.
    # Preserve the approved artwork, positions, visibility and real actions.
    counts = {'play':0,'pause':0,'rotate':0}
    def replace(m):
        b=m.group()
        for icon in ('play','pause'):
            if ('>infinity_reference/'+icon+'.png</texture>').encode() in b:
                counts[icon]+=1
                old=('colordiffuse="$VAR[InfinityGlassTextPrimary]">infinity_reference/'+icon+'.png').encode()
                if old in b:
                    return once(b,old,('colordiffuse="FFFFFFFF">infinity_reference/'+icon+'.png').encode())
                require(('colordiffuse="FFFFFFFF">infinity_reference/'+icon+'.png').encode() in b,'unexpected play/pause tint')
                return b
        old=b'colordiffuse="FFFFFFFF">infinity_reference/rotate.png'
        if old in b:
            counts['rotate']+=1
            return once(b,old,b'colordiffuse="$VAR[InfinityGlassTextPrimary]">infinity_reference/rotate.png')
        return b
    result=re.sub(rb'<control type="image">.*?</control>',replace,raw,flags=re.S)
    require(counts=={'play':1,'pause':1,'rotate':1},'unexpected original OSD state images')
    return result

def clock_cluster(raw):
    # The crescent was baked into header_dark.png at x=1593..1631, independent
    # of the responsive proportional clock. The prior 708-unit correction
    # moved a DIFFERENT object, the health orb. Preserve that orb and anchor
    # the extracted original crescent to Kodi's measured auto-width time.
    start=raw.index(b'<include name="InfinityHomeStatusCluster">')
    stop=raw.index(b'</include>',start)+len(b'</include>')
    section=raw[start:stop]
    root=ET.fromstring(section);definition=root.find('definition')
    clocks=[n for n in definition.findall('control') if n.findtext('label')=='$INFO[System.Time]']
    require(len(clocks)==1,'wrong status cluster')
    clock=clocks[0]
    image=ET.Element('control',{'type':'image'})
    ET.SubElement(image,'texture').text='infinity_ui/clock_moon.png'
    ET.SubElement(image,'aspectratio').text='keep'
    light='[String.IsEqual(Window(Home).Property(Infinity.SystemTheme),light) | String.IsEqual(Window(Home).Property(Infinity.SystemTheme),Light) | [String.IsEmpty(Window(Home).Property(Infinity.SystemTheme)) + String.IsEqual(Window(Home).Property(Infinity.NativeSystemTheme),light)] | [String.IsEmpty(Window(Home).Property(Infinity.SystemTheme)) + String.IsEqual(Window(Home).Property(Infinity.NativeSystemTheme),Light)]]'
    ET.SubElement(image,'visible').text='!'+light+' + !Control.IsVisible(29900)'
    for element in (clock,):
        for node in list(element):
            if node.tag in ('left','right','top','bottom','centerleft','centertop','width','height','align'):
                element.remove(node)
    for tag,value in (('left','0'),('centertop','50%'),('width','18'),('height','18')):
        ET.SubElement(image,tag).text=value
    for tag,value in (('left','0'),('top','0'),('height','$PARAM[timeheight]'),('align','right')):
        ET.SubElement(clock,tag).text=value
    width=ET.SubElement(clock,'width',{'min':'1','max':'$PARAM[timewidth]'})
    width.text='auto'
    group=ET.Element('control',{'type':'grouplist'})
    for tag,value in (('left','$PARAM[timeleft]'),('top','$PARAM[timetop]'),
                     ('width','$PARAM[timewidth]'),('height','$PARAM[timeheight]'),
                     ('orientation','horizontal'),('align','right'),('itemgap','8'),('usecontrolcoords','true')):
        ET.SubElement(group,tag).text=value
    group.extend((image,clock))
    definition.remove(clock);definition.append(group)
    updated=ET.tostring(root,encoding='utf-8')
    return raw[:start]+updated+raw[stop:]

def compact_player_settings(original):
    # Reuse the original native settings templates and actions; keep scrolling
    # controls 5/60 and all cloned native settings. This is a separate resource,
    # selected only for the three Infinity video-player settings windows.
    root = ET.fromstring(original)
    panel = root.find('.//control[@id="9900"]')
    require(panel is not None, 'missing unified settings group')
    for n in list(panel):
        if n.tag in ('animation','left','right','top','bottom'):
            panel.remove(n)
    for tag,value in (('centerleft','50%'),('centertop','50%'),('width','840'),('height','740')):
        ET.SubElement(panel,tag).text=value
    for image in list(panel.findall('control')):
        if image.get('type') == 'image' and image.findtext('texture') == 'infinity_glass/surface.png':
            if image.findtext('visible','').startswith('!'):
                panel.remove(image)
            else:
                for n in list(image.findall('visible')):
                    image.remove(n)
    scrim = root.find('./controls/control[@type="image"]/texture')
    require(scrim is not None, 'missing settings scrim')
    scrim.set('colordiffuse','33000000')
    return b"<?xml version='1.0' encoding='utf-8'?>\n" + ET.tostring(root,encoding='utf-8')

def components(original):
    result = dict(original)
    changes = {CC+'/plugin.py':controller_plugin, UI+'/plugin.py':ui_plugin,
               UI+'/controller_access.py':controller_access, UI+'/home_option_b.py':option_b}
    for name, fn in changes.items():
        result[name] = fn(original[name])
    for name, raw in original.items():
        if not name.startswith(SKIN+'/'):
            continue
        if name.endswith('/Custom_1191_InfinitySystemHub.xml'):
            result[name] = silent_row(raw)
        elif name.endswith('/AddonBrowser.xml'):
            result[name] = browser(raw)
        elif name.endswith('/VideoOSD.xml'):
            result[name] = osd_contrast(raw)
        elif name.endswith('/Includes_InfinityHomeUnified.xml'):
            result[name] = clock_cluster(raw)
        elif name.endswith('/Home.xml'):
            result[name] = once(raw,b'>infinity_ui/header_dark.png</texture>',
                                    b'>infinity_ui/header_dark_clock_safe.png</texture>')
    for asset in ('header_dark_clock_safe','clock_moon'):
        result[SKIN+'/media/infinity_ui/'+asset+'.png'] = base64.b64decode((HERE/'assets'/(asset+'.png.b64')).read_text(),validate=False)
    compact = compact_player_settings(original[SKIN+'/unified/DialogSettings.xml'])
    layouts = [n.rsplit('/',1)[0] for n in original if n.startswith(SKIN+'/') and n.endswith('/DialogSettings.xml')]
    require(len(layouts)==14, 'incomplete original native settings layout inventory')
    for layout in layouts:
        result[layout+'/InfinityPlayerSettings.xml'] = compact
    for addon, old, new in PACKAGES:
        result[addon+'/addon.xml'] = retag(original[addon+'/addon.xml'], addon, old, new)
    result[CC+'/checkpoint_runtime.py'] = once(original[CC+'/checkpoint_runtime.py'],
        b'ADDON_VERSION = "0.3.5.22"', b'ADDON_VERSION = "0.3.5.23"')
    result[UI+'/addon.xml'] = once(result[UI+'/addon.xml'],
        b'addon="script.infinity.commandcenter" version="0.3.5.22"',
        b'addon="script.infinity.commandcenter" version="0.3.5.23"')
    result[WB+'/controller.py'] = once(original[WB+'/controller.py'],
        b'get("version") != "0.3.5.22"', b'get("version") != "0.3.5.23"')
    for addon in (UI,WB):
        name = addon+'/CONTROLLER-PREIMAGES.json'
        pins = json.loads(original[name])
        require(len(pins)==13 and all(sha(original[CC+'/'+n])==h for n,h in pins.items()), 'incomplete protected controller pins')
        result[name] = (json.dumps({n:sha(result[CC+'/'+n]) for n in pins},indent=2,sort_keys=True)+'\n').encode()
    # Extend only the current candidate's explicit protected exceptions.
    # All historical baselines and their hashes remain in the manifest.
    name = SKIN+'/Infinity-Protected-Manifest.json'
    manifest = json.loads(original[name])
    exceptions = {}
    for path, body in result.items():
        if path.startswith(SKIN+'/') and original.get(path) != body:
            relative = path[len(SKIN)+1:]
            exceptions[relative] = {'before':sha(original[path]) if path in original else None,'after':sha(body)}
            manifest['protected_files'][relative] = sha(body)
    manifest.update(candidate=230, candidate_version='1.0.5.230', skin_version='1.0.5.230',candidate_locked=False)
    manifest['fold_corrective_230'] = {'parent_apk_sha256':PARENT,'explicit_protected_exceptions':exceptions,
                                     'cobra_changed':False,'physical_fold_verified':False,'final_lock':False}
    result[name] = (json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    return result

def read_parent(apk):
    require(digest(apk) == PARENT, 'not the immutable signed 2103392 APK')
    with ZipFile(apk) as z:
        require(len(z.namelist()) == len(set(z.namelist())) and z.testzip() is None, 'corrupt/ambiguous parent')
        return {n[len('assets/addons/'):]:z.read(n) for n in z.namelist()
                if n.startswith('assets/addons/') and not n.endswith('/') and
                n[len('assets/addons/'):].split('/')[0] in {x[0] for x in PACKAGES}}

def ledger(before, after):
    require(set(before).issubset(after), 'original component member removed')
    changed = {n:{'before':sha(before[n]) if n in before else None,'after':sha(b)}
               for n,b in after.items() if before.get(n)!=b}
    require(not any('cobra' in n.lower() for n in changed), 'Cobra target forbidden')
    return {'schema':1, 'parent_apk_sha256':PARENT, 'parent_commit':COMMIT,
            'changed_members':dict(sorted(changed.items())), 'removed_members':[],
            'versions':{a:new for a,_,new in PACKAGES}, 'physical_fold_verified':False,
            'original_sigsegv_fixed':False, 'final_lock':False}

def stage(apk, destination):
    before = read_parent(apk)
    after = components(before)
    proof = ledger(before, after)
    require(proof == json.loads((HERE/'MEMBER-DELTA.json').read_text()), 'unreviewed component delta')
    require(not destination.exists(), 'stage already exists')
    for n, b in after.items():
        if n.endswith('.py'):
            compile(b,n,'exec')
        elif n.endswith('.xml'):
            ET.fromstring(b)
        p = destination/n
        p.parent.mkdir(exist_ok=True,parents=True)
        p.write_bytes(b)
    return proof

def main():
    p = argparse.ArgumentParser()
    p.add_argument('apk',type=Path)
    p.add_argument('destination',type=Path)
    args=p.parse_args()
    print(json.dumps(stage(args.apk,args.destination),indent=2))

if __name__ == '__main__':
    main()
