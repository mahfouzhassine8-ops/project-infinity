# Exact routing-function excerpts for regression only. Not shipped in the skin.
# Source: https://github.com/nebulous42069/Omega/blob/0494b4b82f5da765d5b03f1fe69fcdad1f507ead/omega/plugin.video.playlistbrowser/main.py
def load_baked_in_sources(base_idx_start: int = 100):
    """
    Load baked-in sources from addons\plugin.video.playlistbrowser\resources\baked_in.json.
    The JSON should be a list of objects with keys like:
      - name (str)
      - m3u or m3u_url (str)  [optional if 'json' provided]
      - json or json_url (str) [optional if 'm3u' provided]
      - epg or epg_xml or epg_url (str) [optional]
      - source_id (integer >= 100) [stable number for widget paths]
    Only additive: if file is missing or invalid, returns [].
    """
    try:
        # Resolve baked-in path inside the addon folder
        path = os.path.join(ADDON_PATH, 'resources', 'baked_in.json')
        raw = read_text(path)
        if not raw:
            return []
        data = json.loads(raw)
        if not isinstance(data, list):
            return []

        def pick(d, *keys):
            for k in keys:
                if k in d and d.get(k):
                    return d.get(k)
            return ""

        out = []
        reserved = set()
        for item in data:
            if not isinstance(item, dict) or 'source_id' not in item:
                continue
            try:
                source_id = int(item['source_id'])
                if source_id < base_idx_start or source_id in reserved:
                    log(f"Invalid or duplicate baked-in source_id: {source_id}")
                    continue
                reserved.add(source_id)
            except (ValueError, TypeError):
                log(f"Invalid baked-in source_id: {item['source_id']}")
        used = set()
        next_id = base_idx_start
        for item in data:
            if not isinstance(item, dict):
                continue
            if 'source_id' in item:
                try:
                    idx = int(item['source_id'])
                except (ValueError, TypeError):
                    continue
                if idx < base_idx_start or idx in used:
                    continue
            else:
                while next_id in reserved or next_id in used:
                    next_id += 1
                idx = next_id
                next_id += 1
            name = pick(item, 'name', 'Name', 'display_name') or f"Baked {idx}"
            m3u = pick(item, 'm3u', 'm3u_url', 'M3U', 'M3U_URL')
            js  = pick(item, 'json', 'json_url', 'JSON', 'JSON_URL')
            epg = pick(item, 'epg', 'epg_xml', 'epg_url', 'EPG', 'EPG_XML', 'EPG_URL')
            alias_source = pick(item, 'alias_source')
            alias_group = pick(item, 'alias_group')
            # A group reference can replace a playlist URL.
            if not (m3u or js or (alias_source and alias_group)):
                continue
            s = Source(idx, name, m3u, js, epg)
            s.alias_source = alias_source
            s.alias_group = alias_group
            try:
                s.src_icon = pick(item, 'icon','Icon','icon_url','IconUrl')
                s.src_fanart = pick(item, 'fanart','Fanart','fanart_url','FanartUrl')
            except Exception:
                pass
            out.append(s)
            used.add(idx)
        return out
    except Exception as e:
        try:
            log(f"baked_in.json load error: {e}")
        except Exception:
            pass
        return []

def load_sources():
    sources = []
    for i in (1,2,3):
        name = get_string_setting(f"SRC{i}_NAME", f"Playlist {i}")
        m3u = get_string_setting(f"SRC{i}_M3U_URL", "")
        js  = get_string_setting(f"SRC{i}_JSON_URL", "")
        epg = get_string_setting(f"SRC{i}_EPG_XML_URL", "")
        if any([m3u, js]): sources.append(Source(i, name, m3u, js, epg))
    # Append baked-in sources (if any)
    sources.extend(load_baked_in_sources(base_idx_start=100))

    return sources

