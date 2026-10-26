"""Exact signed407 Search metadata transport and presentation-only corrections."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
CC = 'script.infinity.commandcenter'


def edits(name):
    if name == 'infinity_search.py':
        return [
            ("'mpaa','rating','thumbnail']", "'mpaa','rating','thumbnail','trailer','premiered']"),
            ("'runtime','mpaa','rating') if key in row}",
             "'runtime','mpaa','rating','premiered') if key in row}\n"
             "        from title_metadata import trailer_route\n"
             "        trailer = trailer_route(row.get('trailer'))\n"
             "        if trailer:info['trailer'] = trailer"),
        ]
    if name == 'title_metadata.py':
        # Kodi's older getter returns a localized date. The existing W3C
        # getter preserves the same date without ambiguous locale parsing.
        return [("'premiered': 'getPremiered'", "'premiered': 'getPremieredAsW3C'")]
    if name == 'information.py':
        return [
            ('from pathlib import Path\n', 'from pathlib import Path\nfrom datetime import date\nimport re\n'),
            ('        value = data.get(field)\n',
             '        value = data.get(field)\n'
             '        if field == "premiered":\n'
             '            # Kodi can expose a Windows FILETIME epoch as 1601-01-01.\n'
             '            # Validate only the displayed fact; keep the original snapshot.\n'
             '            try:\n'
             '                if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):\n'
             '                    raise ValueError()\n'
             '                if date.fromisoformat(value).year < 1800:\n'
             '                    raise ValueError()\n'
             '            except ValueError:\n'
             '                value = ""\n'
             '        elif field == "rating" and type(value) in (int, float):\n'
             '            value = "%.1f" % value\n'),
            ('            self.getControl(102).setEnabled(trailer)\n',
             '            self.getControl(102).setLabel("Trailer" if trailer else "Trailer unavailable")\n'
             '            self.getControl(102).setEnabled(trailer)\n'),
        ]
    raise ValueError('Unowned metadata source: '+name)


def patch(name, raw, require_preimage=True):
    if require_preimage:
        plan = json.loads((ROOT/'FIRSTPARTY-COMPOSITION-PLAN.json').read_text())
        expected = plan['plan'][CC]['signed407_all_file_preimages'][name]
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Wrong signed metadata preimage: '+name)
    text = raw.decode()
    for old, new in edits(name):
        if text.count(old) != 1:
            raise ValueError('Nonunique metadata transport boundary: '+name)
        text = text.replace(old,new,1)
    ast.parse(text)
    restored = text
    for old, new in reversed(edits(name)):
        restored = restored.replace(new,old,1)
    if restored.encode() != raw:
        raise ValueError('Unrelated metadata source changed')
    return text.encode()
