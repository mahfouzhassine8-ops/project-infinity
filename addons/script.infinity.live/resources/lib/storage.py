import json
import os
import tempfile
import uuid

import xbmcaddon
import xbmcvfs


class SourceStore:
    def __init__(self):
        addon = xbmcaddon.Addon("script.infinity.live")
        self.profile_dir = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
        os.makedirs(self.profile_dir, exist_ok=True)
        self.path = os.path.join(self.profile_dir, "sources.json")
        self.data = self._load()

    @staticmethod
    def _default():
        return {"schema": 1, "active_source_id": "", "sources": [], "favorites": {}, "last_channel": {}}

    def _load(self):
        if not os.path.exists(self.path):
            return self._default()
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                value = json.load(handle)
            if not isinstance(value, dict) or value.get("schema") != 1:
                raise ValueError("unsupported schema")
            value.setdefault("sources", [])
            value.setdefault("favorites", {})
            value.setdefault("last_channel", {})
            value.setdefault("active_source_id", "")
            return value
        except Exception:
            return self._default()

    def save(self):
        fd, tmp = tempfile.mkstemp(prefix="infinity-live-", suffix=".json", dir=self.profile_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, sort_keys=True)
            try:
                os.chmod(tmp, 0o600)
            except OSError:
                pass
            os.replace(tmp, self.path)
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def sources(self):
        return list(self.data.get("sources", []))

    def active(self):
        sources = self.sources()
        wanted = self.data.get("active_source_id")
        for source in sources:
            if source.get("id") == wanted:
                return source
        return sources[0] if sources else None

    def add(self, source: dict):
        source = dict(source)
        source.setdefault("id", uuid.uuid4().hex)
        source.setdefault("name", "Live TV")
        self.data["sources"].append(source)
        self.data["active_source_id"] = source["id"]
        self.save()
        return source

    def set_active(self, source_id: str):
        if any(item.get("id") == source_id for item in self.sources()):
            self.data["active_source_id"] = source_id
            self.save()

    def remove(self, source_id: str):
        self.data["sources"] = [item for item in self.sources() if item.get("id") != source_id]
        self.data.get("favorites", {}).pop(source_id, None)
        self.data.get("last_channel", {}).pop(source_id, None)
        if self.data.get("active_source_id") == source_id:
            self.data["active_source_id"] = self.data["sources"][0]["id"] if self.data["sources"] else ""
        self.save()

    def favorites(self, source_id: str):
        return set(self.data.setdefault("favorites", {}).get(source_id, []))

    def toggle_favorite(self, source_id: str, channel_key: str):
        values = self.favorites(source_id)
        if channel_key in values:
            values.remove(channel_key)
            enabled = False
        else:
            values.add(channel_key)
            enabled = True
        self.data.setdefault("favorites", {})[source_id] = sorted(values)
        self.save()
        return enabled

    def set_last_channel(self, source_id: str, channel_key: str):
        self.data.setdefault("last_channel", {})[source_id] = channel_key
        self.save()

    def last_channel(self, source_id: str):
        return self.data.setdefault("last_channel", {}).get(source_id, "")
