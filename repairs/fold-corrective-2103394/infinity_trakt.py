"""Infinity's local tracking menu; no external Trakt API or provider writes."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from common import addon_profile, persistence_scope
import resume_hub as hub

ACTIONS=(('Mark Watched','mark-watched'),('Mark Unwatched','mark-unwatched'),
         ('Add to Watchlist','add-watchlist'),('Remove from Watchlist','remove-watchlist'),
         ('Add to Collection','add-collection'),('Remove from Collection','remove-collection'),
         ('Save For Later','save-later'),('Remove Save For Later','remove-later'))


def _bridge():
    addon=xbmcaddon.Addon('script.infinity.watchedbridge')
    if addon.getAddonInfo('version')!='1.0.5':
        raise RuntimeError('Install the matching Infinity Watched Bridge component before using this menu.')
    root=Path(xbmcvfs.translatePath(addon.getAddonInfo('path'))).resolve()
    sys.path.insert(0,str(root))
    spec=importlib.util.spec_from_file_location('_infinity_verified_watched_context',root/'context.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if Path(module.controller.__file__).resolve()!=root/'controller.py':
        raise RuntimeError('A conflicting tracking module is loaded. No saved data was changed.')
    cc=xbmcaddon.Addon('script.infinity.commandcenter')
    modules=module.controller.load(xbmcvfs.translatePath(cc.getAddonInfo('path')))
    return module,modules


def selected(item, bridge, modules):
    if item is None:return None
    tag=item.getVideoInfoTag();kind=tag.getMediaType()
    if kind in ('movie','episode'):
        return bridge.selected(modules,item)  # retain the verified producer/episode contracts
    if kind not in ('tvshow','season'):
        return None
    ids=hub.verified_ids({n:tag.getUniqueID(n) for n in ('tmdb','tvdb','imdb')})
    season=tag.getSeason() if kind=='season' else -1
    if kind=='season':
        # Provider season IDs are not assumed to be series IDs. The original
        # native library can prove its season-to-show relation without a guess.
        dbid=tag.getDbId()
        if type(dbid) is not int or dbid<=0 or not item.getPath().startswith('videodb://'):
            return None
        reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,
            method='VideoLibrary.GetSeasonDetails',params=dict(seasonid=dbid,properties=['season','tvshowid'])))))
        detail=reply.get('result',{}).get('seasondetails',{})
        show=detail.get('tvshowid')
        if 'error' in reply or detail.get('season')!=season or type(show) is not int or show<=0:return None
        reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,
            method='VideoLibrary.GetTVShowDetails',params=dict(tvshowid=show,properties=['uniqueid'])))))
        detail=reply.get('result',{}).get('tvshowdetails',{})
        if 'error' in reply or detail.get('tvshowid')!=show:return None
        ids=hub.verified_ids(detail.get('uniqueid'))
    identity=hub.show_identity(kind,ids,season)
    key=hub.identity_key(identity)
    if not key:return None
    path=item.getPath()
    if not path.startswith(('plugin://','videodb://')):return None
    return dict(key=key,identity=identity,media='tv',title=tag.getTitle() or item.getLabel(),
        label=item.getLabel(),source=path,stable_source=path,season=season,episode=-1,dbid=-1,
        poster=item.getArt('poster') or item.getArt('thumb'),fanart=item.getArt('fanart'),**ids)


def set_membership(data, entry, action):
    """Explicit, idempotent actions on one independent local list."""
    operations={'add-watchlist':('watchlist',True),'remove-watchlist':('watchlist',False),
                'add-collection':('collection',True),'remove-collection':('collection',False),
                'save-later':('later',True),'remove-later':('later',False)}
    if action not in operations:return None
    bucket,add=operations[action];key=entry['key']
    if add:
        if key in data[bucket]:return False
        data[bucket][key]=hub._stamp(entry,'added_at')
    else:
        if key not in data[bucket]:return False
        del data[bucket][key]
    return True


def apply_local(profile, snapshot, action):
    identity=hub.entry_identity(snapshot)
    if not identity or not hub.KEY_RE.fullmatch(snapshot.get('key','')):return False
    with persistence_scope():
        data=hub.load(profile);key=hub.compatible_key(data,snapshot)
        saved=hub.find_entry(data,key)
        if saved and not hub.same_identity(identity,hub.entry_identity(saved)):return False
        entry=dict(saved or snapshot,key=key)
        changed=set_membership(data,entry,action)
        if changed is None and identity['kind'] in ('tvshow','season'):
            # These are local show/season states; never manufacture episode
            # records or synchronize a provider/library database from them.
            if action=='mark-watched':data,result=hub.mark_watched_data(data,key,entry);changed=result is not None
            elif action=='mark-unwatched':data,result=hub.mark_unwatched_data(data,key);changed=result is not None
        if changed:hub.save(profile,data,hub.publish_home)
    return bool(changed)


def show(entry, profile=None, bridge=None, modules=None):
    if xbmc.getSkinDir()!='skin.infinity.diggz' or not hub.entry_identity(entry):return False
    profile=profile or addon_profile()
    snapshot=dict(entry)
    native_watched=bool(snapshot.pop('_native_watched',False))
    home=xbmcgui.Window(10000);home.setProperty('Infinity.Select.Compact','true')
    try:pick=xbmcgui.Dialog().select('Infinity Trakt',[label for label,_ in ACTIONS])
    finally:home.clearProperty('Infinity.Select.Compact')
    if not 0<=pick<len(ACTIONS):return False
    action=ACTIONS[pick][1]
    if snapshot['identity']['kind'] in ('movie','episode'):
        bridge,modules=(bridge,modules) if bridge is not None else _bridge()
        # Reuse all producer proof, selected-state and pending-sync safeguards.
        data=hub.load_view(profile);key=hub.compatible_key(data,snapshot)
        query=bridge.contracts.canonical(snapshot,bridge.identity(snapshot),snapshot.get(bridge.contracts.ENTRY_PROOF))
        local=bridge.lookup(bridge.records(data),query)
        watched=local=='true' or (native_watched and local!='false')
        if action in ('mark-watched','mark-unwatched') and (action=='mark-watched')==watched:return False
        intent=bridge.menu_intent(data,key,local,watched)
        changed=bridge.controller.apply(modules,profile,snapshot,action,intent=intent)
    else:
        changed=apply_local(profile,snapshot,action)
    if changed:xbmc.executebuiltin('Container.Refresh')
    return changed


def show_saved(key):
    if not hub.KEY_RE.fullmatch(key):return False
    entry=hub.find_entry(hub.load_view(addon_profile()),key)
    return show(entry) if entry else False


def main(item=None):
    if xbmc.getSkinDir()!='skin.infinity.diggz':return
    try:
        bridge,modules=_bridge();entry=selected(item or getattr(sys,'listitem',None),bridge,modules)
        if not entry:
            xbmcgui.Dialog().ok('Infinity Trakt','This row has no supported verified movie, show or episode identity. Its provider actions and saved data were retained.')
            return
        entry['_native_watched']=bool(getattr(item or getattr(sys,'listitem',None),'getVideoInfoTag')().getPlayCount()>0)
        show(entry,bridge=bridge,modules=modules)
    except (OSError,ValueError,RuntimeError,AttributeError) as error:
        xbmcgui.Dialog().ok('Infinity Trakt',str(error))
