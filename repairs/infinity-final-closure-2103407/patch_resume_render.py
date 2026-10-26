"""Exact signed411 read-only rendering optimization; no new persistence owner."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).parent
CC='script.infinity.commandcenter'

SIGNATURE='''def _render_source_stamp(root, bridge, names):
    """A rendering hint only; selected actions always verify raw source again."""
    import stat
    paths = [bridge / 'PROVIDER-CONTRACTS.json', root / 'addon.xml']
    paths.extend(root / name for name in sorted(names))
    result = [str(root), str(bridge)]
    for path in paths:
        value = path.lstat()
        if not stat.S_ISREG(value.st_mode) or path.resolve() != path.absolute():
            return None
        result.append((str(path), value.st_dev, value.st_ino, value.st_size,
                       value.st_mtime_ns, value.st_ctime_ns))
    return tuple(result)


'''

VERIFY='''def _render_verified_source(entry, route, render=None):
    if render is None:
        return verified_source(entry, route)
    from experience import _source_contract
    cache = render.setdefault('source_contracts', {})
    return verified_source(entry, route, lambda provider: _source_contract(provider, cache))


'''


def edits(name):
    if name=='experience.py':
        return [
            ('def _source_contract(provider):\n',SIGNATURE+'def _source_contract(provider, render_cache=None):\n'),
            ("        for name, digest in contract['files'].items():\n",
             "        stamp = _render_source_stamp(root, bridge, contract['files']) if render_cache is not None else None\n"
             "        cached = render_cache.get(provider) if stamp is not None else None\n"
             "        if cached is not None and cached[0] == stamp and cached[1] == contract:\n"
             "            return contract\n"
             "        if render_cache is not None:\n"
             "            render_cache.pop(provider, None)\n"
             "        for name, digest in contract['files'].items():\n"),
            ('        return contract\n    except (OSError, ValueError, RuntimeError, ET.ParseError):',
             "        if stamp is not None:\n"
             "            if _render_source_stamp(root, bridge, contract['files']) != stamp:\n"
             "                return None\n"
             "            # Only two reviewed source-memory providers can reach here.\n"
             "            if len(render_cache) < 2:\n"
             "                render_cache[provider] = (stamp, contract)\n"
             '        return contract\n    except (OSError, ValueError, RuntimeError, ET.ParseError):')
        ]
    if name=='plugin.py':
        return [
            ('def _target(entry, sources=None, render=None):\n',VERIFY+'def _target(entry, sources=None, render=None):\n'),
            ('            route = verified_source(entry, saved)\n','            route = _render_verified_source(entry, saved, render)\n'),
            ('        return verified_source(entry, source)\n','        return _render_verified_source(entry, source, render)\n'),
        ]
    if name=='addon.xml':
        return [('version="0.3.5.41"','version="0.3.5.42"')]
    raise ValueError('Unowned render source: '+name)


def patch(name,raw):
    plan=json.loads((ROOT/'RESUME-RENDER-412-PLAN.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=plan['owned_source_preimages'][name]:
        raise ValueError('Exact signed411 render source required: '+name)
    text=raw.decode()
    for old,new in edits(name):
        if text.count(old)!=1:raise ValueError('Render source boundary differs: '+name+' '+old[:55])
        text=text.replace(old,new,1)
    restored=text
    for old,new in reversed(edits(name)):restored=restored.replace(new,old,1)
    if restored.encode()!=raw:raise ValueError('Unrelated rendering change')
    if name.endswith('.py'):compile(text,name,'exec',dont_inherit=True)
    return text.encode()
