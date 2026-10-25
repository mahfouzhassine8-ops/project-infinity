from pathlib import Path
from textwrap import dedent
import hashlib
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--work',type=Path,required=True)
args=parser.parse_args()
P=args.work
cc=P/'script.infinity.commandcenter'
context=(cc/'context.py').read_text(encoding='utf-8')
plugin=(cc/'plugin.py').read_text(encoding='utf-8')
ctx_old_sha='6b22050d7e6c0c320d18e34370b9fd48261f982b181899702e3a7f65b9b0e319'
plugin_old_sha='380dc998e10419b957337a7337719808ada2c946657b3953a63e81ab18f60c84'
assert hashlib.sha256(context.encode()).hexdigest()==ctx_old_sha
assert hashlib.sha256(plugin.encode()).hexdigest()==plugin_old_sha

def replace_exact(text,old,new):
    assert text.count(old)==1, (repr(old[:130]),text.count(old))
    res=text.replace(old,new,1)
    assert res.replace(new,old,1)==text
    return res

helper='''def _watchnixtoons_exact_previous(item, route, kind):
    """Reuse ONLY a prior verified identity bound to this exact provider route.

    Never infer from a title, season label, poster or another add-on's route.
    Conflicting stored identities require fresh, user-confirmed verification.
    Read-only: neither this lookup nor holding the menu changes saved data.
    """
    data=hub.load_view(addon_profile())
    matches=[]
    media='movie' if kind=='movie' else 'tv'
    for bucket in ('items','watched','watchlist','collection','later'):
        for row in data.get(bucket,{}).values():
            if not isinstance(row,dict) or row.get('source')!=route or row.get('stable_source')!=route:
                continue
            identity=hub.entry_identity(row)
            if not identity or row.get('media')!=media or identity['kind']!=kind:
                continue
            if kind in ('season','episode') and (hub.episode_number(row.get('season')) !=
                                                  hub.episode_number(item.getVideoInfoTag().getSeason())):
                continue
            if kind=='episode' and (hub.episode_number(row.get('episode')) !=
                                    hub.episode_number(item.getVideoInfoTag().getEpisode())):
                continue
            matches.append((row,identity))
    if not matches or not all(hub.same_identity(matches[0][1], ident) for _,ident in matches):
        return None
    row=dict(matches[0][0])
    row['key']=hub.identity_key(matches[0][1])
    row['title']=str(item.getVideoInfoTag().getTitle() or item.getLabel())
    row['label']=str(item.getLabel())
    row['poster']=item.getArt('poster') or item.getArt('thumb')
    row['fanart']=item.getArt('fanart')
    row['_native_watched']=item.getVideoInfoTag().getPlayCount()>0
    return row if hub.entry_identity(row) else None


def _watchnixtoons_confirmed_entry(item,route,kind,title):
    """Get typed ID from a pin-verified Search provider after explicit user consent.

    Only the same first-party Search inventory/route and native lease are used.
    One eligible provider at a time, never provider edits or title guessing.
    User selection + confirmation is mandatory. No mapping is saved here.
    """
    from infinity_search import providers, _provider_result, _Cancellation
    from infinity_settings import choose
    media='movie' if kind=='movie' else 'tv'
    search=xbmcgui.Dialog().input('Find the verified title for WatchNixtoons2',title[:160]).strip()
    if not search or len(search)>160 or any(ord(ch)<32 for ch in search):
        return None
    ready,_=providers(media,force=True)
    # Nixtoons itself supplies no trusted cross-provider unique IDs here.
    # Keep the published search capability and component hash/lease checks.
    ready=[p for p in ready if p.get('id')!='plugin.video.watchnixtoons2' and
           isinstance(p.get('id'),str) and isinstance(p.get('contract'),dict)]
    if not ready:
        xbmcgui.Dialog().ok('Infinity Trakt','No verified metadata provider is available. No tracking record was changed.')
        return None
    which=choose('Choose verified metadata provider',[p['name'] for p in ready])
    if not isinstance(which,int) or not 0<=which<len(ready):return None
    provider=ready[which]
    home=xbmcgui.Window(10000)
    progress=xbmcgui.DialogProgress()
    progress.create('Infinity Trakt','Checking verified media IDs')
    cancel=_Cancellation()
    try:
        found,status,result,_=_provider_result(provider,search,home,cancel)
    finally:
        cancel.cancel();progress.close()
    if found['id']!=provider['id'] or status!='completed' or 'error' in result:
        xbmcgui.Dialog().ok('Infinity Trakt','The metadata provider could not confirm a result. No records were changed.')
        return None
    rows=result.get('result',{}).get('files',[])
    if not isinstance(rows,list):return None
    candidates=[]
    for row in rows[:40]:
        if not isinstance(row,dict) or row.get('type')!=('movie' if media=='movie' else 'tvshow'):
            continue
        origin=row.get('file','')
        if not isinstance(origin,str) or not origin.startswith('plugin://'+provider['id']+'/'):
            continue
        ids=hub.verified_ids(row.get('uniqueid'))
        if not ids:continue
        if kind=='movie':identity=hub.media_identity('movie',ids)
        elif kind=='episode':identity=hub.media_identity('tv',{},item.getVideoInfoTag().getSeason(),
                              item.getVideoInfoTag().getEpisode(),show_ids=ids)
        else:identity=hub.show_identity(kind,ids,item.getVideoInfoTag().getSeason())
        if not identity or not hub.identity_key(identity):continue
        name=row.get('title') or row.get('label')
        if not isinstance(name,str) or not name.strip() or len(name)>512:continue
        year=row.get('year')
        year=str(year) if type(year) is int and 1900<=year<=2100 else 'Year unknown'
        idhint=', '.join(n.upper()+':'+v for n,v in ids.items())
        candidates.append((name,year,idhint,identity,ids))
    if not candidates:
        xbmcgui.Dialog().ok('Infinity Trakt','This provider returned no verified IDs for the selected media type. Saved records were not changed.')
        return None
    which=choose('Confirm the exact title',[
        name+' ('+year+') — '+idhint for name,year,idhint,_,_ in candidates])
    if not isinstance(which,int) or not 0<=which<len(candidates):return None
    name,year,idhint,identity,ids=candidates[which]
    # The user must explicitly confirm this source record. The provider title
    # need not match the source label (dub/localization/spin-offs differ).
    if not xbmcgui.Dialog().yesno('Verify WatchNixtoons2 identity',
            'Source: '+title[:150]+'\\nVerified: '+name[:150]+' ('+year+')\\n'+idhint[:150]+
            '\\nUse this verified identity for the selected action?'):
        return None
    if item.getPath()!=route or item.getVideoInfoTag().getMediaType()!=kind:return None
    key=hub.identity_key(identity)
    tag=item.getVideoInfoTag()
    entry=dict(key=key,identity=identity,media=media,title=title,label=item.getLabel(),
        source=route,stable_source=route,season=hub.episode_number(tag.getSeason()) if kind in ('season','episode') else -1,
        episode=hub.episode_number(tag.getEpisode()) if kind=='episode' else -1,dbid=-1,
        poster=item.getArt('poster') or item.getArt('thumb'),fanart=item.getArt('fanart'),
        _native_watched=tag.getPlayCount()>0,**ids)
    return entry if hub.entry_identity(entry) and entry['key']==hub.identity_key(hub.entry_identity(entry)) else None


def _watchnixtoons_tracking(item,route,kind,title,label,op):
    # Identity stays independent of the Nixtoons provider URI; the original
    # URI is retained only for play/open after a user-verified typed-ID link.
    entry=_watchnixtoons_exact_previous(item,route,kind)
    if entry is None:entry=_watchnixtoons_confirmed_entry(item,route,kind,title)
    if entry is None:return False
    if item.getPath()!=route or item.getVideoInfoTag().getMediaType()!=kind:return False
    return _popup_module().show_item_menu(entry['key'],bucket='',incoming=entry,
                                         nixtoons_confirmed_row=(label,op,''))


'''
anchor='def _unverified_anime_menu(item):\n'
context=replace_exact(context,anchor,helper+anchor)
old='''    rows=[('Open in '+sources[parsed.netloc],'open'),
          ('Information','information')]
    if favourite is not None:
        rows.append(('Remove from Favourites' if favourite else 'Add to Favourites','favourite'))
'''
new='''    if parsed.netloc=='plugin.video.watchnixtoons2':
        # Exactly one exception to the otherwise frozen anime fallback:
        # show the SAME applicable tracking choices as the universal menu.
        # No identity-dependent action can run until verified explicitly.
        linked=_watchnixtoons_exact_previous(item,route,kind)
        if linked is not None:
            return _popup_module().show_item_menu(linked['key'],bucket='',incoming=linked)
        rows=[('Open in WatchNixtoons2','open'),('Mark Watched','track:mark-watched'),
              ('Add to Watchlist','track:toggle-watchlist')]
        if favourite is not None:
            rows.append(('Remove from Favourites' if favourite else 'Add to Favourites','favourite'))
        rows.extend([('Add to Collection','track:toggle-collection'),
                     ('Add to Custom List','track:add-list'),
                     ('Save for Later','track:save-later'),('Information','information')])
    else:
        rows=[('Open in '+sources[parsed.netloc],'open'),
              ('Information','information')]
        if favourite is not None:
            rows.append(('Remove from Favourites' if favourite else 'Add to Favourites','favourite'))
'''
context=replace_exact(context,old,new)
old2='''    action=rows[selected][1]
    if action=='information':
'''
new2='''    action=rows[selected][1]
    if parsed.netloc=='plugin.video.watchnixtoons2' and action.startswith('track:'):
        return _watchnixtoons_tracking(item,route,kind,title,rows[selected][0],action[6:])
    if action=='information':
'''
context=replace_exact(context,old2,new2)

