#!/usr/bin/env python3
"""Infinity 2103404: source-exact WatchNixtoons2 local tracking + version contracts.

Reads immutable 2103403 signed component files. Changes are deliberately
limited: context.py, resume_hub.py, infinity_trakt.py, checkpoint_runtime.py,
and Watched Bridge controller.py. No provider, Cobra, or Search source altered.
"""
from pathlib import Path
import hashlib, sys

ORIGINAL = {
    'context.py': 'aec101d4c9ba7b38eb7b98876fd91fa5042b70f17ae0ca33d4832df6cb73e14f',
    'resume_hub.py': 'd1ee9efe3aa7d59132e63d9a1cd726e579a14ef53b671a5d2aa0204dea7d5155',
}

def exactly(s,a,b):
    n=s.count(a)
    if n!=1:raise AssertionError((a[:100],n))
    return s.replace(a,b,1)

SOURCE_FUNCTION='''def watchnixtoons_source_identity(route, kind, season=-1, episode=-1):
    """A local-only identity from an exact WNT2 source URL, never a TMDb/Trakt ID.

    The add-on's actionEpisodesMenu and actionResolve URLs carry a concrete web
    page location. Name, artwork, search position and query are NOT identities.
    Fail closed when no exact URL is available; do not browse provider pages.
    """
    from urllib.parse import parse_qs, urlsplit
    if (not isinstance(route, str) or len(route) > 8192 or
            any(ord(ch) < 32 for ch in route) or '\\\\' in route):
        return None
    parsed = urlsplit(route)
    if (parsed.scheme != 'plugin' or parsed.netloc != 'plugin.video.watchnixtoons2' or
            parsed.path not in ('','/') or parsed.fragment):
        return None
    parts = parse_qs(parsed.query, keep_blank_values=True, max_num_fields=30)
    if len(parts.get('action', [])) != 1 or len(parts.get('url', [])) != 1:
        return None
    action, source_url = parts['action'][0], parts['url'][0]
    allowed = {'actionEpisodesMenu': ('tvshow', 'season'),
               'actionResolve': ('movie', 'episode')}
    if kind not in allowed.get(action, ()):
        return None
    if (not source_url or len(source_url) > 4096 or
            any(ord(ch) < 32 for ch in source_url) or '\\\\' in source_url):
        return None
    try:
        site = urlsplit(source_url)
        port = site.port
    except ValueError:
        return None
    if site.scheme:
        if (site.scheme not in ('https','http') or not site.hostname or site.username or
                site.password or site.fragment or port not in (None,80,443)):
            return None
        # Keep host and page location exact; never follow a link or merge domains.
    elif (not source_url.startswith('/') or source_url.startswith('//') or
          '?' in source_url or '#' in source_url):
        return None
    sn=episode_number(season) if kind in ('season','episode') else -1
    en=episode_number(episode) if kind=='episode' else -1
    if kind=='season' and sn<0:
        return None
    # Some Nixtoons standalone episodes lack a season number. Their unique
    # original episode page is still an exact, local-only source identity.
    token = hashlib.sha256(('wnt2-source-v1\\0'+action+'\\0'+source_url+'\\0'+
        kind+'\\0'+str(sn)+'\\0'+str(en)).encode('utf-8')).hexdigest()
    value = {'schema': 1, 'kind': kind, 'scope': 'watchnixtoons_local',
             'ids': {'wnt2': token}}
    if kind in ('season','episode'):
        value['season']=sn
    if kind=='episode':
        value['episode']=en
    return value


'''

HUB_VALIDATION='''    if value.get('scope') == 'watchnixtoons_local':
        kind = value.get('kind')
        if (kind not in ('movie','tvshow','season','episode') or
                media not in ('tv','movie') or
                (media == 'movie') != (kind == 'movie') or
                entry.get('source') != entry.get('stable_source')):
            return None
        rebuilt = watchnixtoons_source_identity(entry.get('source'), kind,
                entry.get('season'), entry.get('episode'))
        # The persisted source location must independently reproduce the ID.
        return rebuilt if rebuilt == value else None
'''

CONTEXT_PROVIDER='''def _watchnixtoons_source_entry(item, route, kind, title):
    """Direct local-only tracking from the selected, exact Nixtoons page URL.

    Never present a source digest as a TMDb/IMDb/TVDb ID or silently sync Trakt.
    The original plugin route remains the only playback/navigation destination.
    """
    tag = item.getVideoInfoTag()
    identity = hub.watchnixtoons_source_identity(route, kind, tag.getSeason(), tag.getEpisode())
    key = hub.identity_key(identity)
    if not key or item.getPath() != route or tag.getMediaType() != kind:
        return None
    return dict(key=key, identity=identity, media='movie' if kind=='movie' else 'tv',
                title=title, label=item.getLabel(), source=route, stable_source=route,
                season=hub.episode_number(tag.getSeason()) if kind in ('season','episode') else -1,
                episode=hub.episode_number(tag.getEpisode()) if kind=='episode' else -1,
                dbid=-1, poster=item.getArt('poster') or item.getArt('thumb'),
                fanart=item.getArt('fanart'), _native_watched=tag.getPlayCount()>0)


'''

