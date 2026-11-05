"""Videos-only geometry/artwork correction; no provider, native or state edits."""
from pathlib import Path
import subprocess
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[2]
MEMBER = 'repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Includes_InfinityMediaLists.xml'
BASE = '2b5fcc73a12adcf223858b429d1daa23ed4420ea'
MEDIA = ('movies', 'tvshows', 'seasons', 'episodes', 'sets', 'musicvideos', 'videos')
PREDICATE = ' | '.join('Container.Content(%s)' % c for c in MEDIA)


def set_value(node, tag, text):
    child = node.find(tag)
    if child is None:
        child = E.SubElement(node, tag)
    child.text = text
    return child


def fragment():
    return E.parse(Path(__file__).with_name('browser-elements.xml')).getroot()


def corrected(data):
    root = E.fromstring(data)
    shared = fragment()
    for node in reversed(list(shared)):
        root.insert(0, node)
    for name in ('InfinityMedia_VideoList', 'InfinityMedia_SlimVideoList'):
        include = root.find("include[@name='%s']" % name)
        group = include.find('control')
        for node in list(group):
            if node.tag in ('centerleft', 'left', 'top', 'width', 'height', 'bottom'):
                group.remove(node)
        for k, v in [('left', '1.5%'), ('top', '300'), ('width', '97%'), ('bottom', '144')]:
            set_value(group, k, v)
        left = group.find("control[@type='group']")
        for k, v in [('left', '0'), ('top', '0'), ('width', '61%'), ('height', '100%')]:
            set_value(left, k, v)
        panel = left.find("control[@id='50']")
        for k, v in [('left', '0'), ('top', '0'), ('width', '100%'), ('height', '100%')]:
            set_value(panel, k, v)
        image = left.find("control[@type='image']")
        for k, v in [('left', '0'), ('top', '0'), ('width', '100%'), ('height', '100%')]:
            set_value(image, k, v)
        set_value(image, 'visible', '![%s]' % PREDICATE)
        # Retain all non-media layouts, IDs, actions, native content and filters.
        for child in list(panel):
            if child.tag in ('itemlayout', 'focusedlayout') and child.get('condition') in (
                    'Container.Content(%s)' % c for c in MEDIA):
                panel.remove(child)
        slim = name.endswith('SlimVideoList')
        first_layout = next((i for i, node in enumerate(panel)
                             if node.tag in ('itemlayout', 'focusedlayout')), len(panel))
        for offset, focused in enumerate((False, True)):
            layout = E.Element('focusedlayout' if focused else 'itemlayout',
                               {'condition': PREDICATE, 'width': '100%', 'height': '108' if slim else '124'})
            panel.insert(first_layout + offset, layout)
            row = E.SubElement(layout, 'include', {'content': 'InfinityMedia_BrowserRow'})
            for k, v in [('Focused', str(focused).lower()), ('ArtHeight', '78' if slim else '108'),
                         ('TitleHeight', '44' if slim else '48'), ('MetaTop', '62' if slim else '68')]:
                E.SubElement(row, 'param', {'name': k, 'value': v})
        scrollbar = left.find("control[@type='scrollbar']")
        if scrollbar is not None:
            for k, v in [('left', '99%'), ('top', '0'), ('width', '10'), ('height', '100%')]:
                set_value(scrollbar, k, v)
        # Keep specialist non-media controls; they cannot cover the media panel.
        for right in group.findall("control[@type='group']"):
            if right is left:
                continue
            old = right.findtext('visible') or 'true'
            set_value(right, 'visible', '[%s] + ![%s]' % (old, PREDICATE))
        detail = E.SubElement(group, 'control', {'type': 'group'})
        for k, v in [('left', '0'), ('top', '0'), ('width', '100%'), ('height', '100%'),
                     ('visible', PREDICATE)]:
            set_value(detail, k, v)
        E.SubElement(detail, 'include', {'content': 'InfinityMedia_SelectedMedia'})
        seam = E.SubElement(group, 'control', {'type': 'image'})
        for k, v in [('left','62.5%'),('top','0'),('width','1'),('height','100%')]:
            set_value(seam,k,v)
        texture=E.SubElement(seam,'texture',{'colordiffuse':'$VAR[InfinityPaletteBorder]'})
        texture.text='infinity_ui/contract_white.png'
    # The legacy title bar otherwise paints over the existing VIDEOS header.
    topbar=root.find("include[@name='InfinityMedia_Topbar']/control")
    E.SubElement(topbar,'visible').text='![Control.IsVisible(50) + [%s]]'%PREDICATE
    return root


def main():
    raw = subprocess.run(['git', 'show', BASE + ':' + MEMBER], cwd=ROOT,
                         capture_output=True, check=True).stdout
    root = corrected(raw)
    E.indent(root, space='  ')
    (ROOT / MEMBER).write_bytes(E.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n')


if __name__ == '__main__':
    main()
