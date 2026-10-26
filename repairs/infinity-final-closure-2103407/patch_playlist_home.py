"""Exact signed418 Home: avoid a Python invocation for an absent optional provider."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).parent
SKIN='skin.infinity.diggz'
CC='script.infinity.commandcenter'
PLAN='PLAYLIST-HOME-419-PLAN.json'
PREFIX='assets/addons/'+SKIN+'/'
PROVIDER='plugin.video.playlistbrowser'
OLD='<onload>RunScript(special://skin/resources/lib/infinity_playlist_routes.py)</onload>'
PRESENT='System.HasAddon('+PROVIDER+')'
# These are exactly the original helper\'s absent-provider output. Ready is last.
ABSENT_ACTIONS=[
    'ClearProperty(Infinity.Playlist.Request,Home)',
    'ClearProperty(Infinity.Playlist.TVPath,Home)',
    'ClearProperty(Infinity.Playlist.SportsPath,Home)',
    'SetProperty(Infinity.Playlist.TVBrowse,addons://sources/video/,Home)',
    'SetProperty(Infinity.Playlist.SportsBrowse,addons://sources/video/,Home)',
    'SetProperty(Infinity.Playlist.Status,unavailable,Home)',
    'SetProperty(Infinity.Playlist.Version,unavailable,Home)',
    'SetProperty(Infinity.Playlist.Ready,v1,Home)',
]
NEW=('<onload condition="'+PRESENT+'">RunScript(special://skin/resources/lib/infinity_playlist_routes.py)</onload>'+\
    ''.join('\n  <onload condition="!'+PRESENT+'">'+action+'</onload>' for action in ABSENT_ACTIONS))


def digest(raw):return hashlib.sha256(raw).hexdigest()


def pinned(name,raw):
    if digest(raw)!=json.loads((ROOT/PLAN).read_text())['source_preimages'].get(PREFIX+name):
        raise ValueError('Exact signed418 skin source required: '+name)


def skin_sources(before):
    for name,pin in json.loads((ROOT/PLAN).read_text())['unchanged_helper_sha256'].items():
        if name not in before or digest(before[name])!=pin:raise ValueError('Original playlist helper changed')
    result=dict(before);homes=[n for n in before if n.endswith('/Home.xml')]
    if len(homes)!=14:raise ValueError('All14 exact Home profiles required')
    for name in homes:
        pinned(name,before[name]);text=before[name].decode()
        if text.count(OLD)!=1:raise ValueError('Original playlist onload required')
        updated=text.replace(OLD,NEW,1)
        if updated.replace(NEW,OLD,1)!=text:raise ValueError('Unrelated Home delta')
        ET.fromstring(updated);result[name]=updated.encode()
    name='addon.xml';pinned(name,before[name]);text=before[name].decode()
    if text.count('version="1.0.5.245"')!=1:raise ValueError('Exact parent skin version required')
    result[name]=text.replace('version="1.0.5.245"','version="1.0.5.246"',1).encode()
    name='infinity-skin.json';pinned(name,before[name]);meta=json.loads(before[name])
    meta.update(version='1.0.5.246',skin_version='1.0.5.246',candidate=246,candidate_locked=False,
                physical_device_verified=False,candidate_name='Infinity corrective verification candidate')
    result[name]=(json.dumps(meta,indent=2,sort_keys=True)+'\n').encode()
    name='Infinity-Protected-Manifest.json';pinned(name,before[name]);protected=json.loads(before[name])
    if name in protected['protected_files'] or len(protected['protected_files'])!=942:
        raise ValueError('Exact non-self-referential protected inventory required')
    for member,pin in protected['protected_files'].items():
        if member not in before or digest(before[member])!=pin:raise ValueError('Signed parent protected pin differs')
        protected['protected_files'][member]=digest(result[member])
    protected.update(skin_version='1.0.5.246',candidate_version='1.0.5.246',candidate=246,candidate_locked=False)
    result[name]=(json.dumps(protected,indent=2,sort_keys=True)+'\n').encode()
    changed={n for n in result if result[n]!=before[n]}
    if changed!=set(homes)|{'addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json'}:
        raise ValueError('Unowned skin edit')
    return result,dict(changed_members=sorted(changed),preserved_members=len(before)-len(changed),
        all942parent_pins_verified=True,onload_commands_only=True,layouts_geometry_player_resources_unchanged=True,
        all_original_helper_sources_byte_identical=True,all_first_party_modules_byte_identical=True)
