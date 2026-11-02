"""One private player and existing handler labels; all old manifest nodes preserved."""
import copy
import struct
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(R/'repairs/dual-experience-isolation-2103420'), str(R/'repairs/infinity-final-closure-2103407/p0')]
from inventory import manifest_tree, chunks, string_pool
from manifest import append_strings, start, end
from release_gate import ANDROID, require

PLAYER = 'com.projectinfinity.kodi.InfinityExternalPlayerActivity'
LABEL = 'Infinity Preview'

def patch(raw):
    before = manifest_tree(raw)
    parts = list(chunks(raw))
    pool = next(p for _,k,p in parts if k == 1)
    old = string_pool(pool)
    additions = [s for s in [PLAYER, ':externalplayer', 'com.projectinfinity.kodi.external',
                'android.intent.action.SEND', LABEL] if s not in old]
    revised = append_strings(pool, additions)
    strings = string_pool(revised)
    resource_map = next(p for _,k,p in parts if k == 0x180)
    ids = list(struct.unpack('<'+'I'*((len(resource_map)-8)//4), resource_map[8:]))
    def node(tag, attrs):
        return start(tag, sorted(attrs, key=lambda a: ids[strings.index(a[0])]), strings)
    player = node('activity', [
        ('theme', 1, 0x0103022e), # android Theme.Material.NoActionBar, no APK resource mutation
        ('name', 3, PLAYER), ('exported', 0x12, 0), ('process', 3, ':externalplayer'),
        ('taskAffinity', 3, 'com.projectinfinity.kodi.external'), ('excludeFromRecents',0x12,1),
        ('launchMode', 0x10, 2), ('screenOrientation',0x10,0xffffffff),
        ('configChanges',0x11,0x00005ff8), ('resizeableActivity',0x12,1)
    ]) + end('activity', strings)
    share = node('intent-filter',[('label',3,LABEL)])
    for tag, attrs in [('action',[('name',3,'android.intent.action.SEND')]),
                       ('category',[('name',3,'android.intent.category.DEFAULT')]),
                       ('data',[('mimeType',3,'video/*')])]:
        share += node(tag,attrs)+end(tag,strings)
    share += end('intent-filter',strings)
    tree = copy.deepcopy(before)
    app = next(n for n in tree['children'] if n['tag']=='application')
    splash = next(n for n in app['children'] if n['tag']=='activity' and n['attributes'][ANDROID+'name']['value'].endswith('.Splash'))
    view = next(n for n in splash['children'] if n['tag']=='intent-filter' and any(
        c['tag']=='action' and c['attributes'][ANDROID+'name']['value']=='android.intent.action.VIEW' for c in n['children']))
    video_filter=copy.deepcopy(view)
    video_filter['attributes'][ANDROID+'label']={'type':3,'value':LABEL}
    video_filter['children']=[n for n in video_filter['children'] if not (n['tag']=='data'
        and ANDROID+'mimeType' in n['attributes'] and n['attributes'][ANDROID+'mimeType']['value']!='video/*')]
    view['children']=[n for n in view['children'] if not (n['tag']=='data'
        and n['attributes'].get(ANDROID+'mimeType',{}).get('value')=='video/*')]
    def encode(n):
        return node(n['tag'],[(k.removeprefix(ANDROID),v['type'],v['value']) for k,v in n['attributes'].items()])+b''.join(encode(c) for c in n['children'])+end(n['tag'],strings)
    video_route=encode(video_filter)
    # Binary edits preserve every existing chunk except the selected filter start.
    output=[]; in_splash=False; in_view=False; index=0; inserted=False; skip_data=False; changed_video=False
    for _,kind,part in parts:
        if kind==1: output.append(revised); continue
        if kind in (0x102,0x103):
            tag=strings[struct.unpack_from('<I',part,20)[0]]
            if kind==0x102 and tag=='activity':
                first,step,count=struct.unpack_from('<3H',part,24)
                attributes={}
                for i in range(count):
                    at=16+first+i*step
                    attributes[strings[struct.unpack_from('<I',part,at+4)[0]]]=part[at+15],struct.unpack_from('<I',part,at+16)[0]
                in_splash = attributes.get('name')==(3,strings.index('com.projectinfinity.kodi.Splash'))
                index=0
            if kind==0x102 and tag=='intent-filter' and in_splash:
                index+=1
                if index==2:
                    require(len(part)==36,'EXACT_BASELINE_VIEW_FILTER')
                    in_view=True
            if kind==0x102 and tag=='data' and in_splash and in_view:
                first,step,count=struct.unpack_from('<3H',part,24)
                for i in range(count):
                    at=16+first+i*step
                    if strings[struct.unpack_from('<I',part,at+4)[0]]=='mimeType' and part[at+15]==3 and strings[struct.unpack_from('<I',part,at+16)[0]]=='video/*':
                        skip_data=True;changed_video=True
                if skip_data:continue
            if kind==0x103 and tag=='data' and skip_data:skip_data=False;continue
            if kind==0x103 and tag=='intent-filter':in_view=False
            if kind==0x103 and tag=='activity' and in_splash:
                output.extend([video_route,share]);in_splash=False
            if kind==0x103 and tag=='application':
                output.append(player);inserted=True
        output.append(part)
    body=b''.join(output);result=struct.pack('<HHI',3,8,len(body)+8)+body
    after=manifest_tree(result)
    a=next(n for n in after['children'] if n['tag']=='application')
    added=a['children'].pop()
    require(added['tag']=='activity' and added['attributes'][ANDROID+'name']['value']==PLAYER,'ONE_PRIVATE_ACTIVITY')
    s=next(n for n in a['children'] if n['tag']=='activity' and n['attributes'][ANDROID+'name']['value'].endswith('.Splash'))
    added_share=s['children'].pop()
    require(added_share['tag']=='intent-filter' and added_share['children'][0]['attributes'][ANDROID+'name']['value']=='android.intent.action.SEND','VIDEO_SHARE_FILTER')
    added_video=s['children'].pop()
    require(added_video==video_filter,'ONE_LABELED_VIDEO_VIEW_FILTER')
    require(after==tree and inserted and changed_video,'ONLY_APPROVED_MANIFEST_CHANGES')
    return result
