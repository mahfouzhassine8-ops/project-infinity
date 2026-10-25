"""Exact 2103402 source-only repair: provider hold menu and three UI Repair pins.

No source outside the three explicitly pinned component files is changed.
A title with no verified TMDb/IMDb/TVDb identity receives navigation/info/
favourites actions only; mutations to watched/Resume Hub remain gated.
"""
from pathlib import Path
from zipfile import ZipFile
from urllib.parse import urlsplit
import hashlib
import json

CC = 'script.infinity.commandcenter/'
UR = 'script.infinity.uirepair/'
WB = 'script.infinity.watchedbridge/'
CONTEXT = CC+'context.py'
PINS = [UR+'CONTROLLER-PREIMAGES.json',WB+'CONTROLLER-PREIMAGES.json']
PINNED = {
 CONTEXT:'b0bcd0f64b7883b1d05878ac23eafe439b7aa3b397e60453bf5f8dcfddbfa2bb',
 PINS[0]:'56e743fe9683d7b650c5cc9d2bad0b33e4c16d51a295c542ca3c1cdc646a707e',
 PINS[1]:'96c4f714b19f42bca935194adf5949b0f3f6d93db3a24c419a3e553612251be9',
}
UI_OLD = {'information.py':'c388b83353bff8e7687a545d3a00ea16691a208bd34b3a0a0678ff6441abb54e',
 'resources/skins/Default/1080i/InfinityInformation.xml':'bcfae57fcacc96a799e67f0c80cdfc22919a4a39fcb7f8ef9876eabf02f3a1e7',
 'service.py':'ca9233507680c5d013468a38d4996bb54389ebe4d3e2410df8c241dd8340f6c5'}
PREFIX = 'assets/addons/'
def sha(v): return hashlib.sha256(v).hexdigest()

def once(s, old, new, why):
    if s.count(old)!=1: raise ValueError('Unexpected exact source for '+why)
    after=s.replace(old,new,1)
    if after.replace(new,old,1)!=s: raise ValueError('Unauthorized change: '+why)
    return after

HELPERS = r'''def _unverified_anime_menu(item):
    """Never invent a media identity. Provider paths remain exact."""
    import json
    from urllib.parse import urlsplit
    from title_metadata import capture
    from infinity_settings import choose
    route = item.getPath()
    if not isinstance(route, str) or len(route)>8192 or any(ord(c)<32 for c in route):
        return False
    parsed=urlsplit(route)
    sources={'plugin.video.otaku':'Otaku',
             'plugin.video.watchnixtoons2':'WatchNixtoons2'}
    if parsed.scheme!='plugin' or parsed.netloc not in sources or not route.startswith('plugin://'+parsed.netloc+'/'):
        return False
    tag=item.getVideoInfoTag()
    kind=tag.getMediaType()
    if kind not in ('movie','tvshow','episode','season'):
        return False
    title=str(tag.getTitle() or item.getLabel() or '').strip()
    if not title or len(title)>512 or any(ord(c)<32 for c in title):
        return False
    folder=bool(item.isFolder()) or kind in ('tvshow','season')
    spec={'title':title,'type':'window' if folder else 'media'}
    if folder: spec.update(window='videos',windowparameter=route)
    else: spec['path']=route
    art=item.getArt('poster') or item.getArt('thumb')
    if isinstance(art,str) and 0<len(art)<=2048: spec['thumbnail']=art

    def rpc(name,params):
        result=json.loads(xbmc.executeJSONRPC(json.dumps({
            'jsonrpc':'2.0','id':1,'method':name,'params':params})))
        if not isinstance(result,dict) or 'error' in result:
            raise RuntimeError('Kodi refused the selected original-item action')
        return result.get('result') or {}

    def existing_favourite():
        saved=rpc('Favourites.GetFavourites',
                  {'properties':['path','window','windowparameter','thumbnail']}).get('favourites',[])
        if not isinstance(saved,list): return None
        matches=[row for row in saved if isinstance(row,dict) and
                 row.get('type')==spec['type'] and
                 (row.get('windowparameter')==route and
                  str(row.get('window','')).lower() in ('videos','10025')
                  if folder else row.get('path')==route)]
        return bool(matches) if len(matches)<=1 else None

    try: favourite=existing_favourite()
    except (RuntimeError,ValueError,TypeError): favourite=None
    rows=[('Open in '+sources[parsed.netloc],'open'),
          ('Information','information')]
    if favourite is not None:
        rows.append(('Remove from Favourites' if favourite else 'Add to Favourites','favourite'))
    selected=choose(title,[label for label,_ in rows])
    if not isinstance(selected,int) or not 0<=selected<len(rows):
        return False
    if item.getPath()!=route or item.getVideoInfoTag().getMediaType()!=kind:
        return False
    action=rows[selected][1]
    if action=='information':
        from information import show_information
        record={'title':title,'label':title,
                'poster':art if isinstance(art,str) else '',
                'information':capture(item)}
        show_information(item,record,play_available=False)
        return True
    if action=='favourite':
        if existing_favourite()!=favourite: return False
        rpc('Favourites.AddFavourite',spec)
        return True
    if folder:
        rpc('GUI.ActivateWindow',{'window':'videos','parameters':[route,'return']})
    else:
        xbmc.Player().play(route,item)
    return True


'''

