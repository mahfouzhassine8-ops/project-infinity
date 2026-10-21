"""Additive local-list adapter; keep the original protected persistence owner."""
from __future__ import annotations
import ast
import xml.etree.ElementTree as ET
from native94 import once, require


def replace_function(raw,name,transform):
    text=raw.decode();tree=ast.parse(text)
    node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
    lines=text.splitlines(keepends=True)
    original=''.join(lines[node.lineno-1:node.end_lineno])
    return once(raw,original.encode(),transform(original).encode())


def hub(raw):
    raw=once(raw,b"    'collection': 1000,",b"    'collection': 1000,\n    'later': 500,")
    raw=once(raw,b"('items', 'sources', 'watched', 'watchlist', 'collection', 'ratings', 'lists')",
        b"('items', 'sources', 'watched', 'watchlist', 'collection', 'ratings', 'lists', 'later')")
    old=b"for bucket in ('items', 'watched', 'watchlist', 'collection'):"
    require(raw.count(old)==2,'existing identity/store lookup scope drift')
    raw=raw.replace(old,b"for bucket in ('items', 'watched', 'watchlist', 'collection', 'later'):")
    helper=b'''def show_identity(kind, ids, season=-1):
    ids = verified_ids(ids)
    if not ids or kind not in ('tvshow', 'season'):
        return None
    identity = dict(schema=1, kind=kind, scope='show' if kind == 'tvshow' else 'show_season', ids=ids)
    if kind == 'season':
        season = episode_number(season)
        if season < 0:
            return None
        identity['season'] = season
    return identity


'''
    raw=once(raw,b'def entry_identity(entry):\n',helper+b'def entry_identity(entry):\n')
    def validate(block):
        position=block.rindex('    return None')
        return block[:position]+'''    if media == 'tv' and value.get('kind') in ('tvshow', 'season'):
        kind = value['kind']
        if value.get('scope') != ('show' if kind == 'tvshow' else 'show_season'):
            return None
        if kind == 'season' and episode_number(value.get('season')) != episode_number(entry.get('season')):
            return None
        return show_identity(kind, value.get('ids'), value.get('season', -1))
'''+block[position:]
    raw=replace_function(raw,'entry_identity',validate)
    raw=once(raw,b"            if identity['kind'] == 'episode':\n                raw += '|%s|%s' % (identity['season'], identity['episode'])",
        b"            if identity['kind'] == 'episode':\n                raw += '|%s|%s' % (identity['season'], identity['episode'])\n            elif identity['kind'] == 'season':\n                raw += '|%s' % identity['season']")
    raw=once(raw,b"    common = set(left['ids']) & set(right['ids'])",
        b"    if left['kind'] == 'season' and left['season'] != right['season']:\n        return False\n    common = set(left['ids']) & set(right['ids'])")
    return raw


def plugin(raw):
    def context(block):
        legacy=block.replace('def _context(', 'def _legacy_management_context(',1)
        return legacy+'''


def _context(entry, data, bucket='', list_name=''):
    rows = _legacy_management_context(entry, data, bucket, list_name)
    kept = [row for row in rows if not any(('op=' + op) in row[1] for op in
            ('mark-watched', 'mark-unwatched', 'toggle-watchlist', 'toggle-collection'))]
    if hub.entry_identity(entry) and not entry.get('synthetic_next'):
        kept.insert(0, ('Infinity Trakt', _mutate_url('trakt', entry['key'])))
    return kept
'''
    raw=replace_function(raw,'_context',context)
    raw=once(raw,b"    op = PARAMS.get('op', '')\n    key = PARAMS.get('key', '')",
        b"    op = PARAMS.get('op', '')\n    key = PARAMS.get('key', '')\n    if op == 'trakt':\n        from infinity_trakt import show_saved\n        show_saved(key)\n        xbmcplugin.endOfDirectory(HANDLE, succeeded=True, cacheToDisc=False)\n        return")
    raw=once(raw,b"'collection': 'Collection', 'history': 'Watched History',",
        b"'collection': 'Collection', 'later': 'Save For Later', 'history': 'Watched History',")
    require(raw.count(b"('Collection', 'collection',")==2,'both existing local navigators required')
    raw=raw.replace(b"            ('Collection', 'collection',",b"            ('Save For Later', 'later', 'Your separate local saved list'),\n            ('Collection', 'collection',")
    raw=once(raw,b"    action = PARAMS.get('action', 'continue')\n",
        b"    action = PARAMS.get('action', 'continue')\n    if action == 'search':\n        from infinity_search import open_search\n        open_search(PARAMS.get('media', 'movie'))\n        xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)\n        return\n")
    return raw


def context(raw):
    return replace_function(raw,'main',lambda block:'''def main():
    from infinity_trakt import main as local_tracking
    local_tracking(getattr(sys, 'listitem', None))''')


def addon(raw):
    root=ET.fromstring(raw)
    extension=root.find('extension[@point="kodi.context.item"]')
    require(extension is not None,'original local context ingress missing')
    menu=extension.find('menu');items=menu.findall('item')
    require(len(items)==2,'unexpected existing Command Center context entries')
    for item in items:menu.remove(item)
    item=ET.SubElement(menu,'item',{'library':'context.py','args':'manage'})
    ET.SubElement(item,'label').text='Infinity Trakt'
    ET.SubElement(item,'visible').text='[String.IsEqual(ListItem.DBTYPE,movie) | String.IsEqual(ListItem.DBTYPE,episode) | String.IsEqual(ListItem.DBTYPE,tvshow) | String.IsEqual(ListItem.DBTYPE,season)] + String.IsEmpty(ListItem.Property(Infinity.ResumeHub.Key)) + [!String.IsEmpty(ListItem.UniqueID(tmdb)) | !String.IsEmpty(ListItem.UniqueID(tvdb)) | !String.IsEmpty(ListItem.UniqueID(imdb)) | Integer.IsGreater(ListItem.DBID,0)]'
    return ET.tostring(root,encoding='utf-8')


def bridge_addon(raw):
    root=ET.fromstring(raw);node=root.find('extension[@point="kodi.context.item"]')
    require(node is not None,'original redundant Infinity context entry missing');root.remove(node)
    return ET.tostring(root,encoding='utf-8')


def controller(raw):
    # Keep original episode canonicalization, existing writer lease, queued
    # Kodi sync, stale-state checks and all legacy toggle call contracts.
    raw=once(raw,b'''            else:
                return False
        saved_canonical''',b'''            elif action in ('add-watchlist', 'remove-watchlist', 'add-collection', 'remove-collection', 'save-later', 'remove-later'):
                pass  # explicit idempotent intent; never turn Add into Remove
            else:
                return False
        saved_canonical''')
    raw=once(raw,b'''        if changed is None:
            return False
        if identity["kind"] == "episode" and provider(entry):''',b'''        if action in ('add-watchlist', 'remove-watchlist', 'add-collection', 'remove-collection', 'save-later', 'remove-later'):
            from infinity_trakt import set_membership
            changed = admitted if set_membership(data, admitted, action) else None
        if changed is None:
            return False
        if identity["kind"] == "episode" and provider(entry):''')
    raw=once(raw,b'for bucket in ("items", "watched", "watchlist", "collection"):',
        b'for bucket in ("items", "watched", "watchlist", "collection", "later"):')
    return raw