def list_channels_by_group(src_idx: int, group_name: str):
    src = next((x for x in load_sources() if x.idx==src_idx), None)
    if not src:
        xbmcgui.Dialog().ok('Channels', 'Source not found.')
        xbmcplugin.endOfDirectory(HANDLE); return
    channels = [ch for ch in src.load_channels() if (ch.get('group') or '').strip() == (group_name or '').strip()]
    src.load_epg()
    xbmcplugin.setContent(HANDLE, 'videos')
    now_utc = datetime.now(timezone.utc)
    for ch in channels:
        epg_key = src.match_epg_key(ch)
        current = None
        if epg_key and src.progs.get(epg_key):
            for pr in src.progs[epg_key]:
                if pr['start'] <= now_utc < pr['stop']:
                    current = pr
                    break

        title_plain = ch.get('name','Channel')
        title_col = _apply_color(title_plain, 'COLOR_CHANNEL')

        if current:
            tstart = nice_time(current['start'])
            tstop = nice_time(current['stop'])
            epg_title = current.get('title','') or ''
            epg_col = _apply_color(epg_title, 'COLOR_EPG')
            time_col = _apply_color(f"({tstart}-{tstop})", 'COLOR_TIME')
            label_epg = f"{epg_col}  {time_col}"
            label = f"{title_col}  {label_epg}"
            label2 = label_epg
            plot = f"{epg_title}  ({tstart}-{tstop})\n{current.get('desc','') or ''}"
        else:
            # No current EPG: show only the channel name (no extra '(No current EPG)' text)
            label = f"{title_col}"
            label2 = ''
            plot = ''

        li = xbmcgui.ListItem(label=label)
        li.setLabel2(label2)
        li.setInfo('video', {'title': title_col, 'plot': plot, 'mediatype':'video', 'genre': ch.get('group','Live')})
        set_art(li, channel_logo(ch, src)); li.setProperty('IsPlayable','true')
        li.addContextMenuItems([('Add To Your Live TV Favorites', f"RunPlugin({build_url({'action':'fav_add','src':src.idx,'cname':ch.get('name',''),'tvg':ch.get('tvg_id',''),'url':ch.get('url',''),'logo':channel_logo(ch, src)})})")], replaceItems=True)
        xbmcplugin.addDirectoryItem(HANDLE, build_url({'action':'play','url':ch['url']}), li, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)

def router(paramstring):
    log("Router start")
    params = dict(urllib.parse.parse_qsl(paramstring[1:])) if paramstring else {}
    action = params.get('action')
    if action == 'settings': ADDON.openSettings()
    elif action == 'refresh_epg': refresh_epg(int(params.get('src','0') or '0'))
    elif action == 'refresh_channels': refresh_channels(int(params.get('src','0') or '0'))
    elif action == 'write_match_report': write_match_report(int(params.get('src','0') or '0'))
    elif action == 'play': play_item(params.get('url',''))
    elif action == 'source': list_source_home(int(params.get('src','0') or '0'))
    elif action == 'channels': list_channels(int(params.get('src','0') or '0'))
    elif action == 'guide_now': show_guide_now(int(params.get('src','0') or '0'))
    elif action == 'guide_channels': list_guide_channels(int(params.get('src','0') or '0'))
    elif action == 'guide_channel': show_guide_for_channel(int(params.get('src','0') or '0'), params.get('cname',''), params.get('tvg',''), params.get('url',''))
    elif action == 'channel_groups': list_channel_groups(int(params.get('src','0') or '0'))
    elif action == 'channels_by_group': list_channels_by_group(int(params.get('src','0') or '0'), params.get('group',''))
    elif action == 'favorites': list_favorites()
    elif action == 'fav_add': fav_add(int(params.get('src','0') or '0'), params.get('cname',''), params.get('tvg',''), params.get('url',''), params.get('logo','') or '')
    elif action == 'fav_remove': fav_remove(params.get('cname',''), params.get('tvg',''), params.get('url',''))
    elif action == 'refresh_all': refresh_all_sources()
    else: list_root()

# Source.load_channels, unmodified body; bound to a fixture Source in tests.
def load_channels(self):
    if getattr(self, 'alias_source', None):
        target = next((s for s in load_sources() if s.name == self.alias_source and s.idx != self.idx), None)
        if not target or getattr(target, 'alias_source', None):
            log(f"Widget source target unavailable: {self.alias_source}")
            return []
        return [ch for ch in target.load_channels()
                if (ch.get('group') or '').strip() == self.alias_group.strip()]
    if self.channels is not None: return self.channels
    # Prefer cached channels JSON (written by 'Refresh channels now')
    try:
        raw_path, ch_json_path = _playlist_cache_paths(self.idx, self)
        data = read_text(ch_json_path)
        if (data or '').strip():
            try:
                self.channels = json.loads(data)
                return self.channels
            except Exception:
                pass
    except Exception:
        pass
    # Fallback: fetch once and cache for subsequent runs
    if self.js:
        raw = read_text(self.js)
        self.channels = parse_json(raw)
    elif self.m3u:
        raw = read_text(self.m3u)
        self.channels = parse_m3u(raw)
    else:
        self.channels = []
    try:
        _, ch_json_path = _playlist_cache_paths(self.idx, self)
        _write_json(ch_json_path, self.channels)
    except Exception:
        pass
    return self.channels