def patch_hub(src):
    src=exactly(src, 'def entry_identity(entry):\n',SOURCE_FUNCTION+'def entry_identity(entry):\n')
    src=exactly(src, "    media = _dict(entry).get('media')\n", "    media = _dict(entry).get('media')\n" + HUB_VALIDATION)
    src=exactly(src, '''    ids = verified_ids(identity.get('ids'))
    for namespace in ('tmdb', 'imdb', 'tvdb'):
''', '''    if identity.get('scope') == 'watchnixtoons_local':
        ids = identity.get('ids')
        if (identity.get('kind') in ('tvshow','season','episode','movie') and
                isinstance(ids,dict) and len(ids)==1 and
                isinstance(ids.get('wnt2'),str) and
                re.fullmatch(r'[a-f0-9]{64}',ids['wnt2'])):
            return hashlib.sha256(('wnt2-local-key-v1|'+identity['kind']+'|'+ids['wnt2']).encode('ascii')).hexdigest()
        return ''
    ids = verified_ids(identity.get('ids'))
    for namespace in ('tmdb', 'imdb', 'tvdb'):
''')
    src=exactly(src, '''    if left['kind'] == 'episode' and (left['season'], left['episode']) != (right['season'], right['episode']):
''', '''    if left['scope'] == 'watchnixtoons_local':
        return (left.get('ids') == right.get('ids') and
                set(left.get('ids') or {}) == {'wnt2'} and
                bool(re.fullmatch(r'[a-f0-9]{64}',left['ids']['wnt2'])))
    if left['kind'] == 'episode' and (left['season'], left['episode']) != (right['season'], right['episode']):
''')
    compile(src,'resume_hub.py','exec')
    return src

def patch_context(src):
    src=exactly(src,'def _watchnixtoons_tracking(item,route,kind,title,label,op):\n',CONTEXT_PROVIDER+'def _watchnixtoons_tracking(item,route,kind,title,label,op):\n')
    old='''    if entry is None:entry=_watchnixtoons_confirmed_entry(item,route,kind,title)
    if entry is None:return False
'''
    new='''    if entry is None:entry=_watchnixtoons_source_entry(item,route,kind,title)
    if entry is None:
        # Refuse to guess when this provider does not expose a source URL.
        xbmcgui.Dialog().ok('Infinity Tracked','This item has no verifiable WatchNixtoons2 source location. Nothing was changed.')
        return False
'''
    src=exactly(src,old,new)
    src=exactly(src, '''    return _popup_module().show_item_menu(entry['key'],bucket='',incoming=entry,
                                         nixtoons_confirmed_row=(label,op,''))
''', '''    completed = _popup_module().show_item_menu(entry['key'],bucket='',incoming=entry,
                                         nixtoons_confirmed_row=(label,op,''))
    if completed and (hub.entry_identity(entry) or {}).get('scope') == 'watchnixtoons_local':
        # Trakt and third-party provider databases are not modified by local actions.
        try:
            xbmcgui.Dialog().notification('Infinity Tracked', 'Saved in Infinity locally • Trakt not synced', xbmcgui.NOTIFICATION_INFO, 2600)
        except Exception:
            pass
    return completed
''')
    compile(src,'context.py','exec')
    return src


def main():
    target=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    for name, wanted in ORIGINAL.items():
        src=(target/name).read_text(encoding='utf-8')
        assert hashlib.sha256(src.encode()).hexdigest()==wanted,('Unexpected signed parent',name)
        patch=patch_context(src) if name=='context.py' else patch_hub(src)
        (out/name).write_text(patch,encoding='utf-8')
        print(name,hashlib.sha256(patch.encode()).hexdigest())
    for name,sub in [('checkpoint_runtime.py',[('0.3.5.35','0.3.5.37')]),
                     ('infinity_trakt.py',[('0.3.5.35','0.3.5.37'),('1.0.16','1.0.18')])]:
        src=(target/name).read_text(encoding='utf-8')
        for old,new in sub: src=exactly(src,old,new)
        compile(src,name,'exec');(out/name).write_text(src,encoding='utf-8')
        print(name,hashlib.sha256(src.encode()).hexdigest())
if __name__=='__main__':main()