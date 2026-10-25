"""WatchNixtoons2: opt-in, persistent, exact-route identity link (2103403 work-in-progress).

Reads the signed 2103402 commandcenter context and modifies only this file.
No changes to providers, Search, skin, or Cobra. Runtime writes are guarded by
existing Essential-First persistence_scope() and resume_hub.save().
"""
from pathlib import Path
import hashlib, sys

EXPECTED = '96e4216c67d6a5a61c7e085da753089ac459373a30240f6acc6bb51a440a4b64'


def replace_once(text, old, new):
    assert text.count(old) == 1, (old[:100], text.count(old))
    return text.replace(old, new, 1)


def patch(text):
    assert hashlib.sha256(text.encode()).hexdigest() == EXPECTED, 'Wrong signed CC source'
    # Keep all current search-provider guards and explicit consent unchanged.
    added = '''def _watchnixtoons_identity_slot(route):
    import hashlib
    if not isinstance(route, str) or not route.startswith('plugin://plugin.video.watchnixtoons2/') or len(route) > 8192:
        return ''
    return hashlib.sha256(route.encode('utf-8')).hexdigest()


def _watchnixtoons_verified_link(data, route, kind):
    """An opt-in link can be reused only for this exact provider URI and media kind."""
    slot = _watchnixtoons_identity_slot(route)
    links = data.get('nixtoons_verified_links', {})
    if not slot or not isinstance(links, dict):
        return None
    row = links.get(slot)
    if (not isinstance(row, dict) or row.get('source') != route or
            row.get('stable_source') != route or row.get('media') !=
            ('movie' if kind == 'movie' else 'tv')):
        return None
    identity = hub.entry_identity(row)
    if not identity or identity.get('kind') != kind or hub.identity_key(identity) != row.get('key'):
        return None
    return dict(row)


def _watchnixtoons_owned_records(data, route):
    """Inspect every owned list, not only Resume Hub's five primary buckets."""
    for bucket in ('items', 'watched', 'watchlist', 'collection', 'later'):
        for record in data.get(bucket, {}).values():
            if isinstance(record, dict) and record.get('source') == route:
                yield record
    for values in data.get('lists', {}).values():
        if isinstance(values, dict):
            for record in values.values():
                if isinstance(record, dict) and record.get('source') == route:
                    yield record


def _watchnixtoons_store_verified_link(item, route, kind, entry):
    """Persist only the explicitly confirmed typed-ID association, not a tracking action.

    Fail closed on a conflicting route identity, unsupported schema or full map.
    The existing essential participant owns atomic writes and checkpoint proof.
    """
    slot = _watchnixtoons_identity_slot(route)
    identity = hub.entry_identity(entry)
    if (not slot or not identity or identity.get('kind') != kind or
            entry.get('source') != route or entry.get('stable_source') != route or
            entry.get('key') != hub.identity_key(identity) or
            item.getPath() != route or item.getVideoInfoTag().getMediaType() != kind):
        return False
    profile = addon_profile()
    with persistence_scope():
        data = hub.load(profile)
        links = data.get('nixtoons_verified_links', {})
        if not isinstance(links, dict):
            return False
        old = _watchnixtoons_verified_link(data, route, kind)
        if slot in links and not old:
            return False
        if old is not None and not hub.same_identity(hub.entry_identity(old), identity):
            return False
        for row in _watchnixtoons_owned_records(data, route):
            bound = hub.entry_identity(row)
            if bound is not None and not hub.same_identity(bound, identity):
                return False
        if old is not None:
            return True
        if len(links) >= 500:
            return False  # Never evict user-approved links as an implicit side effect.
        linked = {key: value for key, value in entry.items() if key != '_native_watched'}
        linked['source'] = route
        linked['stable_source'] = route
        updated = dict(links)
        updated[slot] = linked
        data['nixtoons_verified_links'] = updated
        hub.save(profile, data, hub.publish_home, retain_records=True)
    return True


'''
    text = replace_once(text, 'def _watchnixtoons_exact_previous(item, route, kind):\n', added + 'def _watchnixtoons_exact_previous(item, route, kind):\n')
    text = replace_once(text,
'''    data=hub.load_view(addon_profile())
    matches=[]
    media='movie' if kind=='movie' else 'tv'
    for bucket in ('items','watched','watchlist','collection','later'):
        for row in data.get(bucket,{}).values():
            if not isinstance(row,dict) or row.get('source')!=route or row.get('stable_source')!=route:
                continue
            identity=hub.entry_identity(row)
            if not identity or row.get('media')!=media or identity['kind']!=kind:
                continue
            if kind in ('season','episode') and (hub.episode_number(row.get('season')) !=
                                                  hub.episode_number(item.getVideoInfoTag().getSeason())):
                continue
            if kind=='episode' and (hub.episode_number(row.get('episode')) !=
                                    hub.episode_number(item.getVideoInfoTag().getEpisode())):
                continue
            matches.append((row,identity))
''',
'''    data=hub.load_view(addon_profile())
    matches=[]
    media='movie' if kind=='movie' else 'tv'
    verified = _watchnixtoons_verified_link(data, route, kind)
    candidates = list(_watchnixtoons_owned_records(data, route))
    if verified is not None:
        candidates.append(verified)
    for row in candidates:
        if row.get('stable_source') != route:
            continue
        identity=hub.entry_identity(row)
        if not identity or row.get('media')!=media or identity['kind']!=kind:
            continue
        if kind in ('season','episode') and (hub.episode_number(row.get('season')) !=
                                              hub.episode_number(item.getVideoInfoTag().getSeason())):
            continue
        if kind=='episode' and (hub.episode_number(row.get('episode')) !=
                                hub.episode_number(item.getVideoInfoTag().getEpisode())):
            continue
        matches.append((row,identity))
''')
    # Keep fail-closed on all agreeing prior identities and no name-based matching.
    text = replace_once(text,
'''    return entry if hub.entry_identity(entry) and entry['key']==hub.identity_key(hub.entry_identity(entry)) else None


def _watchnixtoons_tracking''',
'''    if not hub.entry_identity(entry) or entry['key'] != hub.identity_key(hub.entry_identity(entry)):
        return None
    if not _watchnixtoons_store_verified_link(item, route, kind, entry):
        xbmcgui.Dialog().ok('Infinity Trakt', 'The verified link could not be saved safely. No tracking action was performed.')
        return None
    return entry


def _watchnixtoons_tracking''')
    compile(text,'context.py','exec')
    return text


if __name__=='__main__':
    original=Path(sys.argv[1]).read_text(encoding='utf-8')
    result=patch(original)
    dest=Path(sys.argv[2]);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(result,encoding='utf-8')
    print('original SHA',hashlib.sha256(original.encode()).hexdigest())
    print('new SHA     ',hashlib.sha256(result.encode()).hexdigest())
