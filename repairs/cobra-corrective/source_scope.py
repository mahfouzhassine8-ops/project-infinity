"""Gate B/C: approved-source bytes and Java tokens outside reviewed six-item contracts.

This is a scope guard, not a substitute for the Android runtime gates.
"""
import hashlib
import json
import re
from pathlib import Path

PREFIX = Path('tools/android/packaging/xbmc/src')
FILES = ('InfinityLiveActivity.java.in', 'CobraProUi.java.in')
LEX = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\w+|[^\s]', re.M)

# (owner class or None, method, authorized item numbers, contract)
EXISTING_ACTIVITY = [
 (None,'cobraPreviewPanel',[2],'Append separate phone PiP target; original six callbacks and row untouched.'),
 (None,'buildPlayer',[1],'Only scoped Channels replacement construction inherits existing userMuted and requested volume; same audio/player engine.'),
 ('CobraIconButton','onDraw',[4],'Fullscreen Stats delegates to the exact existing Pro mini stats canvas icon.'),
 (None,'cobraLayoutGuide',[2],'Only hide duplicate corner PiP while actual Pro owns its own PiP controls; geometry unchanged.'),
 (None,'cobraBuildPlayerChrome',[2,3,4],'Phone PiP; Pro-only original-width horizontal row; actual Sports-only Stats; original other callbacks.'),
 (None,'cobraRenderPlayerDrawer',[1],'Wrap only actual channel-row replacement in one synchronous Channels audio-intent scope.'),
 (None,'cobraRestoreAfterPipFailure',[2],'Restore mini origin after existing PiP failure behavior.'),
 (None,'cobraBuildProChrome',[6],'Existing Pro header structure/callbacks; theme text/muted tokens and existing glass surface.'),
 (None,'cobraProPlayerSportsEnabled',[3,4,5],'Actual live phone Pro ownership/mode, never persisted guide preference; approved Pro capabilities retained.'),
 (None,'cobraProControl',[2],'PiP callback index8 added without remapping existing indices0–7.'),
 (None,'cobraConsumeLauncherPipReturn',[2],'Mini button origin handoff before existing launcher/native-return handling.'),
 ('CobraEspnSiteSportsRepository','summary',[4],'Read available metadata/player fields from existing summary response; original lines/leaders preserved.'),
 (None,'showCobraSportsStats',[4],'Existing Stats entry shared by mini/fullscreen, Sports-only enhancement, owner guard, spoilers/unavailable handling.'),
 (None,'cobraSportsWatch',[1,5],'Only actual Pro Sports fullscreen Channels invocation uses new layer-free chooser; original matching preserved.'),
]
ADDED_ACTIVITY = [
 ('cobraCorrectiveSportsContext',[3,4,5],'Actual Pro plus current Sports section or hero pane.'),
 ('cobraChannelsTune',[1],'Capture existing user mute/requested-volume intent, exclude temporary focus/call mute, finally clear scope.'),
 ('cobraButtonPictureInPicture',[2],'Phone-only existing-player promotion and existing PiP API; remember mini origin.'),
 ('cobraRestoreButtonPipOrigin',[2],'Same-session fullscreen-to-mini return after resumed native expansion/failure.'),
 ('cobraReadCorrectiveSportsSummary',[4],'Parse available venue/city/clock/possession/situation/player fields without invented data.'),
 ('cobraRenderCorrectiveSportsStats',[4],'Available team names/logos, metadata and existing detailed lines; stale/spoiler gates.'),
 ('cobraChannelsSportsBroadcast',[1,5],'Close obsolete layers then invoke original broadcast action inside Channels audio scope.'),
 ('cobraChannelsBroadcastChooser',[5],'Install only the scoped chooser on existing fullscreen owner.'),
]
EXISTING_UI = [
 (None,'icon',[2],'Add PiP glyph; existing Stats geometry unchanged.'),
 ('Hero','Hero',[2],'Append PiP index8 and separate muted-preview PiP; preserve all original control indices.'),
 ('Hero','applyModeVisibility',[2],'PiP visibility only; all original control visibility rules unchanged.'),
 ('Hero','onLayout',[2],'Place only added muted-preview PiP beside Unmute; original layout expressions unchanged.'),
]

def tokens(text):
    return [m[0] for m in LEX.finditer(text) if not m[0].startswith(('//','/*'))]

def closing(text, opening):
    depth=0
    for token in LEX.finditer(text,opening):
        if token[0]=='{': depth+=1
        elif token[0]=='}':
            depth-=1
            if depth==0:return token.end()
    raise AssertionError('Unclosed Java body')

def class_span(text,name):
    matches=list(re.finditer(r'\bclass\s+'+re.escape(name)+r'\b[^\{;]*\{',text))
    assert len(matches)==1,(name,len(matches))
    m=matches[0];return m.start(),closing(text,text.index('{',m.start()))

def method_span(text,name,owner=None):
    start,end=class_span(text,owner) if owner else (0,len(text))
    region=text[start:end]
    pattern=re.compile(r'^\s*(?:@Override\s+)?(?:(?:public|private|protected|static|final|synchronized)\s+)*(?:[\w<>\[\].]+\s+)?'+re.escape(name)+r'\s*\([^;{}]*\)\s*(?:throws\s+[^;{]+)?\s*\{',re.M)
    matches=list(pattern.finditer(region))
    assert len(matches)==1,(owner,name,len(matches))
    m=matches[0];opening=start+region.index('{',m.start());return start+m.start(),closing(text,opening)

