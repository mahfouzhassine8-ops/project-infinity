def _continue_native_item(item):
    """Recover a typed active video tag when JSON loses non-library metadata.

    Read only, at the existing arming point. A label or a numeric provider ID
    never establishes the media type. No title search, worker or writer.
    """
    if xbmc.getSkinDir() != 'skin.infinity.diggz':
        return {}
    try:
        player = xbmc.Player()
        if not player.isPlayingVideo():
            return {}
        source = player.getPlayingFile()
        if not source or (item.get('file') and item['file'] != source):
            return {}

        def snapshot():
            tag = player.getVideoInfoTag()
            return dict(type=tag.getMediaType(), title=tag.getTitle(),
                        showtitle=tag.getTVShowTitle(), season=tag.getSeason(),
                        episode=tag.getEpisode(),
                        uniqueid={name: str(tag.getUniqueID(name) or '').strip()
                                  for name in ('tmdb', 'tvdb', 'imdb')})

        native = snapshot()
        kind = native['type']
        if kind not in ('movie', 'episode'):
            return {}
        if not hub.media_identity('tv' if kind == 'episode' else 'movie', native['uniqueid'],
                                  native['season'], native['episode']):
            return {}
        known = item.get('uniqueid')
        if isinstance(known, dict) and any(
                str(value or '').strip() and native['uniqueid'].get(name) != str(value).strip()
                for name, value in known.items() if name in ('tmdb', 'tvdb', 'imdb')):
            return {}
        from title_metadata import capture
        information = capture(player)
        # The same file can carry consecutive episodes. Check typed identity as
        # well as the path after capture, and withhold every ambiguous snapshot.
        if native != snapshot() or source != player.getPlayingFile() or not player.isPlayingVideo():
            return {}
        result = dict(item, **native)
        result.update(information)
        if information.get('duration'):
            result['runtime'] = information['duration']
        result['file'] = source
        result.pop('id', None)  # Never promote an untyped ID to a library write.
        from experience import stable_route
        if not stable_route(source):
            result['infinity_transient_playback_source'] = True
        return result
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return {}