def change_context(original):
    if sha(original)!=PINNED[CONTEXT]:
        raise ValueError('Exact accepted CC03535 context.py required')
    text=original.decode('utf-8')
    declaration='def title_popup(item):\n    """Native exact-item handoff for Infinity\'s Movie/TV title holds only."""'
    text=once(text,declaration,HELPERS+declaration,'helper insertion')
    old="""        bridge, modules = _bridge()
        if item.getVideoInfoTag().getMediaType() not in ('movie', 'tvshow', 'episode', 'season'):
            return False
        candidate = item
"""
    new="""        if item.getVideoInfoTag().getMediaType() not in ('movie', 'tvshow', 'episode', 'season'):
            return False
        path = item.getPath()
        anime = isinstance(path,str) and path.startswith(
            ('plugin://plugin.video.otaku/','plugin://plugin.video.watchnixtoons2/'))
        if anime:
            tag = item.getVideoInfoTag()
            ids=hub.verified_ids({n:tag.getUniqueID(n) for n in ('tmdb','imdb','tvdb')})
            if not ids:
                return _unverified_anime_menu(item)
        bridge, modules = _bridge()
        candidate = item
"""
    text=once(text,old,new,'identity independent menu')
    old="""        entry = selected(candidate, bridge, modules)
        if not entry:
            notice('This title has no supported verified media identity. Its records were retained.')
            return False
"""
    new="""        entry = selected(candidate, bridge, modules)
        if not entry:
            if anime:
                return _unverified_anime_menu(item)
            notice('This title has no supported verified media identity. Its records were retained.')
            return False
"""
    text=once(text,old,new,'unsupported identity fallback')
    compile(text,CONTEXT,'exec')
    return text.encode('utf-8')

def change_pins(original,owner,newcontext,ui):
    path=PINS[0] if ui else PINS[1]
    if sha(original)!=PINNED[path]: raise ValueError('Exact original verified pin file required: '+path)
    mapping=json.loads(original)
    if len(mapping)!=25 or mapping.get('context.py')!=PINNED[CONTEXT]:
        raise ValueError('Unexpected pin inventory')
    old_mismatches={name for name,pin in mapping.items()
                    if sha(owner.read(PREFIX+CC+name))!=pin}
    if old_mismatches != (set(UI_OLD) if ui else set()):
        raise ValueError('Unexpected mismatch beyond reviewed UI files: '+repr(old_mismatches))
    mapping['context.py']=sha(newcontext)
    if ui:
        for name,old in UI_OLD.items():
            if mapping[name]!=old: raise ValueError('Old UI hash changed '+name)
            mapping[name]=sha(owner.read(PREFIX+CC+name))
    for name,pin in mapping.items():
        raw=newcontext if name=='context.py' else owner.read(PREFIX+CC+name)
        if sha(raw)!=pin: raise ValueError('New pin mismatch: '+name)
    return (json.dumps(mapping,indent=2,ensure_ascii=False)+'\n').encode('utf-8')

def changes(apk):
    with ZipFile(apk) as archive:
        src=change_context(archive.read(PREFIX+CONTEXT))
        out={CONTEXT:src}
        for name in PINS:
            out[name]=change_pins(archive.read(PREFIX+name),archive,src,name==PINS[0])
        return out

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--apk',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists(): raise ValueError('Refusing to modify old overlay')
    entries=changes(a.apk)
    for name,raw in entries.items():
        path=a.output/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(raw)
    (a.output/'RECEIPT.json').write_text(json.dumps({
        'source_build':40153625864,
        'changed_files':{name:sha(blob) for name,blob in entries.items()},
        'ui_repair_pins':25,'watchedbridge_pins':25,
        'native_compatibility':'REQUIRES_MATCHING_BUILD',
        'Cobra':'UNCHANGED','saved_data':'UNTOUCHED'
    },indent=2)+'\n')
