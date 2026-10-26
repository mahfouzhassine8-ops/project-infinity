def _local_next_proof(entry):
    """A rendered route is only a selector; fresh native details authorize play."""
    if not isinstance(entry, dict):
        return None
    identity = hub.entry_identity(entry)
    proof = entry.get('library_next')
    if (entry.get('synthetic_next') is not True or entry.get('next_verified') is not True or
            entry.get('show_ids_verified') is not True or not identity or
            identity.get('scope') != 'show_episode' or not isinstance(proof, dict)):
        return None
    tmdb = str(entry.get('show_tmdb') or '')
    if (not hub.verified_ids({'tmdb': tmdb}) or identity['ids'].get('tmdb') != tmdb or
            proof.get('show_tmdb') != tmdb or
            any(type(proof.get(name)) is not int or proof[name] <= 0
                for name in ('episodeid', 'tvshowid')) or
            any(type(proof.get(name)) is not int or proof[name] < 0
                for name in ('season', 'episode')) or
            proof.get('season') != identity.get('season') or
            proof.get('episode') != identity.get('episode')):
        return None
    source = proof.get('file')
    if not stable_route(source) or source.lower().startswith('plugin://'):
        return None
    return proof


def play_local_next(key):
    """Resolve only the current exact local catalogue successor after a click."""
    if xbmc.getSkinDir() != 'skin.infinity.diggz' or not hub.KEY_RE.fullmatch(str(key)):
        return False
    try:
        entry = next((value for value in hub.next_episodes(hub.load_view(PROFILE))
                      if value.get('key') == key), None)
        proof = _local_next_proof(entry)
        if proof is None:
            return False
        properties = ['title', 'showtitle', 'season', 'episode', 'tvshowid', 'file',
                      'uniqueid', 'plot', 'runtime', 'art']
        details = _rpc('VideoLibrary.GetEpisodeDetails', {
            'episodeid': proof['episodeid'], 'properties': properties}).get('episodedetails')
        if (not isinstance(details, dict) or type(details.get('episodeid')) is not int or
                details['episodeid'] != proof['episodeid'] or
                type(details.get('tvshowid')) is not int or details['tvshowid'] != proof['tvshowid'] or
                any(type(details.get(name)) is not int for name in ('season', 'episode')) or
                details.get('season') != entry['season'] or details.get('episode') != entry['episode'] or
                details.get('file') != proof['file']):
            return False
        show = _rpc('VideoLibrary.GetTVShowDetails', {
            'tvshowid': proof['tvshowid'], 'properties': ['uniqueid']}).get('tvshowdetails')
        if (not isinstance(show, dict) or type(show.get('tvshowid')) is not int or
                show['tvshowid'] != proof['tvshowid'] or
                hub.verified_ids(show.get('uniqueid')).get('tmdb') != entry['show_tmdb']):
            return False
        import xbmcvfs
        if not xbmcvfs.exists(proof['file']):
            return False
        # Kodi resolves this as its normal native library video. No stream URL,
        # title search, provider fallback or synthetic parent-as-episode ID.
        item = xbmcgui.ListItem(label=str(details.get('title') or entry['label']), path=proof['file'])
        item.setInfo('video', {'title': str(details.get('title') or entry['title']),
            'tvshowtitle': str(details.get('showtitle') or entry['showtitle']),
            'mediatype': 'episode', 'dbid': proof['episodeid'], 'season': entry['season'],
            'episode': entry['episode'], 'plot': str(details.get('plot') or ''),
            'duration': int(number(details.get('runtime')))})
        ids = hub.verified_ids(details.get('uniqueid'))
        if ids:
            item.setUniqueIDs(ids)
        if isinstance(details.get('art'), dict):
            item.setArt(details['art'])
        xbmcplugin.setResolvedUrl(HANDLE, True, item)
        return True
    except (AttributeError, KeyError, OSError, TypeError, ValueError, RuntimeError):
        return False
