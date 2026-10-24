import xbmcgui

from .providers import normalize_server


def _input(heading, default="", hidden=False):
    kwargs = {"heading": heading, "defaultt": default, "type": xbmcgui.INPUT_ALPHANUM}
    if hidden:
        kwargs["option"] = xbmcgui.ALPHANUM_HIDE_INPUT
    return xbmcgui.Dialog().input(**kwargs)


def add_source_dialog(store):
    dialog = xbmcgui.Dialog()
    kind = dialog.select("Add Live source", ["M3U / M3U8 URL", "Local M3U file", "Xtream-style login"])
    if kind < 0:
        return False
    name = _input("Source name", "My Live TV").strip()
    if not name:
        return False

    if kind == 0:
        m3u = _input("M3U / M3U8 playlist URL").strip()
        if not m3u:
            return False
        epg = _input("XMLTV / EPG URL (optional)").strip()
        store.add({"type": "m3u", "name": name, "m3u": m3u, "epg": epg})
        return True

    if kind == 1:
        path = dialog.browseSingle(1, "Choose M3U / M3U8 playlist", "files", ".m3u|.m3u8")
        if not path:
            return False
        epg = _input("XMLTV / EPG URL (optional)").strip()
        store.add({"type": "m3u", "name": name, "m3u": path, "epg": epg})
        return True

    server = _input("Provider server address").strip()
    username = _input("Username").strip()
    password = _input("Password", hidden=True)
    if not server or not username or not password:
        return False
    try:
        server = normalize_server(server)
    except ValueError as exc:
        dialog.ok("Infinity Live", str(exc))
        return False
    output_index = dialog.select("Stream format", ["MPEG-TS (recommended)", "HLS / M3U8"])
    output = "m3u8" if output_index == 1 else "ts"
    store.add({"type": "xtream", "name": name, "server": server, "username": username, "password": password, "output": output})
    return True


def manage_sources_dialog(store):
    dialog = xbmcgui.Dialog()
    while True:
        sources = store.sources()
        active = store.active()
        labels = ["＋ Add source"]
        for item in sources:
            marker = "● " if active and item.get("id") == active.get("id") else "○ "
            labels.append(marker + (item.get("name") or "Live TV"))
        labels.append("Remove source")
        choice = dialog.select("Infinity Live sources", labels)
        if choice < 0:
            return False
        if choice == 0:
            if add_source_dialog(store):
                return True
            continue
        if choice == len(labels) - 1:
            if not sources:
                continue
            remove_index = dialog.select("Remove source", [item.get("name") or "Live TV" for item in sources])
            if remove_index >= 0 and dialog.yesno("Infinity Live", f"Remove {sources[remove_index].get('name') or 'this source'}?"):
                store.remove(sources[remove_index]["id"])
                return True
            continue
        source = sources[choice - 1]
        store.set_active(source["id"])
        return True
