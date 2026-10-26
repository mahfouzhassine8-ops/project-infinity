"""Exact signed419 -> scoped P0 runtime sources; no shutdown/native/chooser edits."""
import hashlib, json, re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).parent
CC = 'script.infinity.commandcenter'
SKIN = 'skin.infinity.diggz'
HC = 'script.kodihealthcenter'
VERSION = 2103420
PLAN = ROOT / 'P0-PLAN.json'

def digest(raw): return hashlib.sha256(raw).hexdigest()

def once(text, old, new):
    if text.count(old) != 1: raise ValueError('Exact nonunique P0 source boundary: '+old[:90])
    return text.replace(old, new, 1)

def checked(name, raw):
    pin = json.loads(PLAN.read_text())['source_preimages'].get(name)
    if not pin or digest(raw) != pin: raise ValueError('Exact signed419 preimage required: '+name)

def firstparty(before):
    result = dict(before)
    name = CC+'/context.py'; checked(name,before[name]); text=before[name].decode()
    start = "            root = Path(xbmcvfs.translatePath(xbmcaddon.Addon('script.infinity.uirepair').getAddonInfo('path')))\n"
    end = '            decoder = importlib.util.module_from_spec(spec); spec.loader.exec_module(decoder)\n'
    a=text.index(start); b=text.index(end,a)+len(end)
    replacement = """            from module_contract import source_module
            relative = 'script.infinity.commandcenter/infinity_modules/uirepair/latest_identity.py'
            if _infinity_contract.files.get(relative) != '225ac23336701db63715583ca8b6716afa96bb9b738b4b99750d9a5bbd8ab223':
                raise RuntimeError('The media identity component differs from the verified release.')
            decoder = source_module(_infinity_contract, '_infinity_title_identity', relative)
"""
    result[name]=(text[:a]+replacement+text[b:]).encode()
    name=CC+'/infinity_modules/uirepair/plugin.py';checked(name,before[name]);text=before[name].decode()
    text=once(text,"            values = plugin._values_for(data, media, 'continue')[:100]",
        "            values = plugin._values_for(data, media, 'continue')[:20]")
    text=once(text,'            for entry in values:\n', '            rows = []\n            for entry in values:\n')
    text=once(text,'                xbmcplugin.addDirectoryItem(handle, target, item, isFolder=False)',
        '                rows.append((target, item, False))\n            xbmcplugin.addDirectoryItems(handle, rows, totalItems=len(rows))')
    text=once(text,'            xbmcplugin.addDirectoryItems(handle, rows, totalItems=len(rows))',
        '            xbmcplugin.addDirectoryItems(handle, rows, totalItems=len(rows))\n            xbmcgui.Window(10000).setProperty(\'Infinity.Home.FirstViewportReady\', \'true\')')
    text=once(text,'    except Exception as exc:\n',
        "    except Exception as exc:\n        if action == 'continue':\n            xbmcgui.Window(10000).setProperty('Infinity.Home.FirstViewportReady', 'true')\n")
    result[name]=text.encode()
    name=CC+'/plugin.py';checked(name,before[name]);text=before[name].decode()
    text=once(text,'    visible = values[:100]\n',
        "    visible = values[:20 if PARAMS.get('home') == '1' else 100]\n")
    anchor="    hub.trace_timing('directory_items', rendered, items=min(len(values), 100), revision=int(data.get(\"revision\") or 0), **timing)\n"
    text=once(text,anchor,anchor+"    if PARAMS.get('home') == '1':\n        xbmcgui.Window(10000).setProperty('Infinity.Home.FirstViewportReady', 'true')\n")
    for old in ('items=min(len(values), 100),',):
        if text.count(old)!=2:raise ValueError('Original listing timing boundaries differ')
        text=text.replace(old,'items=len(visible),')
    result[name]=text.encode()
    name=CC+'/addon.xml';checked(name,before[name])
    result[name]=once(before[name].decode(),'version="0.3.5.48"','version="0.3.5.49"').encode()
    for name,raw in result.items():
        if name.endswith('.py') and raw != before[name]:compile(raw,name,'exec',dont_inherit=True)
    return result

