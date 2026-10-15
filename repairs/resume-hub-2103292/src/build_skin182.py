#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, re, shutil, zipfile
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat

EXPECTED_PARENT='330d539c7591d0ebbf8a2d435efac38e74236d677183224ab3b1659caf5a917b'
VERSION='1.0.5.182'
COMMAND_VERSION='0.3.5.19'
OUT_NAME='Infinity-1.0.5.182-Resume-Hub-2-2103291-Reflow-Repair-RC2.zip'
HOME_DIRS=('16x9','20x9','6x5','5x6','portrait','fallback',
           'responsive/base','responsive/wide','responsive/ultrawide','responsive/landscape',
           'responsive/square','responsive/portrait','responsive/tall')
INCLUDE_DIRS=('16x9','fallback','responsive/base','responsive/wide','responsive/ultrawide',
              'responsive/landscape','responsive/square','responsive/portrait','responsive/tall')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# 2103291 keeps the live control tree and re-evaluates authored XML geometry in place.
# Positive root/include/default/definition positions must therefore remain parent-relative.
# Rewrite only those values, preserving every other XML byte.
REFLOW_POS={'left','top','right','bottom','posx','posy','centerleft','centerright','centertop','centerbottom'}
REFLOW_PARENTS={'coordinates','include','default','definition'}
REFLOW_H={'left','right','posx','centerleft','centerright','x'}
REFLOW_NUM=re.compile(r'^\\s*(-?\\d+(?:\\.\\d+)?)\\s*
def patch_home(text:str)->str:
    if '<label>INFINITY MOVIES</label>' in text:
        raise RuntimeError('Parent already contains Infinity Movies')
    # Disambiguate Trakt vs local items while reusing the exact same approved widget controls.
    trakt_movies='''          <item>\n            <label>TRAKT MOVIES</label>\n            <property name="section">traktmovies</property>\n            <property name="submenuVisibility">traktmovies</property>\n            <property name="widgetName">Umbrella - Trakt Watchlist</property>\n            <property name="widgetName.2">Umbrella - Collection</property>\n            <onclick>ActivateWindow(Videos,"plugin://plugin.video.umbrella/?action=mymovieNavigator&amp;folderName=My+Movies",return)</onclick>\n            <icon>infinity_ui/icons/trakt.png</icon>\n          </item>'''
    trakt_movies_new=trakt_movies.replace('<property name="submenuVisibility">traktmovies</property>', '<property name="submenuVisibility">traktmovies</property>\n            <property name="hubsource">trakt</property>')
    if text.count(trakt_movies)!=1: raise RuntimeError('Unexpected Trakt Movies menu anchor')
    text=text.replace(trakt_movies,trakt_movies_new,1)
    trakt_tv='''          <item>\n            <label>TRAKT TV</label>\n            <property name="section">trakttv</property>\n            <property name="submenuVisibility">trakttv</property>\n            <property name="widgetName">Umbrella - Next Episodes</property>\n            <property name="widgetName.2">Umbrella - Progress Shows</property>\n            <onclick>ActivateWindow(Videos,"plugin://plugin.video.umbrella/?action=mytvNavigator&amp;folderName=My+TV+Shows",return)</onclick>\n            <icon>infinity_ui/icons/trakt.png</icon>\n          </item>'''
    infinity='''          <item>\n            <label>INFINITY MOVIES</label>\n            <property name="section">traktmovies</property>\n            <property name="submenuVisibility">infinitymovies</property>\n            <property name="hubsource">infinity</property>\n            <property name="widgetName">Infinity - Watchlist</property>\n            <property name="widgetName.2">Infinity - Collection</property>\n            <onclick>ActivateWindow(Videos,"plugin://script.infinity.commandcenter/?action=movies",return)</onclick>\n            <icon>infinity_ui/icons/movie.png</icon>\n          </item>\n          <item>\n            <label>INFINITY TV</label>\n            <property name="section">trakttv</property>\n            <property name="submenuVisibility">infinitytv</property>\n            <property name="hubsource">infinity</property>\n            <property name="widgetName">Infinity - Next Episodes</property>\n            <property name="widgetName.2">Infinity - Progress Shows</property>\n            <onclick>ActivateWindow(Videos,"plugin://script.infinity.commandcenter/?action=tv",return)</onclick>\n            <icon>infinity_ui/icons/tv.png</icon>\n          </item>'''
    trakt_tv_new=trakt_tv.replace('<property name="submenuVisibility">trakttv</property>', '<property name="submenuVisibility">trakttv</property>\n            <property name="hubsource">trakt</property>')
    if text.count(trakt_tv)!=1: raise RuntimeError('Unexpected Trakt TV menu anchor')
    text=text.replace(trakt_tv,trakt_tv_new+'\n'+infinity,1)

    # Two nav-card current-section accents must compare hubsource too, otherwise Trakt and Infinity
    # cards would both look selected because they intentionally share the same proven widget section.
    old='String.IsEqual(ListItem.Property(section),Container(9000).ListItem.Property(section))'
    new='[String.IsEqual(ListItem.Property(section),Container(9000).ListItem.Property(section)) + String.IsEqual(ListItem.Property(hubsource),Container(9000).ListItem.Property(hubsource))]'
    if text.count(old)<2: raise RuntimeError('Missing nav selected-state anchors')
    text=text.replace(old,new)

    path_vars={
      'traktwatchlist':'InfinityMoviesPrimaryPath',
      'traktcollection':'InfinityMoviesSecondaryPath',
      'url=progress':'InfinityTVPrimaryPath',
      'progresstv':'InfinityTVSecondaryPath',
    }
    lines=[]
    for line in text.splitlines():
        stripped=line.strip()
        replaced=False
        if stripped.startswith('<content ') and 'plugin://plugin.video.umbrella/' in line:
            for marker,var in path_vars.items():
                if marker in line:
                    prefix=line[:line.index('>')+1]
                    suffix='</content>'
                    lines.append(prefix+'$VAR['+var+']'+suffix)
                    replaced=True; break
        if replaced: continue
        # Browse buttons keep existing Trakt path when Trakt is selected, and use local path when
        # the new Infinity item is selected. All focus/navigation IDs remain untouched.
        if stripped.startswith('<onclick condition=') and 'SetProperty(Infinity.BrowsePath,plugin://plugin.video.umbrella/' in line:
            mapping=None
            if 'traktwatchlist' in line: mapping=('traktmovies','InfinityMoviesPrimaryPath')
            elif 'traktcollection' in line: mapping=('traktmovies','InfinityMoviesSecondaryPath')
            elif 'url=progress' in line and 'calendar' in line: mapping=('trakttv','InfinityTVPrimaryPath')
            elif 'progresstv' in line: mapping=('trakttv','InfinityTVSecondaryPath')
            if mapping:
                section,var=mapping
                indent=line[:len(line)-len(line.lstrip())]
                # Tighten original condition to Trakt source.
                original=line.replace(f'String.IsEqual(Container(9000).ListItem.Property(section),{section})',
                    f'[String.IsEqual(Container(9000).ListItem.Property(section),{section}) + String.IsEqual(Container(9000).ListItem.Property(hubsource),trakt)]',1)
                local=(f'{indent}<onclick condition="[String.IsEqual(Container(9000).ListItem.Property(section),{section}) + '
                       f'String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)]">'
                       f'SetProperty(Infinity.BrowsePath,$VAR[{var}],Home)</onclick>')
                lines.extend([original,local]); continue
        lines.append(line)
    return '\n'.join(lines)+'\n'

VARIABLES='''\n  <!-- Infinity 1.0.5.182 / Resume Hub 2: Trakt and local Infinity sections reuse the same\n       approved view-mode geometry. Only their data source changes. -->\n  <variable name="InfinityMoviesPrimaryPath">\n    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=movie&amp;bucket=watchlist&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>\n    <value>plugin://plugin.video.umbrella/?action=movies&amp;url=traktwatchlist&amp;folderName=Trakt+Watchlist&amp;reload=$INFO[Window(Home).Property(widgetreload-movies)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>\n  </variable>\n  <variable name="InfinityMoviesSecondaryPath">\n    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=movie&amp;bucket=collection&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>\n    <value>plugin://plugin.video.umbrella/?action=movies&amp;url=traktcollection&amp;folderName=Collection&amp;reload=$INFO[Window(Home).Property(widgetreload-movies)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>\n  </variable>\n  <variable name="InfinityTVPrimaryPath">\n    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=tv&amp;bucket=next&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>\n    <value>plugin://plugin.video.umbrella/?action=calendar&amp;url=progress&amp;folderName=Progress+Episodes&amp;reload=$INFO[Window(Home).Property(widgetreload)]$INFO[Window(Home).Property(widgetreload2)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>\n  </variable>\n  <variable name="InfinityTVSecondaryPath">\n    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=tv&amp;bucket=progress&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>\n    <value>plugin://plugin.video.umbrella/?action=shows_progress&amp;url=progresstv&amp;folderName=Progress+Shows&amp;reload=$INFO[Window(Home).Property(widgetreload)]$INFO[Window(Home).Property(widgetreload2)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>\n  </variable>\n  <variable name="InfinityResumeHubWatchedState">\n    <value condition="String.IsEqual(ListItem.Property(Infinity.ResumeHub.Watched),true)">true</value>\n    <value condition="Integer.IsGreater(ListItem.PlayCount,0)">true</value>\n    <value>false</value>\n  </variable>\n'''

def patch_includes(text):
    if 'InfinityMoviesPrimaryPath' in text: raise RuntimeError('Parent already has Resume Hub 2 variables')
    marker='  <!-- Infinity 1.0.5.115: compact-only Continue Watching media card. -->'
    if marker in text:
        return text.replace(marker,VARIABLES+'\n'+marker,1)
    if '</includes>' not in text:
        raise RuntimeError('Missing unified include root close')
    return text.replace('</includes>',VARIABLES+'\n</includes>',1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--parent',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); parent=a.parent.resolve(); out=a.out_dir.resolve()
    if sha(parent)!=EXPECTED_PARENT: raise RuntimeError('Not exact locked Infinity skin 1.0.5.181 parent')
    if out.exists(): shutil.rmtree(out)
    root=out/'root'; root.mkdir(parents=True)
    with zipfile.ZipFile(parent) as z:
        if z.testzip() is not None: raise RuntimeError('Parent CRC failure')
        z.extractall(root)
    skin=root/'skin.infinity.diggz'
    changed=[]
    for d in HOME_DIRS:
        p=skin/d/'Home.xml'
        if not p.is_file(): continue
        before=p.read_bytes(); p.write_text(patch_home(before.decode('utf-8')),encoding='utf-8')
        if p.read_bytes()!=before: changed.append(p.relative_to(skin).as_posix())
    for d in INCLUDE_DIRS:
        p=skin/d/'Includes_InfinityHomeUnified.xml'
        if not p.is_file(): raise RuntimeError('Missing unified include: '+d)
        before=p.read_bytes(); p.write_text(patch_includes(before.decode('utf-8')),encoding='utf-8')
        if p.read_bytes()!=before: changed.append(p.relative_to(skin).as_posix())

    # Direct 2103291 responsive-reflow repair. The marker carries the original reference
    # canvas for every responsive class; use it to convert only root/include fragment positions.
    marker_data=json.loads((skin/'resources/infinity-native-responsive-v1.json').read_text())
    reflow_conversions=0
    reflow_files=[]
    for cls,meta in marker_data.get('classes',{}).items():
        ref_width,ref_height=meta['reference']
        for p in sorted((skin/'responsive'/cls).glob('*.xml')):
            before=p.read_bytes()
            count=normalize_2103291_reflow(p,ref_width,ref_height)
            if count:
                reflow_conversions+=count
                reflow_files.append(p.relative_to(skin).as_posix())
                if p.read_bytes()!=before and p.relative_to(skin).as_posix() not in changed:
                    changed.append(p.relative_to(skin).as_posix())
    if reflow_conversions != 843:
        raise RuntimeError(f'Expected 843 2103291 geometry conversions, got {reflow_conversions}')
    if len(reflow_files) != 233:
        raise RuntimeError(f'Expected 233 responsive XML repair files, got {len(reflow_files)}')

    addon=skin/'addon.xml'; text=addon.read_text()
    if 'version="1.0.5.181"' not in text: raise RuntimeError('Unexpected skin version')
    text=text.replace('version="1.0.5.181"',f'version="{VERSION}"',1)
    text=text.replace('addon="script.infinity.commandcenter" version="0.3.5.17"',f'addon="script.infinity.commandcenter" version="{COMMAND_VERSION}"',1)
    text=re.sub(r'(<description lang="en_GB">).*?(</description>)',
        r'\1Infinity Resume Hub 2 with 2103291 In-Place Responsive Reflow geometry repair. Local Infinity Movies/TV, watched history, Watchlist, Collection, ratings and lists use Command Center 0.3.5.19. Responsive root/include positions are class-relative; core player behavior, providers, light/dark presentation and native engine are preserved.\2',text,flags=re.S)
    addon.write_text(text); changed.append('addon.xml')

    release={'baseline':'1.0.5.181','title':'Infinity Resume Hub 2 + 2103291 Responsive Reflow Repair RC2','controller':COMMAND_VERSION,
             'requires_apk':2103292,'native_changed':False,'runtime_tested':False,
             'status':'device_acceptance_pending','scope':'Resume Hub 2 plus direct 2103291 in-place responsive-reflow geometry repair; core player behavior, providers, accounts and light/dark presentation preserved',
             'resume_hub_watched_contract':'Kodi playcount/overlay + Infinity.ResumeHub.Watched',
             'responsive_reflow_contract':'2103291 In-Place Responsive Reflow v1',
             'responsive_geometry_conversions':843}
    p=skin/'infinity-skin.json'; data=json.loads(p.read_text()); data['previous_release_metadata']=data.get('current_release'); data['current_release']=release
    data.update(candidate=182,candidate_name='Infinity Resume Hub 2 + 2103291 Responsive Reflow Repair RC2',skin_version=VERSION,resume_hub_api='2.0',responsive_reflow_contract='2103291 In-Place Responsive Reflow v1',responsive_reflow_geometry_repaired=True); p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n'); changed.append('infinity-skin.json')
    p=skin/'Infinity-Protected-Manifest.json'; data=json.loads(p.read_text()); data['previous_release_metadata']=data.get('current_release'); data['current_release']=release
    data.update(skin_version=VERSION,candidate='Infinity Resume Hub 2 1.0.5.182 + 2103291 Reflow Repair RC2',resume_hub_api='2.0',responsive_reflow_contract='2103291 In-Place Responsive Reflow v1',responsive_reflow_geometry_repaired=True)
    protected=data.get('protected_files',{})
    for rel in list(protected):
        f=skin/rel
        if f.is_file(): protected[rel]=hashlib.sha256(f.read_bytes()).hexdigest()
    for rel in changed:
        f=skin/rel
        if f.is_file(): protected[rel]=hashlib.sha256(f.read_bytes()).hexdigest()
    data['protected_files']=protected; p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n'); changed.append('Infinity-Protected-Manifest.json')

    # Parse every XML touched and verify the menu/data-source contract in every active responsive universe.
    for rel in changed:
        p=skin/rel
        if p.suffix=='.xml': ET.fromstring(p.read_bytes())
    for d in HOME_DIRS:
        p=skin/d/'Home.xml'
        if not p.is_file(): continue
        text=p.read_text()
        for token in ('<label>INFINITY MOVIES</label>','<label>INFINITY TV</label>','<property name="hubsource">infinity</property>'):
            if token not in text: raise RuntimeError(f'{d} missing {token}')
    for d in INCLUDE_DIRS:
        text=(skin/d/'Includes_InfinityHomeUnified.xml').read_text()
        for token in ('InfinityMoviesPrimaryPath','InfinityMoviesSecondaryPath','InfinityTVPrimaryPath','InfinityTVSecondaryPath','InfinityResumeHubWatchedState'):
            if token not in text: raise RuntimeError(f'{d} missing {token}')

    output=out/OUT_NAME
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(root).as_posix())
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None: raise RuntimeError('Output CRC failure')
    proof={'schema':1,'parent_sha256':EXPECTED_PARENT,'skin_version':VERSION,'controller_min':COMMAND_VERSION,
           'requires_apk':2103292,'candidate_sha256':sha(output),'native_changed':False,
           'home_profiles_changed':len([x for x in changed if x.endswith('/Home.xml')]),
           'unified_include_profiles_changed':len([x for x in changed if x.endswith('/Includes_InfinityHomeUnified.xml')]),
           'trakt_sections_preserved':True,'infinity_movies_tv_added':True,'core_player_behavior_surfaces_changed':False,
           'responsive_playercontrols_geometry_normalized':True,'responsive_reflow_contract':'2103291 In-Place Responsive Reflow v1',
           'responsive_geometry_conversions':reflow_conversions,'responsive_reflow_files_changed':len(reflow_files),
           'changed_files':changed,'physical_device_verified':False}
    (out/'SKIN-PROOF.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    print(output); print(proof['candidate_sha256'])
if __name__=='__main__': main()
)

def _reflow_pct(value, axis):
    text=f'{value/axis*100:.4f}'.rstrip('0').rstrip('.')
    if text in ('','-0'): text='0'
    return text+'%'

def _tag_end(data,start):
    quote=None
    for i in range(start,len(data)):
        ch=data[i]
        if quote is not None:
            if ch==quote: quote=None
        elif ch in (34,39):
            quote=ch
        elif ch==62:
            return i
    raise RuntimeError('unterminated XML tag')

def normalize_2103291_reflow(path, ref_width, ref_height):
    data=path.read_bytes()
    parser=expat.ParserCreate()
    stack=[]
    replacements=[]
    converted=0

    def axis(tag):
        return ref_width if tag in REFLOW_H else ref_height

    def start(name, attrs):
        nonlocal converted
        at=parser.CurrentByteIndex
        end=_tag_end(data,at)
        parent=stack[-1]['name'] if stack else None
        if name=='origin' and parent=='coordinates':
            raw=data[at:end+1].decode('utf-8')
            new=raw
            for attr,dim in (('x',ref_width),('y',ref_height)):
                rx=re.compile(r'(\\b'+attr+r'\\s*=\\s*["\\\'])(-?\\d+(?:\\.\\d+)?)(["\\\'])')
                def repl(match, dim=dim):
                    nonlocal converted
                    value=float(match.group(2))
                    if value < 0: return match.group(0)
                    converted+=1
                    return match.group(1)+_reflow_pct(value,dim)+match.group(3)
                new=rx.sub(repl,new)
            if new!=raw:
                replacements.append((at,end+1,new.encode('utf-8')))
        stack.append({'name':name,'content':end+1,'target':name in REFLOW_POS and parent in REFLOW_PARENTS})

    def end(name):
        nonlocal converted
        at=parser.CurrentByteIndex
        item=stack.pop()
        if not item['target']: return
        raw=data[item['content']:at].decode('utf-8')
        match=re.fullmatch(r'(\\s*)(-?\\d+(?:\\.\\d+)?)(\\s*)',raw)
        if not match: return
        value=float(match.group(2))
        if value < 0: return
        replacement=(match.group(1)+_reflow_pct(value,axis(name))+match.group(3)).encode('utf-8')
        if replacement!=data[item['content']:at]:
            converted+=1
            replacements.append((item['content'],at,replacement))

    parser.StartElementHandler=start
    parser.EndElementHandler=end
    parser.Parse(data,True)
    out=data
    for start_at,end_at,replacement in sorted(replacements,key=lambda x:x[0],reverse=True):
        out=out[:start_at]+replacement+out[end_at:]
    if out!=data:
        path.write_bytes(out)
    return converted

def patch_home(text:str)->str:
    if '<label>INFINITY MOVIES</label>' in text:
        raise RuntimeError('Parent already contains Infinity Movies')
    # Disambiguate Trakt vs local items while reusing the exact same approved widget controls.
    trakt_movies='''          <item>\n            <label>TRAKT MOVIES</label>\n            <property name="section">traktmovies</property>\n            <property name="submenuVisibility">traktmovies</property>\n            <property name="widgetName">Umbrella - Trakt Watchlist</property>\n            <property name="widgetName.2">Umbrella - Collection</property>\n            <onclick>ActivateWindow(Videos,"plugin://plugin.video.umbrella/?action=mymovieNavigator&amp;folderName=My+Movies",return)</onclick>\n            <icon>infinity_ui/icons/trakt.png</icon>\n          </item>'''
    trakt_movies_new=trakt_movies.replace('<property name="submenuVisibility">traktmovies</property>', '<property name="submenuVisibility">traktmovies</property>\n            <property name="hubsource">trakt</property>')
    if text.count(trakt_movies)!=1: raise RuntimeError('Unexpected Trakt Movies menu anchor')
    text=text.replace(trakt_movies,trakt_movies_new,1)
    trakt_tv='''          <item>\n            <label>TRAKT TV</label>\n            <property name="section">trakttv</property>\n            <property name="submenuVisibility">trakttv</property>\n            <property name="widgetName">Umbrella - Next Episodes</property>\n            <property name="widgetName.2">Umbrella - Progress Shows</property>\n            <onclick>ActivateWindow(Videos,"plugin://plugin.video.umbrella/?action=mytvNavigator&amp;folderName=My+TV+Shows",return)</onclick>\n            <icon>infinity_ui/icons/trakt.png</icon>\n          </item>'''
    infinity='''          <item>\n            <label>INFINITY MOVIES</label>\n            <property name="section">traktmovies</property>\n            <property name="submenuVisibility">infinitymovies</property>\n            <property name="hubsource">infinity</property>\n            <property name="widgetName">Infinity - Watchlist</property>\n            <property name="widgetName.2">Infinity - Collection</property>\n            <onclick>ActivateWindow(Videos,"plugin://script.infinity.commandcenter/?action=movies",return)</onclick>\n            <icon>infinity_ui/icons/movie.png</icon>\n          </item>\n          <item>\n            <label>INFINITY TV</label>\n            <property name="section">trakttv</property>\n            <property name="submenuVisibility">infinitytv</property>\n            <property name="hubsource">infinity</property>\n            <property name="widgetName">Infinity - Next Episodes</property>\n            <property name="widgetName.2">Infinity - Progress Shows</property>\n            <onclick>ActivateWindow(Videos,"plugin://script.infinity.commandcenter/?action=tv",return)</onclick>\n            <icon>infinity_ui/icons/tv.png</icon>\n          </item>'''
    trakt_tv_new=trakt_tv.replace('<property name="submenuVisibility">trakttv</property>', '<property name="submenuVisibility">trakttv</property>\n            <property name="hubsource">trakt</property>')
    if text.count(trakt_tv)!=1: raise RuntimeError('Unexpected Trakt TV menu anchor')
    text=text.replace(trakt_tv,trakt_tv_new+'\n'+infinity,1)

    # Two nav-card current-section accents must compare hubsource too, otherwise Trakt and Infinity
    # cards would both look selected because they intentionally share the same proven widget section.
    old='String.IsEqual(ListItem.Property(section),Container(9000).ListItem.Property(section))'
    new='[String.IsEqual(ListItem.Property(section),Container(9000).ListItem.Property(section)) + String.IsEqual(ListItem.Property(hubsource),Container(9000).ListItem.Property(hubsource))]'
    if text.count(old)<2: raise RuntimeError('Missing nav selected-state anchors')
    text=text.replace(old,new)

    path_vars={
      'traktwatchlist':'InfinityMoviesPrimaryPath',
      'traktcollection':'InfinityMoviesSecondaryPath',
      'url=progress':'InfinityTVPrimaryPath',
      'progresstv':'InfinityTVSecondaryPath',
    }
    lines=[]
    for line in text.splitlines():
        stripped=line.strip()
        replaced=False
        if stripped.startswith('<content ') and 'plugin://plugin.video.umbrella/' in line:
            for marker,var in path_vars.items():
                if marker in line:
                    prefix=line[:line.index('>')+1]
                    suffix='</content>'
                    lines.append(prefix+'$VAR['+var+']'+suffix)
                    replaced=True; break
        if replaced: continue
        # Browse buttons keep existing Trakt path when Trakt is selected, and use local path when
        # the new Infinity item is selected. All focus/navigation IDs remain untouched.
        if stripped.startswith('<onclick condition=') and 'SetProperty(Infinity.BrowsePath,plugin://plugin.video.umbrella/' in line:
            mapping=None
            if 'traktwatchlist' in line: mapping=('traktmovies','InfinityMoviesPrimaryPath')
            elif 'traktcollection' in line: mapping=('traktmovies','InfinityMoviesSecondaryPath')
            elif 'url=progress' in line and 'calendar' in line: mapping=('trakttv','InfinityTVPrimaryPath')
            elif 'progresstv' in line: mapping=('trakttv','InfinityTVSecondaryPath')
            if mapping:
                section,var=mapping
                indent=line[:len(line)-len(line.lstrip())]
                # Tighten original condition to Trakt source.
                original=line.replace(f'String.IsEqual(Container(9000).ListItem.Property(section),{section})',
                    f'[String.IsEqual(Container(9000).ListItem.Property(section),{section}) + String.IsEqual(Container(9000).ListItem.Property(hubsource),trakt)]',1)
                local=(f'{indent}<onclick condition="[String.IsEqual(Container(9000).ListItem.Property(section),{section}) + '
                       f'String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)]">'
                       f'SetProperty(Infinity.BrowsePath,$VAR[{var}],Home)</onclick>')
                lines.extend([original,local]); continue
        lines.append(line)
    return '\n'.join(lines)+'\n'

VARIABLES='''\n  <!-- Infinity 1.0.5.182 / Resume Hub 2: Trakt and local Infinity sections reuse the same\n       approved view-mode geometry. Only their data source changes. -->\n  <variable name="InfinityMoviesPrimaryPath">\n    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=movie&amp;bucket=watchlist&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>\n    <value>plugin://plugin.video.umbrella/?action=movies&amp;url=traktwatchlist&amp;folderName=Trakt+Watchlist&amp;reload=$INFO[Window(Home).Property(widgetreload-movies)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>\n  </variable>\n  <variable name="InfinityMoviesSecondaryPath">\n    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=movie&amp;bucket=collection&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>\n    <value>plugin://plugin.video.umbrella/?action=movies&amp;url=traktcollection&amp;folderName=Collection&amp;reload=$INFO[Window(Home).Property(widgetreload-movies)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>\n  </variable>\n  <variable name="InfinityTVPrimaryPath">\n    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=tv&amp;bucket=next&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>\n    <value>plugin://plugin.video.umbrella/?action=calendar&amp;url=progress&amp;folderName=Progress+Episodes&amp;reload=$INFO[Window(Home).Property(widgetreload)]$INFO[Window(Home).Property(widgetreload2)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>\n  </variable>\n  <variable name="InfinityTVSecondaryPath">\n    <value condition="String.IsEqual(Container(9000).ListItem.Property(hubsource),infinity)">plugin://script.infinity.commandcenter/?action=library&amp;media=tv&amp;bucket=progress&amp;rev=$INFO[Window(Home).Property(Infinity.ResumeHubRevision)]</value>\n    <value>plugin://plugin.video.umbrella/?action=shows_progress&amp;url=progresstv&amp;folderName=Progress+Shows&amp;reload=$INFO[Window(Home).Property(widgetreload)]$INFO[Window(Home).Property(widgetreload2)]$INFO[Window(Home).Property(Infinity.WidgetReloadRevision)]</value>\n  </variable>\n  <variable name="InfinityResumeHubWatchedState">\n    <value condition="String.IsEqual(ListItem.Property(Infinity.ResumeHub.Watched),true)">true</value>\n    <value condition="Integer.IsGreater(ListItem.PlayCount,0)">true</value>\n    <value>false</value>\n  </variable>\n'''

def patch_includes(text):
    if 'InfinityMoviesPrimaryPath' in text: raise RuntimeError('Parent already has Resume Hub 2 variables')
    marker='  <!-- Infinity 1.0.5.115: compact-only Continue Watching media card. -->'
    if marker in text:
        return text.replace(marker,VARIABLES+'\n'+marker,1)
    if '</includes>' not in text:
        raise RuntimeError('Missing unified include root close')
    return text.replace('</includes>',VARIABLES+'\n</includes>',1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--parent',type=Path,required=True); ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); parent=a.parent.resolve(); out=a.out_dir.resolve()
    if sha(parent)!=EXPECTED_PARENT: raise RuntimeError('Not exact locked Infinity skin 1.0.5.181 parent')
    if out.exists(): shutil.rmtree(out)
    root=out/'root'; root.mkdir(parents=True)
    with zipfile.ZipFile(parent) as z:
        if z.testzip() is not None: raise RuntimeError('Parent CRC failure')
        z.extractall(root)
    skin=root/'skin.infinity.diggz'
    changed=[]
    for d in HOME_DIRS:
        p=skin/d/'Home.xml'
        if not p.is_file(): continue
        before=p.read_bytes(); p.write_text(patch_home(before.decode('utf-8')),encoding='utf-8')
        if p.read_bytes()!=before: changed.append(p.relative_to(skin).as_posix())
    for d in INCLUDE_DIRS:
        p=skin/d/'Includes_InfinityHomeUnified.xml'
        if not p.is_file(): raise RuntimeError('Missing unified include: '+d)
        before=p.read_bytes(); p.write_text(patch_includes(before.decode('utf-8')),encoding='utf-8')
        if p.read_bytes()!=before: changed.append(p.relative_to(skin).as_posix())

    addon=skin/'addon.xml'; text=addon.read_text()
    if 'version="1.0.5.181"' not in text: raise RuntimeError('Unexpected skin version')
    text=text.replace('version="1.0.5.181"',f'version="{VERSION}"',1)
    text=text.replace('addon="script.infinity.commandcenter" version="0.3.5.17"',f'addon="script.infinity.commandcenter" version="{COMMAND_VERSION}"',1)
    text=re.sub(r'(<description lang="en_GB">).*?(</description>)',
        r'\1Infinity Resume Hub 2 adds local Infinity Movies and Infinity TV beside the preserved Trakt sections. Resume Hub owns watched history, Watchlist, Collection, ratings and lists through Command Center 0.3.5.19 while preserving the approved 1.0.5.181 responsive geometry and player surfaces.\2',text,flags=re.S)
    addon.write_text(text); changed.append('addon.xml')

    release={'baseline':'1.0.5.181','title':'Infinity Resume Hub 2 RC1','controller':COMMAND_VERSION,
             'requires_apk':2103292,'native_changed':False,'runtime_tested':False,
             'status':'device_acceptance_pending','scope':'Local Trakt-replacement menus/state plus watched/playcount skin bridge; existing responsive geometry and player surfaces preserved',
             'resume_hub_watched_contract':'Kodi playcount/overlay + Infinity.ResumeHub.Watched'}
    p=skin/'infinity-skin.json'; data=json.loads(p.read_text()); data['previous_release_metadata']=data.get('current_release'); data['current_release']=release
    data.update(candidate=182,candidate_name='Infinity Resume Hub 2 RC1',skin_version=VERSION,resume_hub_api='2.0'); p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n'); changed.append('infinity-skin.json')
    p=skin/'Infinity-Protected-Manifest.json'; data=json.loads(p.read_text()); data['previous_release_metadata']=data.get('current_release'); data['current_release']=release
    data.update(skin_version=VERSION,candidate='Infinity Resume Hub 2 1.0.5.182 RC1',resume_hub_api='2.0')
    protected=data.get('protected_files',{})
    for rel in list(protected):
        f=skin/rel
        if f.is_file(): protected[rel]=hashlib.sha256(f.read_bytes()).hexdigest()
    for rel in changed:
        f=skin/rel
        if f.is_file(): protected[rel]=hashlib.sha256(f.read_bytes()).hexdigest()
    data['protected_files']=protected; p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n'); changed.append('Infinity-Protected-Manifest.json')

    # Parse every XML touched and verify the menu/data-source contract in every active responsive universe.
    for rel in changed:
        p=skin/rel
        if p.suffix=='.xml': ET.fromstring(p.read_bytes())
    for d in HOME_DIRS:
        p=skin/d/'Home.xml'
        if not p.is_file(): continue
        text=p.read_text()
        for token in ('<label>INFINITY MOVIES</label>','<label>INFINITY TV</label>','<property name="hubsource">infinity</property>'):
            if token not in text: raise RuntimeError(f'{d} missing {token}')
    for d in INCLUDE_DIRS:
        text=(skin/d/'Includes_InfinityHomeUnified.xml').read_text()
        for token in ('InfinityMoviesPrimaryPath','InfinityMoviesSecondaryPath','InfinityTVPrimaryPath','InfinityTVSecondaryPath','InfinityResumeHubWatchedState'):
            if token not in text: raise RuntimeError(f'{d} missing {token}')

    output=out/OUT_NAME
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(root).as_posix())
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None: raise RuntimeError('Output CRC failure')
    proof={'schema':1,'parent_sha256':EXPECTED_PARENT,'skin_version':VERSION,'controller_min':COMMAND_VERSION,
           'requires_apk':2103292,'candidate_sha256':sha(output),'native_changed':False,
           'home_profiles_changed':len([x for x in changed if x.endswith('/Home.xml')]),
           'unified_include_profiles_changed':len([x for x in changed if x.endswith('/Includes_InfinityHomeUnified.xml')]),
           'trakt_sections_preserved':True,'infinity_movies_tv_added':True,'player_xml_changed':False,
           'changed_files':changed,'physical_device_verified':False}
    (out/'SKIN-PROOF.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    print(output); print(proof['candidate_sha256'])
if __name__=='__main__': main()
