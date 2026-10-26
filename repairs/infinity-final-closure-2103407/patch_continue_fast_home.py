"""Exact signed416->417 Continue Watching and duplicate Home-start correction."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).parent
CC='script.infinity.commandcenter'
SKIN='skin.infinity.diggz'
PREFIX='assets/addons/'
PLAN='CONTINUE-FAST-HOME-417-PLAN.json'


def digest(raw):return hashlib.sha256(raw).hexdigest()


def require_preimage(name,raw):
    if digest(raw)!=json.loads((ROOT/PLAN).read_text())['source_preimages'].get(PREFIX+name):
        raise ValueError('Exact signed416 source required: '+name)


def edits(name):
    if name=='addon.xml':return [('version="0.3.5.46"','version="0.3.5.47"')]
    if name=='service.py':
        epoch=(ROOT/'home_observer_epoch.py').read_text().rstrip()+'\n\n\n'
        original="""                    result['verified_next'] = {'verified': True, 'after': [season, episode],
                                               'show_tmdb': result['show_tmdb'],
                                               'season': following[0][0], 'episode': following[0][1]}
"""
        revised=original+"""                    matching = [row for row in catalogue if isinstance(row, dict) and
                                (hub.episode_number(row.get('season')), hub.episode_number(row.get('episode'))) == following[0]]
                    if len(matching) == 1:
                        row = matching[0]
                        source = row.get('file')
                        from experience import stable_route
                        if (type(row.get('episodeid')) is int and row['episodeid'] > 0 and
                                stable_route(source) and not source.lower().startswith('plugin://')):
                            result['verified_next']['library'] = {
                                'episodeid': row['episodeid'], 'tvshowid': show_id, 'file': source,
                                'show_tmdb': result['show_tmdb'], 'season': following[0][0],
                                'episode': following[0][1]}
"""
        return [
            ("'tvshowid': show_id, 'properties': ['season', 'episode'],","'tvshowid': show_id, 'properties': ['season', 'episode', 'file'],"),
            (original,revised),
            ('_home_runtime_sync_after = 0.0\n',epoch+'_home_runtime_sync_after = 0.0\n'),
            ('        _consume_home_runtime_sync(now)\n','        _consume_home_observer_epoch()\n        _consume_home_runtime_sync(now)\n')]
    if name=='resume_hub.py':return [
        ("        'watched_at': _now(),\n", "        'watched_at': _now(),\n        'resume_revision': int(data.get('revision') or 0) + 1,\n"),
        ("""    if value.get('show_ids_verified') is True:
        for namespace in ('tmdb', 'tvdb'):
            verified = str(value.get('show_' + namespace) or '')
            if verified.isdigit() and int(verified) > 0:
                return 'series:' + namespace + ':' + verified
""",
         """    series = continue_series_ids(value)
    for namespace in ('tmdb', 'tvdb'):
        if series.get(namespace):
            return 'series:' + namespace + ':' + series[namespace]
"""),
        ("""            marker = (priority, episode_number(value.get('season')), episode_number(value.get('episode')),
                      int(value.get('updated') or value.get('watched_at') or 0))
""",
         """            marker = (priority, int(value.get('updated') or value.get('watched_at') or 0),
                      int(value.get('resume_revision') or 0),
                      episode_number(value.get('season')), episode_number(value.get('episode')))