def health(before):
    result=dict(before)
    for name in ('infinity_runtime_identity.py','addon.xml'):checked(HC+'/'+name,before[name])
    result['infinity_runtime_identity.py']=(ROOT/'infinity_runtime_identity.py').read_bytes()
    compile(result['infinity_runtime_identity.py'],'infinity_runtime_identity.py','exec',dont_inherit=True)
    result['addon.xml']=once(before['addon.xml'].decode(),'version="2.5.26"','version="2.5.27"').encode()
    return result

def power(text):
    root=ET.fromstring(text)
    group=root.find(".//control[@id='15000']")
    if group is None:raise ValueError('Original Reload Skin row missing')
    # Text insertion preserves every existing Power node and Close/Force route.
    match=re.search(r'(?m)^(?P<indent>[ \t]*)<control type="group" id="15000">.*?^(?P=indent)</control>',text,re.S)
    if not match:raise ValueError('Exact Reload Skin group boundary missing')
    row=match.group()
    added=once(row,'id="15000"','id="16000"')
    added=once(added,'id="1500"','id="1600"')
    added=once(added,'<label>RELOAD SKIN</label>','<label>[B]ASK EVERY TIME[/B]</label>')
    actions=re.search(r'<onclick>dialog.close\(shutdownmenu\)</onclick>\s*<onclick>reloadskin\(\)</onclick>',added)
    if not actions:raise ValueError('Exact Reload Skin actions missing')
    added=once(added,actions.group(),
        '<onclick>StartAndroidActivity(com.projectinfinity.kodi,com.projectinfinity.kodi.action.ASK_EVERY_TIME,,,,,,,com.projectinfinity.kodi.InfinityAskEveryTimeActivity)</onclick>')
    added=once(added,'infinity_ui/icons/replay.png','infinity_polish/infinity_mark.png')
    added=once(added,'Reload Infinity presentation resources','Show Choose Your Experience on next launch')
    added=once(added,'<control type="group" id="16000">',
        '<control type="group" id="16000">\n          <visible>System.Platform.Android</visible>')
    result=text[:match.end()]+'\n'+added+text[match.end():]
    check=ET.fromstring(result)
    parent=check.find(".//control[@id='9000']")
    children=list(parent)
    old_index=next(i for i,n in enumerate(children) if n.get('id')=='15000')
    if children[old_index+1].get('id')!='16000':raise ValueError('Power row ordering changed')
    if result.replace('\n'+added,'',1)!=text:raise ValueError('Existing Power content changed')
    return result

READY = ('!System.AddonIsEnabled(script.infinity.commandcenter) | '
    'String.IsEqual(Window(Home).Property(Infinity.Home.FirstViewportReady),true) | '
    '[!String.IsEmpty(Window(Home).Property(Infinity.ContinueWatchingRevision)) + '
    '[!Control.IsVisible(8830) | !Integer.IsGreater(Window(Home).Property(Infinity.ContinueWatchingMovies),0) | Integer.IsGreater(Container(8830).NumItems,0)] + '
    '[!Control.IsVisible(8831) | !Integer.IsGreater(Window(Home).Property(Infinity.ContinueWatchingTV),0) | Integer.IsGreater(Container(8831).NumItems,0)]]')

def home(text):
    tree=ET.fromstring(text);parents={c:p for p in tree.iter() for c in p}
    nodes=tree.findall('.//content[@target]')
    matches=list(re.finditer(r'(<content\b[^>]*\btarget="[^"]*"[^>]*>)([^<]*)(</content>)',text))
    if len(nodes)!=53 or len(matches)!=53:raise ValueError('Exact53 Home dynamic feeds required')
    variables={};replacements=[]
    for node,match in zip(nodes,matches):
        owner=parents[node];ident=owner.get('id')
        if not ident or not ident.isdigit():raise ValueError('A Home feed lacks a stable control ID')
        path=match[2]
        # Native providers evaluate URL labels even when the container is
        # hidden. An empty URL does not enqueue a directory job. Once populated,
        # retain its path/items on view switches to avoid rebuilding a rail.
        condition='Control.IsVisible('+ident+') | Integer.IsGreater(Container('+ident+').NumItems,0)'
        remote=any(token in path for token in ('plugin.infinity.latestreleases','slyguy.','plugin.program.iagl',
                    'InfinityTVPrimaryPath','InfinityMoviesPrimaryPath','InfinityMoviesSecondaryPath','Infinity210Playlist'))
        if remote:
            condition='Integer.IsGreater(Container('+ident+').NumItems,0) | [Control.IsVisible('+ident+') + ['+READY+']]'
        name='InfinityP0HomeFeed'+ident
        variables[name]='  <variable name="'+name+'"><value condition="'+condition+'">'+path+'</value><value /></variable>\n'
        replacements.append((match.start(2),match.end(2),'$VAR['+name+']'))
    for a,b,value in reversed(replacements):text=text[:a]+value+text[b:]
    ET.fromstring(text)
    return text,variables

