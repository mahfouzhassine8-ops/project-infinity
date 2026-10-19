#!/usr/bin/env python3
"""Staged Group #1 original #01 ONLY: choose existing verified TV routes safely.

Target EXACT 2103390 Command Center plugin.py, never addon source on device.
No third-party addons, database, saved route or SlyGuy changes. Fail closed.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

PREIMAGE_SHA256 = '11a741a694869eeca6f1fbdac17bb6ab02c9f807c73a3aa95a4b43323fc574fd'

ORIGINAL_ROUTE = '''        route = stable_route(preference.get('route') or entry.get('stable_source', ''))
        if route and number(preference.get('failures')) < 2:
            host = route.split('/')[2] if route.startswith('plugin://') else ''
            if not host or _has_addon(host, render):
                return route
'''
SAFE_ROUTE = '''        if number(preference.get('failures')) < 2:
            # Validate stored preferences and the entry's independently captured
            # stable source separately. A stale/invalid preferred URL must not
            # mask an already verified, still installed fallback plugin route.
            for saved in (preference.get('route'), entry.get('stable_source')):
                route = stable_route(saved)
                if not route:
                    continue
                host = route.split('/')[2] if route.startswith('plugin://') else ''
                if not host or _has_addon(host, render):
                    return route
'''
ORIGINAL_TMDB = '''    tmdb = str((entry.get('show_tmdb') if media == 'tv' and entry.get('show_ids_verified') is True
                else entry.get('tmdb') if media == 'movie' else '') or '').strip()
'''
SAFE_TMDB = '''    tmdb = str((entry.get('show_tmdb') if media == 'tv' and entry.get('show_ids_verified') is True
                else entry.get('tmdb') if media == 'movie' else '') or '').strip()
    if media == 'tv' and not tmdb:
        # An already saved, validated SHOW-EPISODE identity is sufficient
        # evidence of a series TMDb ID. An EPISODE ID NEVER is. No provider
        # search, name-based guess, or mutation of saved history is allowed.
        identity = hub.entry_identity(entry)
        if identity and identity.get('scope') == 'show_episode':
            tmdb = str(identity.get('ids', {}).get('tmdb') or '')
'''


def patch_bytes(source:bytes)->bytes:
    if hashlib.sha256(source).hexdigest() != PREIMAGE_SHA256:
        raise ValueError('Unknown version of protected 2103390 Command Center plugin.py')
    text=source.decode('utf-8')
    for old,new in ((ORIGINAL_ROUTE,SAFE_ROUTE),(ORIGINAL_TMDB,SAFE_TMDB)):
        if text.count(old)!=1:
            raise ValueError('Refuse ambiguous route patch')
        text=text.replace(old,new,1)
    return text.encode('utf-8')


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('original',type=Path);p.add_argument('staged',type=Path)
    x=p.parse_args()
    if x.original.resolve()==x.staged.resolve():raise ValueError('Never rewrite original')
    patched=patch_bytes(x.original.read_bytes());x.staged.parent.mkdir(parents=True,exist_ok=True)
    x.staged.write_bytes(patched)
    print('Source-only TV source-memory guard staged, no device mutation')
if __name__=='__main__': main()