anchor2="def show_item_menu(key, bucket='continue', list_name='', incoming=None, expected_selection=''):"
new2="def show_item_menu(key, bucket='continue', list_name='', incoming=None, expected_selection='', nixtoons_confirmed_row=None):"
plugin=replace_exact(plugin,anchor2,new2)
old3="""    from infinity_settings import choose
    selected = choose(str(original.get('label') or original.get('title') or 'Title'), [r[0] for r in rows])
    if not 0 <= selected < len(rows):
"""
new3="""    if nixtoons_confirmed_row is not None:
        # Scoped opt-in from the exact WatchNixtoons2 identity-confirmation UI.
        # All existing menu operations, locks and state rechecks stay intact.
        if (incoming is None or not incoming.get('source','').startswith('plugin://plugin.video.watchnixtoons2/')
                or incoming.get('source') != incoming.get('stable_source')
                or not hub.entry_identity(incoming)
                or not isinstance(nixtoons_confirmed_row, tuple)
                or len(nixtoons_confirmed_row)!=3):
            return False
        selected = next((i for i,r in enumerate(rows) if r==nixtoons_confirmed_row),-1)
        if selected<0:
            # Previously tracked in another provider: show real state, never reverse it.
            from infinity_settings import choose
            selected=choose(str(original.get('label') or original.get('title') or 'Title'),
                            [r[0] for r in rows])
    else:
        from infinity_settings import choose
        selected = choose(str(original.get('label') or original.get('title') or 'Title'), [r[0] for r in rows])
    if not 0 <= selected < len(rows):
"""
plugin=replace_exact(plugin,old3,new3)
for name,data in [('context.py',context),('plugin.py',plugin)]:
    compile(data,name,'exec')
    dest=P/'patched'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(data,encoding='utf-8')
    before=(cc/name).read_bytes()
    print(name,'OLD',hashlib.sha256(before).hexdigest(),'NEW',hashlib.sha256(dest.read_bytes()).hexdigest(),'SIZE',len(before),'NEW_SIZE',dest.stat().st_size)