def skin(before):
    result=dict(before);variables={};homes=sorted(n for n in before if n.endswith('/Home.xml'))
    if len(homes)!=14:raise ValueError('Exact14 Home profiles required')
    stats={}
    for name in homes:
        checked(SKIN+'/'+name,before[name]);text,definitions=home(before[name].decode())
        variables[str(Path(name).parent)]=definitions
        result[name]=text.encode();stats[name]=len(definitions)
    includes=sorted(n for n in before if n.endswith('/Includes_InfinityHomeUnified.xml'))
    if len(includes)!=10:raise ValueError('Exact10 inherited Home include profiles required')
    for name in includes:
        checked(SKIN+'/'+name,before[name]);text=before[name].decode()
        definitions=variables[str(Path(name).parent)]
        # Fallback shares the same bounded widget path while full lists retain100.
        text=text.replace('plugin://script.infinity.commandcenter/?action=continue&amp;media=',
                          'plugin://script.infinity.commandcenter/?action=continue&amp;home=1&amp;media=')
        text=once(text,'</includes>',''.join(definitions[n] for n in sorted(definitions))+'</includes>')
        ET.fromstring(text);result[name]=text.encode()
    for profile,definitions in variables.items():
        if profile+'/Includes_InfinityHomeUnified.xml' not in before and definitions!=variables['16x9']:
            raise ValueError('Inherited Home feed semantics differ: '+profile)
    powers=sorted(n for n in before if n.endswith('/DialogButtonMenu.xml'))
    if len(powers)!=14:raise ValueError('Exact14 Power profiles required')
    for name in powers:
        checked(SKIN+'/'+name,before[name]);result[name]=power(before[name].decode()).encode()
    name='addon.xml';checked(SKIN+'/'+name,before[name]);text=before[name].decode()
    text=once(text,'version="1.0.5.246"','version="1.0.5.247"')
    text=once(text,'<import addon="script.infinity.commandcenter" version="0.3.5.47" />',
                   '<import addon="script.infinity.commandcenter" version="0.3.5.49" />')
    result[name]=text.encode()
    name='infinity-skin.json';checked(SKIN+'/'+name,before[name]);meta=json.loads(before[name])
    meta.update(version='1.0.5.247',skin_version='1.0.5.247',candidate=247,candidate_locked=False,
        physical_device_verified=False,candidate_name='Infinity P0 completion')
    result[name]=(json.dumps(meta,indent=2,sort_keys=True)+'\n').encode()
    name='Infinity-Protected-Manifest.json';checked(SKIN+'/'+name,before[name]);protected=json.loads(before[name])
    for member,pin in protected['protected_files'].items():
        if member not in before or digest(before[member])!=pin:raise ValueError('Parent skin protected pin differs: '+member)
        protected['protected_files'][member]=digest(result[member])
    protected.update(skin_version='1.0.5.247',candidate_version='1.0.5.247',candidate=247,candidate_locked=False)
    result[name]=(json.dumps(protected,indent=2,sort_keys=True)+'\n').encode()
    return result,dict(gated_feeds_per_profile=stats,first_viewport_continue_limit=20,
        remote_first_viewport_ready='real Continue directory completion or explicit failure',
        no_new_timer_worker_or_service=True,existing_power_controls_unchanged=True,
        layout_geometry_player_resources_unchanged=True,shutdown_routes_unchanged=True,
        modified_members=sorted(n for n in result if result[n]!=before[n]))
