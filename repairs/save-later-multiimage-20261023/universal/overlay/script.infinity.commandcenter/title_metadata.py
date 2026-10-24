# SPDX-License-Identifier: GPL-2.0-or-later
"""Lossless descriptive metadata from an already verified selected title.

This is presentation data, never identity, provider capability or route proof.
It stays in the existing entry when an explicitly requested list action saves
that entry. Reading Information does not create progress or write any store.
"""
from __future__ import annotations

import math
from urllib.parse import urlsplit


TEXT_FIELDS = {
    'plot': 'getPlot', 'tagline': 'getTagLine', 'originaltitle': 'getOriginalTitle',
    'premiered': 'getPremiered', 'mpaa': 'getMPAA', 'cast': 'getCast',
}
LIST_FIELDS = {
    'genre': 'getGenres', 'director': 'getDirectors', 'writer': 'getWriters',
    'studio': 'getStudios', 'country': 'getCountries',
}


def _read(tag, name):
    try:
        return getattr(tag, name)()
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return None


def trailer_route(value):
    """Accept only the supplied URI, never a builtin or a guessed title search."""
    if not isinstance(value, str) or not value or any(c in value for c in '\r\n\x00'):
        return ''
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ''
    if parsed.scheme in ('http', 'https') and parsed.netloc:
        return value
    if parsed.scheme == 'plugin' and parsed.netloc and all(
            c.isalnum() or c in '._-' for c in parsed.netloc):
        return value
    return ''


def capture(item):
    """Copy all available original synopsis text, with no length/line limit."""
    try:
        tag = item.getVideoInfoTag()
    except (AttributeError, TypeError, RuntimeError):
        return {}
    result = {}
    for field, getter in TEXT_FIELDS.items():
        value = _read(tag, getter)
        if isinstance(value, str) and value:
            result[field] = value  # Do not strip, summarize or crop the synopsis.
    for field, getter in LIST_FIELDS.items():
        value = _read(tag, getter)
        if isinstance(value, (list, tuple)):
            values = [v for v in value if isinstance(v, str) and v]
            if values:
                result[field] = values
    for field, getter in (('year', 'getYear'), ('duration', 'getDuration')):
        value = _read(tag, getter)
        if type(value) is int and value > 0:
            result[field] = value
    rating = _read(tag, 'getRating')
    if type(rating) in (int, float) and math.isfinite(rating) and 0 < rating <= 10:
        result['rating'] = rating
    trailer = trailer_route(_read(tag, 'getTrailer'))
    if trailer:
        result['trailer'] = trailer
    return result


def from_entry(entry):
    """Read presentation fields without allowing them to override title IDs."""
    snapshot = entry.get('information')
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    result = {}
    for field in TEXT_FIELDS:
        value = snapshot.get(field, entry.get(field))
        if isinstance(value, str) and value:
            result[field] = value
    for field in LIST_FIELDS:
        value = snapshot.get(field, entry.get(field))
        if isinstance(value, (list, tuple)):
            values = [v for v in value if isinstance(v, str) and v]
            if values:
                result[field] = values
    for field in ('year', 'duration'):
        value = (entry.get('duration') or snapshot.get(field)) if field == 'duration' else snapshot.get(field, entry.get(field))
        if type(value) in (int, float) and math.isfinite(value) and value > 0:
            result[field] = int(value)
    value = snapshot.get('rating')
    if type(value) in (int, float) and math.isfinite(value) and 0 < value <= 10:
        result['rating'] = value
    trailer = trailer_route(snapshot.get('trailer', entry.get('trailer')))
    if trailer:
        result['trailer'] = trailer
    return result


def from_player_item(item):
    """Metadata from the same typed Player.GetItem result as playback identity."""
    if not isinstance(item, dict):
        return {}
    data = dict(item)
    if type(item.get('runtime')) in (int, float):
        data['duration'] = item['runtime']  # Kodi JSON runtime is seconds.
    cast = item.get('cast')
    if isinstance(cast, list):
        names = []
        for person in cast:
            if not isinstance(person, dict) or not isinstance(person.get('name'), str) or not person['name']:
                continue
            role = person.get('role')
            names.append(person['name'] + (' as ' + role if isinstance(role, str) and role else ''))
        if names:
            data['cast'] = '\n'.join(names)
    # These are metadata fields only: no file/route/IDs can enter this snapshot.
    return from_entry({'information': data})
