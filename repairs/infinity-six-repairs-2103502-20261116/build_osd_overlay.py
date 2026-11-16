"""Apply only the approved inner-icon dimensions to authenticated 502 XML."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from xml.parsers import expat
import zipfile

MEMBER = 'assets/addons/skin.infinity.diggz/unified/VideoOSD.xml'
PREIMAGE = '4c9adac29735c6e53d5647d3381415cc696b39c6a69ec358654500c74ff46af1'
EXPECTED = [257, 6121, 6121, 264, 200, 202, 202, 205, 253, 250, 255, 263, 263, 262]
OLD = {'left': '28', 'top': '28', 'width': '40', 'height': '40'}
NEW = {'left': '16', 'top': '16', 'width': '64', 'height': '64'}


def nodes(data):
    parser = expat.ParserCreate()
    stack, roots = [], []

    def start(tag, attrs):
        node = {'tag': tag, 'attrs': attrs, 'start': parser.CurrentByteIndex, 'children': []}
        (stack[-1]['children'] if stack else roots).append(node)
        stack.append(node)

    def end(tag):
        node = stack.pop()
        # Only nonempty coordinate elements are sliced; retain the entire source elsewhere.
        node['end'] = data.find(b'>', parser.CurrentByteIndex) + 1

    parser.StartElementHandler, parser.EndElementHandler = start, end
    parser.Parse(data, True)
    return roots


def enlarged(data):
    if hashlib.sha256(data).hexdigest() != PREIMAGE:
        raise ValueError('VideoOSD is not the authenticated 502 preimage')
    replacements, slots = [], []

    def walk(node):
        children = node['children']
        buttons = [c for c in children if c['tag'] == 'control' and c['attrs'].get('type') == 'button']
        if node['tag'] == 'control' and node['attrs'].get('type') == 'group' and len(buttons) == 1:
            button = buttons[0]
            button_id = int(button['attrs'].get('id', '-1'))
            if button_id in EXPECTED:
                images = [c for c in children if c['tag'] == 'control' and c['attrs'].get('type') == 'image']
                for image in images:
                    coords = {c['tag']: c for c in image['children'] if c['tag'] in OLD}
                    if set(coords) != set(OLD):
                        raise ValueError('Unexpected inner-image coordinates')
                    for tag, old in OLD.items():
                        coord = coords[tag]
                        raw = data[coord['start']:coord['end']]
                        match = re.fullmatch(rb'<' + tag.encode() + rb'>(\s*)' + old.encode() + rb'(\s*)</' + tag.encode() + rb'>', raw)
                        if not match:
                            raise ValueError('Unexpected image dimension')
                        new = b'<' + tag.encode() + b'>' + match[1] + NEW[tag].encode() + match[2] + b'</' + tag.encode() + b'>'
                        replacements.append((coord['start'], coord['end'], raw, new))
                    slots.append(button_id)
        for child in children:
            walk(child)

    for root in nodes(data):
        walk(root)
    if slots != EXPECTED or len(replacements) != 56:
        raise ValueError('Unexpected icon slot list')
    result = data
    for start, end, old, new in sorted(replacements, reverse=True):
        if result[start:end] != old:
            raise ValueError('Overlapping source edits')
        result = result[:start] + new + result[end:]
    ET.fromstring(result)
    return result, slots


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    with zipfile.ZipFile(args.apk) as archive:
        candidate, slots = enlarged(archive.read(MEMBER))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    print(json.dumps({'member': MEMBER, 'before_sha256': PREIMAGE,
                      'after_sha256': hashlib.sha256(candidate).hexdigest(), 'image_slots': slots}))


if __name__ == '__main__':
    main()
