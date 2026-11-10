"""Read-only SurfaceFlinger identity parsing; never substitute another layer."""
import re

COMPONENT = 'com.projectinfinity.kodi/com.projectinfinity.kodi.Main'
PATTERN = re.compile(
    r'^(?P<name>(?!Background for )[^{}\n]*SurfaceView\[' + re.escape(COMPONENT) +
    r'\]\(BLAST\)#(?P<id>[0-9]+))(?P<meta>(?: (?:parentId|relativeParentId|z)=-?[0-9]+| !handle)*)$')


def candidates(text):
    found = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('RequestedLayerState{'):
            if not line.endswith('}'):
                continue
            line = line[len('RequestedLayerState{'):-1]
        match = PATTERN.fullmatch(line)
        if not match:
            continue
        name, number = match['name'], int(match['id'])
        parent = re.search(r'(?:^| )parentId=(-?[0-9]+)(?: |$)', match['meta'])
        value = dict(name=name, id=number, parent=int(parent[1]) if parent else None)
        found[(name, number, value['parent'])] = value
    return list(found.values())


def corroborate(text, layer, pid):
    header = re.compile(r'^\s*Layer \[' + str(layer['id']) + r'\] ' + re.escape(layer['name']) + r'\s*$')
    lines = text.splitlines()
    visible = False
    for index, line in enumerate(lines):
        if header.fullmatch(line):
            for detail in lines[index+1:index+12]:
                if re.match(r'^\s*Layer \[', detail):
                    break
                if re.search(r'^\s*visible reason= buffer=[1-9][0-9]*\b', detail):
                    visible = True
    owners = set(re.findall(r'\(BLAST\)#' + str(layer['id']) + r' pid=([0-9]+) uid=[0-9]+\b', text))
    return dict(visible_buffer_observed=visible, owner_pids=sorted(owners),
                owner_matches=owners == {str(pid)}, confirmed=visible and owners == {str(pid)})