"""),
        ("            marker = (episode_number(value.get('season')), episode_number(value.get('episode')), int(value.get('updated') or 0))\n",
         "            marker = (int(value.get('updated') or 0), int(value.get('resume_revision') or 0),\n                      episode_number(value.get('season')), episode_number(value.get('episode')))\n"),
        ("        marker = (season, episode, int(value.get('watched_at') or value.get('updated') or 0))\n",
         "        marker = (int(value.get('watched_at') or value.get('updated') or 0),\n                  int(value.get('resume_revision') or 0), season, episode)\n"),
        ("successor.get('after') != [marker[0], marker[1]]", "successor.get('after') != [episode_number(last.get('season')), episode_number(last.get('episode'))]"),
        ("        candidate['label'] = f\"{show} • S{candidate['season']:02d}E{candidate['episode']:02d}\"\n",
         "        if isinstance(successor.get('library'), dict):\n            candidate['library_next'] = deepcopy(successor['library'])\n        candidate['label'] = f\"{show} • S{candidate['season']:02d}E{candidate['episode']:02d}\"\n")]
    if name=='plugin.py':
        resolver=(ROOT/'local_next_resolver.py').read_text().rstrip()+'\n\n\n'
        return [
            ('def _target(entry, sources=None, render=None):',resolver+'def _target(entry, sources=None, render=None):'),
            ("    media = entry.get('media')\n    if (hub.entry_identity(entry) or {}).get('kind') in ('tvshow', 'season'):",
             "    if _local_next_proof(entry) is not None:\n        return _url(action='play-local-next', key=entry['key'])\n    media = entry.get('media')\n    if (hub.entry_identity(entry) or {}).get('kind') in ('tvshow', 'season'):"),
            ("    action = PARAMS.get('action', 'continue')\n",
             "    action = PARAMS.get('action', 'continue')\n    if action == 'play-local-next':\n        if not play_local_next(PARAMS.get('key', '')):\n            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())\n        return\n")]
    raise ValueError('Unowned Continue/Home source')


def patch(name,raw):
    require_preimage(CC+'/'+name,raw);text=raw.decode();result=text;pairs=edits(name)
    for old,new in pairs:
        if result.count(old)!=1:raise ValueError('Continue/Home source boundary differs: '+name)
        result=result.replace(old,new,1)
    inverse=result
    for old,new in reversed(pairs):
        if inverse.count(new)!=1:raise ValueError('Continue/Home inverse differs: '+name)
        inverse=inverse.replace(new,old,1)
    if inverse!=text:raise ValueError('Unrelated Continue/Home source changed')
    if name.endswith('.py'):compile(result,name,'exec',dont_inherit=True)
    return result.encode()


def home_edits():
    pairs=[]
    for leaf,flag,value,pending in [('infinity_continuity.py','Infinity.Continuity.Observer','active','Continuity'),
                            ('infinity_native_ambient.py','Infinity.NativeAmbient.WriterLifecycle','running-optional','Ambient')]:
        old='<onload>RunScript(special://skin/resources/lib/'+leaf+')</onload>'
        new='<onload condition="!System.AddonIsEnabled(script.infinity.commandcenter) | !String.IsEqual(Window(Home).Property('+flag+'),'+value+')">RunScript(special://skin/resources/lib/'+leaf+')</onload>'
        new+='\n  <onload condition="System.AddonIsEnabled(script.infinity.commandcenter)">SetProperty(Infinity.Home.'+pending+'.Pending,true,Home)</onload>'
        pairs.append((old,new))
    return pairs


def skin_sources(before):
    result=dict(before);homes=[n for n in before if n.endswith('/Home.xml')]
    if len(homes)!=14:raise ValueError('All14 exact Home profiles required')
    for name in homes:
        require_preimage(SKIN+'/'+name,before[name]);text=before[name].decode();updated=text
        for old,new in home_edits():
            if 'infinity_continuity.py' in old and updated.count(old)==0:
                continue  # Do not add a continuity observer to a profile lacking it.
            if updated.count(old)!=1:raise ValueError('Home helper boundary differs: '+name)
            updated=updated.replace(old,new,1)
        inverse=updated
        for old,new in reversed(home_edits()):inverse=inverse.replace(new,old,1)
        if inverse!=text:raise ValueError('Unrelated Home XML changed')
        ET.fromstring(updated);result[name]=updated.encode()
    name='addon.xml';require_preimage(SKIN+'/'+name,before[name]);text=before[name].decode()
    for old,new in [('version="1.0.5.244"','version="1.0.5.245"'),
                    ('<import addon="script.infinity.commandcenter" version="0.3.5.43" />',
                     '<import addon="script.infinity.commandcenter" version="0.3.5.47" />')]:
        if text.count(old)!=1:raise ValueError('Skin dependency/version differs')
        text=text.replace(old,new,1)
    result[name]=text.encode()
    name='infinity-skin.json';require_preimage(SKIN+'/'+name,before[name]);meta=json.loads(before[name])
    meta.update(version='1.0.5.245',skin_version='1.0.5.245',candidate=245,candidate_locked=False,
                physical_device_verified=False,candidate_name='Infinity corrective verification candidate')
    result[name]=(json.dumps(meta,indent=2,sort_keys=True)+'\n').encode()
    name='Infinity-Protected-Manifest.json';require_preimage(SKIN+'/'+name,before[name]);protected=json.loads(before[name])
    if name in protected['protected_files'] or len(protected['protected_files'])!=942:
        raise ValueError('Exact non-self-referential protected inventory required')
    for member,pin in protected['protected_files'].items():
        if member not in before or digest(before[member])!=pin:raise ValueError('Signed parent protected pin differs')
        protected['protected_files'][member]=digest(result[member])
    protected.update(skin_version='1.0.5.245',candidate_version='1.0.5.245',candidate=245,candidate_locked=False)
    result[name]=(json.dumps(protected,indent=2,sort_keys=True)+'\n').encode()
    for leaf,pin in json.loads((ROOT/PLAN).read_text())['unchanged_helper_sha256'].items():
        if digest(result['resources/lib/'+leaf])!=pin:raise ValueError('Original helper changed')
    changed={n for n in result if result[n]!=before[n]}
    if changed!=set(homes)|{'addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json'}:
        raise ValueError('Unowned skin edit')
    return result,dict(changed_members=sorted(changed),preserved_members=len(before)-len(changed),
        all942parent_pins_verified=True,onload_commands_only=True,layouts_geometry_player_resources_unchanged=True,
        all_original_helper_sources_byte_identical=True)
