"""Retain saved history while projecting actual completion and exact next-up."""
import hashlib
import json
from pathlib import Path

CC='script.infinity.commandcenter'
ROOT=Path(__file__).parent


def substitutions(name):
    if name=='addon.xml':return [('version="0.3.5.45"','version="0.3.5.46"')]
    if name=='service.py':return [
        ('        information = capture(player)\n',
         "        information = capture(player)\n        if information.get('premiered') == '1601-01-01':\n            information.pop('premiered')  # Native zero date is missing metadata.\n")]
    if name=='resume_hub.py':return [
        ("    fields = ('position', 'duration', 'percentage', 'updated', 'playback_occurrence', 'resume_revision')\n",
         """    fields = ('position', 'duration', 'percentage', 'updated', 'playback_occurrence', 'resume_revision')
    # Preserve new native/library parent and successor proof in existing rows,
    # alongside their progress. Saved identity, provider routes and keys stay
    # intact. No title match or guessed episode increment grants a successor.
    if not old:
        result.pop('verified_next', None)
    series = continue_series_ids(entry)
    if series and entry.get('show_ids_verified') is True:
        fields += ('show_ids_verified',)
        fields += tuple('show_' + name for name in ('tmdb', 'tvdb')
                        if series.get(name) and entry.get('show_' + name) == series[name])
        successor = _dict(entry.get('verified_next'))
        current = (episode_number(entry.get('season')), episode_number(entry.get('episode')))
        following = (episode_number(successor.get('season')), episode_number(successor.get('episode')))
        if (successor.get('verified') is True and successor.get('after') == list(current) and
                series.get('tmdb') and successor.get('show_tmdb') == series['tmdb'] and
                min(current) >= 0 and min(following) >= 0 and following > current and
                ((current[0] == 0 and following[0] == 0) or (current[0] > 0 and following[0] > 0))):
            entry = dict(entry, verified_next=deepcopy(successor))
            fields += ('verified_next',)
"""),
        ("""    for bucket, priority in (('watched', 0), ('items', 1)):
        for key, value in data[bucket].items():
            if not isinstance(value, dict) or value.get('media') != 'tv':
                continue
""",
         """    for bucket, priority in (('watched', 0), ('items', 1)):
        for key, value in data[bucket].items():
            if (not isinstance(value, dict) or value.get('media') != 'tv' or
                    (bucket == 'items' and not resume_visible(data, key))):
                continue
"""),
        ("""    progress = {}
    for key, value in data['items'].items():
        if isinstance(value, dict) and value.get('media') == 'tv':
""",
         """    progress = {}
    for key, value in data['items'].items():
        if isinstance(value, dict) and value.get('media') == 'tv' and resume_visible(data, key):
""")]
    raise ValueError('Unowned Continue completion source')


def patch(name,raw):
    pins=json.loads((ROOT/'CONTINUE-COMPLETION-416-PLAN.json').read_text())['source_preimages']
    if hashlib.sha256(raw).hexdigest()!=pins.get(name):raise ValueError('Exact signed415 source required')
    text=raw.decode();result=text;pairs=substitutions(name)
    for old,new in pairs:
        if result.count(old)!=1:raise ValueError('Continue completion source boundary differs')
        result=result.replace(old,new,1)
    inverse=result
    for old,new in reversed(pairs):
        if inverse.count(new)!=1:raise ValueError('Continue completion inverse differs')
        inverse=inverse.replace(new,old,1)
    if inverse!=text:raise ValueError('Unrelated Continue source changed')
    if name.endswith('.py'):compile(result,name,'exec',dont_inherit=True)
    return result.encode()
