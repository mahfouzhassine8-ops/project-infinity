from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha1
from typing import Dict, List, Optional


@dataclass
class Channel:
    name: str
    url: str
    group: str = "Other"
    tvg_id: str = ""
    tvg_name: str = ""
    logo: str = ""
    number: str = ""
    properties: Dict[str, str] = field(default_factory=dict)

    def stable_key(self) -> str:
        basis = "\x1f".join((self.tvg_id.strip(), self.name.strip(), self.url.strip()))
        return sha1(basis.encode("utf-8", "replace")).hexdigest()


@dataclass
class Programme:
    channel_id: str
    start: datetime
    stop: datetime
    title: str
    subtitle: str = ""
    description: str = ""
    category: str = ""


@dataclass
class Playlist:
    channels: List[Channel]
    guide_url: str = ""


@dataclass
class GuideData:
    programmes: Dict[str, List[Programme]] = field(default_factory=dict)
    display_names: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ChannelGuide:
    current: Optional[Programme] = None
    next: Optional[Programme] = None
    schedule: List[Programme] = field(default_factory=list)


@dataclass
class Catalog:
    channels: List[Channel]
    guides: Dict[str, ChannelGuide]
    source_id: str
    source_name: str
    groups: List[str]
    warning: str = ""
