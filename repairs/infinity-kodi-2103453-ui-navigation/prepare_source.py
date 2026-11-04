"""Generate a reviewable Kodi UI source overlay from exact signed 2103453 text.

This never builds an APK/component or modifies the input APK. Original shared
dialogs/includes remain byte-identical; Videos receives scoped variants.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as E
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
PREFIX = 'assets/addons/skin.infinity.diggz/'
CC_PREFIX = 'assets/addons/script.infinity.commandcenter/'
NEW_IDS = {1130: 1136, 1131: 1137, 1132: 1138}


def put(node, tag, value, **attrs):
    old = node.findall(tag)
    for child in old:
        node.remove(child)
    new = E.Element(tag, attrs)
    new.text = value
    node.insert(0, new)  # Explicit control values precede inherited include values.
    return new


def drop(node, *tags):
    for tag in tags:
        for child in node.findall(tag):
            node.remove(child)


def xml(node):
    E.indent(node, space='  ')
    return b"<?xml version='1.0' encoding='utf-8'?>\n" + E.tostring(node, encoding='utf-8') + b'\n'


def remap(text):
    for old, new in NEW_IDS.items():
        text = re.sub(r'(?<!\d)' + str(old) + r'(?!\d)', str(new), text)
    return text


def panel_skin(group):
    for texture in ['surface.png', 'rim.png']:
        image = E.Element('control', {'type': 'image'})
        for tag, value in [('width', '100%'), ('height', '100%')]:
            E.SubElement(image, tag).text = value
        E.SubElement(image, 'texture', {'border': '24', 'colordiffuse':
                     '$VAR[InfinityDrawerPanel]' if texture == 'surface.png'
                     else '$VAR[InfinityGlassFocus]'}).text = 'infinity_polish/' + texture
        group.insert(0 if texture == 'surface.png' else 1, image)


def close_button(group, target, content):
    button = E.SubElement(group, 'control', {'type': 'button', 'id': '8999'})
    for tag, value in [('right', '18'), ('top', '18'), ('width', '128'),
                       ('height', '128'), ('label', ''), ('ondown', content),
                       ('onleft', content), ('onup', content),
                       ('onclick', 'Dialog.Close(%s)' % target)]:
        E.SubElement(button, tag).text = value
    for tag, color in [('texturefocus', 'InfinityDrawerFocusWash'),
                       ('texturenofocus', 'InfinityDrawerQuietRow')]:
        E.SubElement(button, tag, {'border': '20', 'colordiffuse': '$VAR[%s]' % color}).text = 'infinity_polish/field.png'
    icon = E.SubElement(group, 'control', {'type': 'image'})
    for tag, value in [('right', '58'), ('top', '58'), ('width', '48'), ('height', '48')]:
        E.SubElement(icon, tag).text = value
    E.SubElement(icon, 'texture', {'colordiffuse': '$VAR[InfinityGlassFocus]'}).text = 'infinity_polish/close.png'


def main(apk, out):
    with apk.open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == '08ca19e9ff01e3830253980028dbcdbfb36056fd71b06a18cbfb922158ceaac8'
    out.mkdir(parents=True, exist_ok=True)
    preimages = {}
    changes = {}
    with ZipFile(apk) as z:
        def read(name):
            data = z.read(PREFIX + name)
            preimages[PREFIX + name] = hashlib.sha256(data).hexdigest()
            return data

        def write(name, data, prefix=PREFIX):
            member = prefix + name
            if member in z.namelist():
                old = z.read(member)
                preimages[member] = hashlib.sha256(old).hexdigest()
                if old == data:
                    raise ValueError('Do not stage an unchanged member: ' + member)
            target = out / member
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            changes[member] = {'before': preimages.get(member),
                               'after': hashlib.sha256(data).hexdigest()}

        # Reject window collisions before introducing Videos-only dialog variants.
        for n in z.namelist():
            if n.startswith(PREFIX + 'unified/') and n.endswith('.xml'):
                root = E.fromstring(z.read(n))
                if root.tag == 'window' and root.get('id') in {str(i) for i in NEW_IDS.values()}:
                    raise ValueError('Scoped dialog ID already used: ' + n)

        includes_bytes = read('unified/Includes.xml')
        includes = E.fromstring(includes_bytes)
        scoped = E.Element('includes')
        for old, new in [('MediaMenuTop', 'InfinityVideoMenuTop'),
                         ('SideBladeLeft', 'InfinityVideoSideBladeLeft')]:
            original = includes.find("include[@name='%s']" % old)
            item = E.fromstring(remap(E.tostring(original, encoding='unicode')))
            item.set('name', new)
            if old == 'MediaMenuTop':
                put(item, 'right', '18')
                put(item, 'top', '176')
                for c in item.iter('control'):
                    for n in c.findall('include'):
                        if n.text == 'ButtonCommonValues_PolishMenu':
                            n.text = 'InfinityVideoMenuRow'
                    drop(c, 'textwidth')
            else:
                # Preserve the header X; remove only Videos' redundant collapse target.
                for p in item.iter():
                    for c in list(p):
                        if c.tag == 'control' and (c.get('id') == '9002' or
                            (c.get('type') == 'image' and (c.findtext('texture') or '').endswith('/collapse.png'))):
                            p.remove(c)
                x = item.find(".//control[@id='8999']")
                put(x, 'width', '128'); put(x, 'height', '128'); put(x, 'top', '18')
                parent = next(p for p in item.iter() if x in list(p))
                for c in parent.findall('control'):
                    if c.get('type') == 'label':
                        put(c, 'right', '166'); put(c, 'top', '42'); put(c, 'height', '64')
                    if (c.findtext('texture') or '').endswith('/close.png'):
                        put(c, 'right', '58'); put(c, 'top', '58');put(c, 'width', '48');put(c, 'height', '48')
            scoped.append(item)

        # Local row definitions: do not change globally shared common values.
        common = E.fromstring(read('unified/Includes_CommonValues.xml'))
        legacy = E.fromstring(read('unified/Includes_InfinityLegacy.xml'))
        for root, old, new in [(common, 'ButtonCommonValues_PolishMenu', 'InfinityVideoMenuRow'),
                               (legacy, 'InfinityLegacy_ButtonCommonValues', 'InfinityVideoOptionRow')]:
            item = copy.deepcopy(root.find("include[@name='%s']" % old));item.set('name', new)
            put(item, 'width', '100%');put(item, 'height', '108')
            put(item, 'textwidth', '0');put(item, 'radioposx', '0');put(item, 'wrapmultiline', 'true')
            scoped.append(item)

        settings_includes = E.fromstring(read('unified/Includes_ViewSettings.xml'))
        aliases = {n.get('name'): 'InfinityVideo_' + n.get('name') for n in settings_includes.findall('include')}
        for item in settings_includes.findall('include'):
            item.set('name', aliases[item.get('name')])
            for n in item.iter('include'):
                if n.text == 'InfinityLegacy_ButtonCommonValues':n.text = 'InfinityVideoOptionRow'
                elif n.text in aliases:n.text = aliases[n.text]
            for c in item.iter('control'):
                if c.get('type') in ('button', 'radiobutton'):
                    put(c, 'width', '100%');put(c, 'height', '108');put(c, 'textwidth', '0');put(c, 'radioposx', '0')
                    put(c, 'wrapmultiline', 'true')
            scoped.append(item)

        for old, suffix in [(1130, 'Views'), (1131, 'ViewSettings'), (1132, 'DisableViews')]:
            root = E.fromstring(remap(read('unified/custom_%s_%s.xml' % (old, suffix)).decode()))
            new = NEW_IDS[old];root.set('id', str(new));put(root, 'onback', 'Dialog.Close(%s)' % new)
            controls = root.find('controls')
            # Reuse the complete original content/actions, removing only old X/frame.
            for p in controls.iter():
                for c in list(p):
                    if c.tag == 'control' and c.get('id') == '8999':p.remove(c)
                    elif c.tag == 'include' and c.get('content') == 'InfinityActionLoadingFrame':
                        if any(v.get('name') == 'control' and v.get('value') == '8999' for v in c):p.remove(c)
            group = E.Element('control', {'type': 'group'})
            for tag, value in [('left', '18'), ('top', '18'), ('bottom', '18')]:E.SubElement(group, tag).text = value
            E.SubElement(group, 'width', {'max': '840'}).text = '92%'
            for c in list(controls):controls.remove(c);group.append(c)
            controls.append(group);panel_skin(group)
            content_id = '9000' if old == 1130 else ('9011' if old == 1131 else '9012')
            close_button(group, new, content_id)
            for n in group.iter('include'):
                if n.text in aliases:n.text = aliases[n.text]
                elif n.text == 'InfinityLegacy_ButtonCommonValues':n.text = 'InfinityVideoOptionRow'
            for c in group.iter('control'):
                if c.get('type') == 'label' and c.findtext('font') == 'InfinityBodyBold':
                    put(c, 'left', '24');put(c, 'right', '166');put(c, 'top', '36');put(c, 'height', '96');drop(c, 'width')
                    put(c, 'scroll', 'true')
                if c.get('id') == content_id:
                    put(c, 'left', '18');put(c, 'right', '18');put(c, 'top', '176')
                    put(c, 'bottom', '128' if old == 1130 else '18');drop(c, 'width', 'height')
                    put(c, 'onback', 'Dialog.Close(%s)' % new)
                    put(c, 'onup', '8999')
                if c.get('type') in ('button', 'radiobutton') and c.get('id') != '8999':
                    put(c, 'width', '100%');put(c, 'height', '108');put(c, 'textwidth', '0');put(c, 'radioposx', '0');put(c, 'wrapmultiline', 'true')
            if old == 1130:
                listing = group.find(".//control[@id='9000']")
                for tag in ['itemlayout', 'focusedlayout']:
                    row = listing.find(tag);row.set('height', '108')
                    for label in row.findall("control[@type='label']"):
                        put(label, 'height', '104');put(label, 'aligny', 'center');put(label, 'textoffsetx', '24');put(label, 'scroll', 'true')
                for item in listing.findall('content/item'):
                    action = item.find('onclick')
                    if action is not None and (action.text or '').startswith('Container.SetViewMode('):
                        view = action.text.split('(')[1].rstrip(')')
                        # Explicit user choice is the only global preference writer.
                        save = E.Element('onclick', {'condition': 'Window.IsActive(videos) + [' +
                            ' | '.join('Container.Content(%s)' % c for c in
                            ('movies', 'tvshows', 'seasons', 'episodes', 'sets', 'musicvideos')) + ']'})
                        save.text = 'Skin.SetString(Infinity.MediaView.Default,%s)' % view
                        item.insert(list(item).index(action), save)
                        for text in ['ClearProperty(MediaMenu,Home)', 'Dialog.Close(%s)' % new, 'SetFocus(%s)' % view]:E.SubElement(item, 'onclick').text = text
                config = group.find(".//control[@id='9012']")
                drop(config, 'top');put(config, 'left', '18');put(config, 'right', '18');drop(config, 'width');put(config, 'bottom', '18')
                put(config, 'onup', '9000');put(config, 'ondown', '8999')
            write('unified/custom_%s_InfinityVideo%s.xml' % (new, suffix), xml(root))

        write('unified/Includes_InfinityVideoOptions.xml', xml(scoped))
        anchor = b'</includes>'
        assert includes_bytes.count(anchor) == 1
        write('unified/Includes.xml', includes_bytes.replace(anchor,
              b'  <include file="Includes_InfinityVideoOptions.xml" />\n</includes>'))

        video = read('unified/MyVideoNav.xml').decode()
        for name in ['InfinityPluginDirectoryCompact', 'InfinityPluginDirectoryRegular']:
            pattern = r'(<include condition=")([^"]+)(">' + name + r'</include>)'
            video, count = re.subn(pattern, lambda m: m[1] + m[2] + ' + !Container.Content(movies)' + m[3], video)
            assert count == 1
        for name in ['VideoList', 'SlimVideoList']:
            pattern = r'(<include condition=")([^"]+)(">' + name + r'</include>)'
            video, count = re.subn(pattern, lambda m: m[1] + m[2].replace('String.IsEmpty(Container.PluginName)',
                '[String.IsEmpty(Container.PluginName) | Container.Content(movies)]') + m[3], video)
            assert count == 1
        assert video.count('<include>MediaMenuTop</include>') == 1
        video = video.replace('<include>MediaMenuTop</include>', '<include>InfinityVideoMenuTop</include>')
        assert video.count('<include>SideBladeLeft</include>') == 1
        video = video.replace('<include>SideBladeLeft</include>', '<include>InfinityVideoSideBladeLeft</include>')
        # These row values occur only in this Videos window's View Options.
        video = video.replace('<include>ButtonCommonValues_PolishMenu</include>', '<include>InfinityVideoMenuRow</include>')
        video = video.replace('<textwidth>300</textwidth>', '<textwidth>0</textwidth>')
        # The existing menu is the only 480-wide group in this window.
        assert video.count('<width>480</width>') == 1
        video = video.replace('<width>480</width>', '<width max="840">92%</width>')
        video = video.replace('<right>112</right>\n          <top>112</top>', '<right>18</right>\n          <top>176</top>')
        write('unified/MyVideoNav.xml', video.encode())

        drawer = read('unified/Custom_1198_InfinityNav.xml').decode()
        # Reorder complete existing raw row fragments; all surviving actions,
        # loading contracts, textures and focus styling retain their original bytes.
        root = E.fromstring(drawer)
        gl = root.find(".//control[@id='1198899']")
        row_pattern = re.compile(r'        <control type="group">.*?\n        </control>', re.S)
        matches = list(row_pattern.finditer(drawer))
        assert len(matches) == len(gl.findall('control'))
        rows = [m.group() for m in matches]
        def row_id(raw):
            n = E.fromstring(raw)
            b = n.find("control[@type='button']")
            return b.get('id') if b is not None else None
        by_id = {row_id(raw): raw for raw in rows if row_id(raw)}
        def newrow(new_id, label, action, icon):
            raw = by_id['1198104']
            raw = raw.replace('1198104', str(new_id)).replace('<label>Library</label>', '<label>' + label + '</label>')
            raw = raw.replace('ActivateWindow(Videos)', action)
            # New actions use native destination-local loading. Existing routing
            # notifications on every retained drawer action remain byte-identical.
            raw = re.sub(r'<onclick condition="System.AddonIsEnabled\(script.infinity.commandcenter\)">NotifyAll.*?</onclick>', '', raw, flags=re.S)
            raw = raw.replace('infinity_polish/library.png', icon)
            return raw
        script = 'RunScript(special://skin/resources/lib/infinity_library_navigation.py,%s)'
        nav = [newrow(1198110, 'Sports', script % 'sports', 'infinity_polish/tv.png'),
               by_id['1198301'].replace('<label>Favourites</label>', '<label>Favorites</label>')]
        library = [newrow(1198104, 'Infinity Movies', 'ActivateWindow(Videos,videodb://movies/titles/,return)', 'infinity_polish/movies.png'),
                   newrow(1198111, 'Infinity TV Shows', 'ActivateWindow(Videos,videodb://tvshows/titles/,return)', 'infinity_polish/tv.png'),
                   newrow(1198112, 'Browse Files', script % 'browse', 'infinity_polish/library.png'),
                   newrow(1198113, 'Downloads', script % 'downloads', 'infinity_polish/library.png'),
                   newrow(1198114, 'Media Sources', 'ActivateWindow(Videos,files,return)', 'infinity_polish/library.png')]
        result = []
        for raw in rows:
            key = row_id(raw)
            if key == '1198301':continue
            if key == '1198104':result.extend(library)
            else:result.append(raw)
            if key == '1198103':result.extend(nav)
        drawer = drawer[:matches[0].start()] + '\n'.join(result) + drawer[matches[-1].end():]
        write('unified/Custom_1198_InfinityNav.xml', drawer.encode())
        write('resources/lib/infinity_library_navigation.py', (HERE / 'navigation.py').read_bytes())

        registered = tuple(int(i) for i in E.fromstring(read('unified/MyVideoNav.xml')).findtext('views').split(','))
        rules = {}
        for item in E.fromstring(read('unified/custom_1130_Views.xml')).findall('.//content/item'):
            action = item.findtext('onclick', '')
            if action.startswith('Container.SetViewMode('):
                view = int(action.split('(')[1].rstrip(')'))
                if view in registered:
                    rules.setdefault(view, []).append(tuple(n.text for n in item.findall('visible')))
        helper = (HERE / 'media_view.py').read_text().replace(
            '()  # GENERATED_REGISTRATION', repr(registered)).replace(
            '{}  # GENERATED_RULES', repr(rules))
        write('media_view.py', helper.encode(), CC_PREFIX)
        resident = z.read(CC_PREFIX + 'service.py').decode()
        for before, after in [
            ('    display_reflow = DisplayReflowController()\n',
             '    display_reflow = DisplayReflowController()\n'
             '    from media_view import MediaViewPreference\n'
             '    media_views = MediaViewPreference(xbmc, xbmcgui)\n'),
            ('        loading.tick()\n', '        loading.tick()\n        media_views.tick()\n')]:
            assert resident.count(before) == 1
            resident = resident.replace(before, after)
        write('service.py', resident.encode(), CC_PREFIX)

    (out.parent / 'SOURCE-PLAN.json').write_text(json.dumps({
        'baseline_source': 'cb7c6214807b79661e397cccb0740fc91fab3e24',
        'preimages': preimages, 'changes': changes, 'apk_built': False}, indent=2) + '\n')
    print(json.dumps({'changed_source_members': len(changes), 'apk_built': False}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apk', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args();main(a.apk, a.out)