def erase_method(text,name,owner=None,added=False):
    start,end=method_span(text,name,owner)
    # Keep modifiers/return type in existing signatures, and erase only reviewed bodies.
    if not added:
        opening=text.index('{',start)
        return text[:opening]+'{ CORRECTIVE_'+name+' }'+text[end:]
    line=text.rfind('\n',0,start)+1
    return text[:line]+text[end:]

def remove_exact(text,segment):
    assert text.count(segment)==1,('Unexpected field declaration',segment,text.count(segment))
    return text.replace(segment,'')

def normalize_activity(before,after):
    for owner,name,_,_ in EXISTING_ACTIVITY:
        before=erase_method(before,name,owner);after=erase_method(after,name,owner)
    for name,_,_ in ADDED_ACTIVITY:after=erase_method(after,name,added=True)
    start,end=class_span(after,'CobraChannelsBroadcastSheet')
    line=after.rfind('\n',0,start)+1;after=after[:line]+after[end:]
    for field in ('private Boolean mCobraChannelsTuneMuted;', 'private float mCobraChannelsTuneVolume=1f;',
                  'private String mCobraChannelsTuneKey="";', 'private boolean mCobraButtonPipMiniOrigin;',
                  'final ArrayList<String> playerLines=new ArrayList<>();',
                  'String venue="",city="",clock="",situation="",possession="";'):
        after=remove_exact(after,field)
    return before,after

def normalize_ui(before,after):
    for owner,name,_,_ in EXISTING_UI:
        before=erase_method(before,name,owner);after=erase_method(after,name,owner)
    for new,old in (('sportsStats,sportsMulti,previewPip;','sportsStats,sportsMulti;'),
                    ('player=new Action[9]','player=new Action[8]'),
                    ('lastControlClick=new long[9]','lastControlClick=new long[8]')):
        assert after.count(new)==1,new
        after=after.replace(new,old)
    return before,after

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(baseline_root:Path,candidate_root:Path,out:Path)->dict:
    baseline_root,candidate_root,out=map(Path,(baseline_root,candidate_root,out))
    baseline_files={p.relative_to(baseline_root) for p in baseline_root.rglob('*') if p.is_file()}
    candidate_files={p.relative_to(candidate_root) for p in candidate_root.rglob('*') if p.is_file()}
    assert baseline_files==candidate_files,{'candidate_only':[str(p) for p in sorted(candidate_files-baseline_files)],'missing':[str(p) for p in sorted(baseline_files-candidate_files)]}
    changed=[];byte_identical=[]
    for path in sorted(baseline_root.rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(baseline_root);candidate=candidate_root/relative
        assert candidate.is_file(),f'Missing baseline file: {relative}'
        if path.read_bytes()!=candidate.read_bytes():
            assert relative in {PREFIX/name for name in FILES},f'Forbidden changed source: {relative}'
            changed.append(str(relative))
        else:byte_identical.append(str(relative))
    assert set(changed)=={str(PREFIX/name) for name in FILES},changed
    inventory=[]
    for name,normalizer in zip(FILES,(normalize_activity,normalize_ui)):
        before=(baseline_root/PREFIX/name).read_text();after=(candidate_root/PREFIX/name).read_text()
        left,right=normalizer(before,after)
        assert tokens(left)==tokens(right),f'Java change outside explicit six-item contracts: {name}'
        for owner,method,items,contract in EXISTING_ACTIVITY if name==FILES[0] else EXISTING_UI:
            bs,be=method_span(before,method,owner);cs,ce=method_span(after,method,owner)
            assert tokens(before[bs:be])!=tokens(after[cs:ce]),f'Unchanged method incorrectly allowlisted: {method}'
            inventory.append(dict(file=name,owner=owner,method=method,kind='changed',items=items,contract=contract))
    for method,items,contract in ADDED_ACTIVITY:inventory.append(dict(file=FILES[0],method=method,kind='added',items=items,contract=contract))
    inventory.append(dict(file=FILES[0],owner='CobraChannelsBroadcastSheet',method='CobraChannelsBroadcastSheet',members=['CobraChannelsBroadcastSheet','onMeasure','onLayout','BaseAdapter.getCount','BaseAdapter.getItem','BaseAdapter.getItemId','BaseAdapter.getView'],kind='added',items=[5],contract='Bounded actual ListView, >=4 complete48dp rows when >=4 matches; side Close for short windows; explicit geometryBlocked below physical capacity.'))
    result=dict(result='PASS',changed_files=changed,changed_methods=inventory,
                protected_java_tokens_identical=True,protected_other_sources_byte_identical=byte_identical,
                baseline_sha256={name:sha(baseline_root/PREFIX/name) for name in FILES},
                candidate_sha256={name:sha(candidate_root/PREFIX/name) for name in FILES},
                physical_validation='PENDING; runtime rendering does not certify hardware playback',
                preserved_ticker='Original optional Pro score-alert feature retained. Only live-mode ownership predicate is corrected; no new non-Sports Stats/score UI.')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('baseline_root',type=Path);parser.add_argument('candidate_root',type=Path);parser.add_argument('out',type=Path);args=parser.parse_args()
    result=verify(args.baseline_root,args.candidate_root,args.out);print(json.dumps({'result':result['result'],'changed_files':result['changed_files'],'method_contracts':len(result['changed_methods'])}))
