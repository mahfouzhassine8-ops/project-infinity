import io
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Union

from .models import GuideData, Programme

_TZ_RE = re.compile(r"^\s*(\d{8,14})(?:\s*([+-]\d{4}|Z))?")


def local_tz():
    return datetime.now().astimezone().tzinfo or timezone.utc


def parse_xmltv_time(value: str):
    match = _TZ_RE.match(value or "")
    if not match:
        return None
    digits, offset = match.groups()
    fmt = {8: "%Y%m%d", 10: "%Y%m%d%H", 12: "%Y%m%d%H%M", 14: "%Y%m%d%H%M%S"}.get(len(digits))
    if not fmt:
        return None
    try:
        dt = datetime.strptime(digits, fmt)
    except ValueError:
        return None
    if offset == "Z":
        tz = timezone.utc
    elif offset:
        sign = 1 if offset[0] == "+" else -1
        hours = int(offset[1:3])
        minutes = int(offset[3:5])
        tz = timezone(sign * timedelta(hours=hours, minutes=minutes))
    else:
        tz = local_tz()
    return dt.replace(tzinfo=tz).astimezone(timezone.utc)


def _tag(element):
    return element.tag.rsplit("}", 1)[-1]


def _child_text(element, name):
    for child in element:
        if _tag(child) == name:
            return (child.text or "").strip()
    return ""


def parse_xmltv(source: Union[str, bytes], now=None, horizon_hours: int = 24) -> GuideData:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    earliest = now - timedelta(hours=4)
    latest = now + timedelta(hours=max(1, horizon_hours))
    programmes = defaultdict(list)
    display_names = defaultdict(list)

    stream = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
    for _event, elem in ET.iterparse(stream, events=("end",)):
        name = _tag(elem)
        if name == "channel":
            channel_id = (elem.attrib.get("id") or "").strip()
            if channel_id:
                for child in elem:
                    if _tag(child) == "display-name" and (child.text or "").strip():
                        display_names[channel_id].append((child.text or "").strip())
            elem.clear()
        elif name == "programme":
            channel_id = (elem.attrib.get("channel") or "").strip()
            start = parse_xmltv_time(elem.attrib.get("start", ""))
            stop = parse_xmltv_time(elem.attrib.get("stop", ""))
            if channel_id and start:
                if not stop or stop <= start:
                    stop = start + timedelta(hours=1)
                if stop >= earliest and start <= latest:
                    programmes[channel_id].append(
                        Programme(
                            channel_id=channel_id,
                            start=start,
                            stop=stop,
                            title=_child_text(elem, "title") or "Untitled",
                            subtitle=_child_text(elem, "sub-title"),
                            description=_child_text(elem, "desc"),
                            category=_child_text(elem, "category"),
                        )
                    )
            elem.clear()

    for items in programmes.values():
        items.sort(key=lambda p: p.start)
    return GuideData(programmes=dict(programmes), display_names=dict(display_names))
