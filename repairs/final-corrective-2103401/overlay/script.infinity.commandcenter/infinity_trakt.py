"""Infinity's local tracking menu; no external Trakt API or provider writes."""
from __future__ import annotations
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from common import addon_profile, persistence_scope
import resume_hub as hub

ACTIONS=(('Mark as Watched','mark-watched'),('Mark as Unwatched','mark-unwatched'),
         ('Add to Watchlist','add-watchlist'),('Remove from Watchlist','remove-watchlist'),
         ('Add to Collection','add-collection'),('Remove from Collection','remove-collection'),
         ('Save for Later','save-later'),('Remove from Save for Later','remove-later'))

# Filled from the exact release inputs, before the native controller contract is
# sealed. The reciprocal CC manifest is checked by controller.load, not pinned
# here (pinning reciprocal manifests would create an impossible hash cycle).
BRIDGE_PINS = {}


def _verified_component(addon, aid, version):
    raw_root=Path(xbmcvfs.translatePath(addon.getAddonInfo('path'))).absolute()
    root=raw_root.resolve()
    if root!=raw_root or not root.is_dir() or addon.getAddonInfo('id')!=aid:
        raise RuntimeError('The installed tracking component identity could not be verified.')
    manifest=root/'addon.xml'
    if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size>131072:
        raise RuntimeError('The tracking component manifest could not be verified.')
    node=ET.fromstring(manifest.read_bytes())
    if node.get('id')!=aid or node.get('version')!=version or addon.getAddonInfo('version')!=version:
        raise RuntimeError('Install the matching Infinity tracking components for this release.')
    return root


def _bridge():
    addon=xbmcaddon.Addon('script.infinity.watchedbridge')
    root=_verified_component(addon,'script.infinity.watchedbridge','1.0.10')
    if not BRIDGE_PINS:raise RuntimeError('The release tracking contract is missing.')
    for name,pin in BRIDGE_PINS.items():
        path=root/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>1048576 or hashlib.sha256(path.read_bytes()).hexdigest()!=pin:
            raise RuntimeError('The installed Watched Bridge differs from the verified release.')
    for name in ('controller','bridge_state','provider_contracts'):
        loaded=sys.modules.get(name)
        if loaded is not None and Path(getattr(loaded,'__file__','')).resolve()!=root/(name+'.py'):
            raise RuntimeError('A conflicting tracking module is loaded. No saved data was changed.')
    previous=list(sys.path)
    try:
        sys.path.insert(0,str(root))
        spec=importlib.util.spec_from_file_location('_infinity_verified_watched_context',root/'context.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    finally:sys.path[:]=previous
    for name in ('controller','bridge_state','provider_contracts'):
        if Path(getattr(sys.modules.get(name),'__file__','')).resolve()!=root/(name+'.py'):
            raise RuntimeError('The effective tracking module path is not the verified component.')
    cc=xbmcaddon.Addon('script.infinity.commandcenter')
    ccroot=_verified_component(cc,'script.infinity.commandcenter','0.3.5.29')
    if Path(__file__).resolve()!=ccroot/'infinity_trakt.py' or Path(hub.__file__).resolve()!=ccroot/'resume_hub.py':
        raise RuntimeError('A conflicting Infinity controller is loaded. No saved data was changed.')
    previous=list(sys.path)
    try:modules=module.controller.load(str(ccroot))
    finally:sys.path[:]=previous
    return module,modules


def notice(message,title='Infinity Trakt'):
    """A bounded Infinity-owned compatibility notice; other dialogs stay intact."""
    root=Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.commandcenter').getAddonInfo('path')))
    class Notice(xbmcgui.WindowXMLDialog):
        def onInit(self):
            bg=self.getControl(2);card=self.getControl(100)
            w=min(760,max(280,bg.getWidth()-48));h=min(340,max(200,bg.getHeight()-48))
            card.setPosition((bg.getWidth()-w)//2,(bg.getHeight()-h)//2)
            for ident in (110,111):self.getControl(ident).setWidth(w);self.getControl(ident).setHeight(h)
            self.getControl(10).setWidth(w-100);self.getControl(10).setLabel(title)
            body=self.getControl(11);body.setWidth(w-48);body.setHeight(h-112);body.setText(message)
            close=self.getControl(9);close.setPosition(w-66,14)
            self.setFocusId(9)
        def onClick(self,ident):
            if ident in (2,9):self.close()
        def onAction(self,action):
            if action.getId() in (10,92,110):self.close()
    window=Notice('InfinityTraktNotice.xml',str(root),'Default','1080i')
    try:window.doModal()
    finally:window.close()


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
        source=Path(profile)/hub.CONTINUE_FILE
        if source.exists():
            if source.stat().st_size>8*1024*1024:raise RuntimeError('The local tracking file exceeds the reviewed limit.')
            try:original=json.loads(source.read_text(encoding='utf-8'))
            except (OSError,ValueError):raise RuntimeError('The local tracking file could not be read. Its data was retained.')
            if not isinstance(original,dict) or type(original.get('schema')) is not int or original['schema'] not in (1,2):
                raise RuntimeError('The existing local schema is unsupported. Its data was retained.')
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
    from infinity_settings import choose
    pick=choose('Infinity Trakt',[label for label,_ in ACTIONS])
    if not 0<=pick<len(ACTIONS):return False
    action=ACTIONS[pick][1]
    if snapshot['identity']['kind'] in ('movie','episode'):
        bridge,modules=(bridge,modules) if bridge is not None else _bridge()
        producer=bridge.contracts.provider(snapshot)
        if snapshot['identity']['kind']=='episode' and producer:
            owner=xbmcaddon.Addon(producer)
            proof=bridge.contracts.verify(producer,xbmcvfs.translatePath(owner.getAddonInfo('path')))
            if not proof:raise RuntimeError('This saved episode producer cannot confirm its identity contract. Its records were retained.')
            snapshot[bridge.contracts.ENTRY_PROOF]=proof
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
            notice('This row has no supported verified movie, show, season or episode identity. Its saved data was retained.')
            return
        entry['_native_watched']=bool(getattr(item or getattr(sys,'listitem',None),'getVideoInfoTag')().getPlayCount()>0)
        show(entry,bridge=bridge,modules=modules)
    except (OSError,ValueError,RuntimeError,AttributeError,ET.ParseError) as error:
        notice(str(error))
