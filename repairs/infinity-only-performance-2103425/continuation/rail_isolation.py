"""Generate source-owned Home rails without changing native list providers.

A control/provider instance belongs permanently to source, media, row and view.
Its in-flight callback can never publish into another source's control. Kodi's
existing per-control job cancellation, revision URLs and selection retention
remain responsible for updates within that one owner. No timers or new workers.
"""
from copy import deepcopy
import re
from lxml import etree as ET

OFFSET = 20000
# Same geometry/view, different stable control identity and provider instance.
RAILS = {8103: ('tv', 'primary'), 8104: ('movie', 'primary'),
         8603: ('tv', 'primary'), 8604: ('movie', 'primary'),
         8703: ('tv', 'primary'), 8704: ('movie', 'primary'),
         8721: ('tv', 'secondary'), 8722: ('movie', 'secondary'),
         8803: ('tv', 'primary'), 8804: ('movie', 'primary'),
         8821: ('tv', 'secondary'), 8822: ('movie', 'secondary'),
         9201: ('tv', 'secondary'), 9202: ('movie', 'secondary')}
OWNER = 'String.IsEqual(Container(9000).ListItem.Property(hubsource),{})'


def parse(raw):
    return ET.fromstring(raw, ET.XMLParser(remove_blank_text=False))


def serialize(root):
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'


def remap(text):
    return re.sub(r'(?<!\d)(' + '|'.join(map(str, RAILS)) + r')(?!\d)',
                  lambda m: str(int(m[0]) + OFFSET), text)


def own(control, source):
    visible = control.find('visible')
    if visible is None:
        visible = ET.SubElement(control, 'visible')
        visible.text = OWNER.format(source)
    else:
        visible.text = '[' + visible.text + '] + [' + OWNER.format(source) + ']'


def map_tree(control):
    for element in control.iter():
        if element.text: element.text = remap(element.text)
        for key in tuple(element.attrib):
            element.set(key, remap(element.get(key)))


def home(raw):
    root = parse(raw)
    existing = {int(c.get('id')) for c in root.iter('control') if c.get('id', '').isdigit()}
    assert not existing.intersection({n + OFFSET for n in RAILS}), 'Control ID collision'
    owned, dependent = [], []
    for c in list(root.iter('control')):
        if c.get('id', '').isdigit() and int(c.get('id')) in RAILS:
            owned.append(c)
        elif not c.findall('control') and any(
                re.search(r'Container\((' + '|'.join(map(str, RAILS)) + r')\)\.ListItem', t)
                for t in c.itertext()):
            dependent.append(c)
    # Dependent fanart/title/year/plot surfaces need the same owner as their card.
    for c in owned + dependent:
        clone = deepcopy(c)
        map_tree(clone)
        if c in dependent and c.get('id'):
            new_id = int(c.get('id')) + OFFSET
            assert new_id not in existing
            clone.set('id', str(new_id)); existing.add(new_id)
        own(c, 'trakt'); own(clone, 'infinity')
        c.addnext(clone)
    protected = {e for c in owned + dependent for e in c.iter()}
    # Both copies already contain all their internal, source-specific navigation.
    protected.update(e for c in owned + dependent for e in c.getnext().iter())
    for element in list(root.iter()):
        if element in protected: continue
        text = element.text or ''
        if element.tag.startswith('on') and (text.isdigit() and int(text) in RAILS or
                re.search(r'SendClick\((' + '|'.join(map(str, RAILS)) + r')\)', text)):
            clone = deepcopy(element)
            map_tree(clone)
            condition = element.get('condition')
            for target, source in ((element, 'trakt'), (clone, 'infinity')):
                target.set('condition', ('[' + condition + '] + ' if condition else '') +
                           '[' + OWNER.format(source) + ']')
            element.addnext(clone)
        else:
            # Navigation/visibility which checks focus must accept the matching
            # source's retained control as well; no hidden Trakt panel receives it.
            for key in tuple(element.attrib):
                element.set(key, expand_focus(element.get(key)))
            if element.text: element.text = expand_focus(element.text)
    return serialize(root)


def expand_focus(text):
    return re.sub(r'Control.HasFocus\((' + '|'.join(map(str, RAILS)) + r')\)',
                  lambda m: '[' + m[0] + ' | Control.HasFocus(' + str(int(m[1]) + OFFSET) + ')]', text)


def includes(raw):
    root = parse(raw)
    paths = {v.get('name'): v for v in root.findall('variable')}
    for ident, (media, row) in RAILS.items():
        key = 'InfinityP0HomeFeed' + str(ident)
        if key not in paths: continue
        original = paths[key]
        clone = deepcopy(original)
        clone.set('name', key.replace(str(ident), str(ident + OFFSET)))
        for v in clone.findall('value'):
            if v.get('condition'): v.set('condition', remap(v.get('condition')))
        route = paths['Infinity' + ('TV' if media == 'tv' else 'Movies') +
                      ('PrimaryPath' if row == 'primary' else 'SecondaryPath')]
        # Unconditional source URLs: never read the currently selected source
        # to decide where an already instantiated rail fetches its contents.
        original.find('value').text = route.findall('value')[1].text
        clone.find('value').text = route.findall('value')[0].text + '&home=1'
        original.addnext(clone)
    return serialize(root)
