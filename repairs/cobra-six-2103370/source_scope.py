"""Prove every Java token outside the six declared owners is preserved."""
import hashlib,json,re
from pathlib import Path
TOKENS=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\w+|[^\s]',re.M)
ACTIVITY_METHODS={
 'cobraPreviewPanel':'PiP control added without resizing or rearranging existing six callbacks',
 'cobraLayoutGuide':'Only new mini PiP control visibility; Pro owns its Hero PiP control',
 'cobraPlayChannelFullscreen':'Fullscreen audio handoff',
 'startSinglePlayer':'Fullscreen audio handoff including drawer/fallback tuning',
 'buildPlayer':'Seed only the targeted fullscreen session before existing audio focus',
 'cobraStartLocalTimeshift':'Commit fullscreen audio after successful proxy preparation only',
 'cobraStartDirectSinglePlayer':'Commit fullscreen audio after successful direct/fallback preparation only',
 'cobraWantsFullscreenPip':'Allow prepared paused sessions only for an explicit PiP button request; automatic behavior unchanged',
 'closePlayer':'Invalidate new handoff/PiP origin state on disposal',
 'promoteCobraPreviewToFullscreen':'Preserve audio only for explicit mini PiP transfer',
 'cobraConsumeLauncherPipReturn':'Explicit mini PiP origin restoration',
 'onPictureInPictureModeChanged':'Explicit mini PiP origin restoration',
 'cobraBuildPlayerChrome':'Pro rail and Cobra-wide PiP button',
 'cobraProSportsStats':'Expand the existing Pro mini game information action for upcoming and live events',
 'cobraProControl':'Pro-only PiP/Status callbacks',
 'cobraBuildProChrome':'Pro-only theme colors',
 'cobraRestyleGuide':'Pro-only header theme correction after existing restyle',
 'cobraRefreshAmbient':'Pro-only header theme correction after existing ambient refresh',
 'cobraOpenSheet':'Only Pro game Status skips a control anchor',
 'summary':'Additional Pro data; every existing Sports summary line retained',
 'cobraSportsParseScoreboard':'Additional venue location/progress fields only',
 'cobraSportsWatch':'Only Pro fullscreen uses corrected selection ownership',
 'cobraPlaySportsBroadcast':'Only Pro fullscreen dismisses obsolete choice layers',
}
def tokens(text):return [m[0] for m in TOKENS.finditer(text) if not m[0].startswith(('//','/*'))]
def digest(data):return hashlib.sha256(data).hexdigest()
def methods(text):
 out=[]
 pattern=r'(?:@Override\s+)?(?:private|protected|public)\s+(?:(?:static|final|synchronized)\s+)*[\w<>\[\],.?]+\s+(\w+)\s*\([^;{}]*\)\s*(?:throws\s+[\w.,\s]+)?\{'
 for m in re.finditer(pattern,text):
  start=text.index('{',m.start());depth=0
  for t in TOKENS.finditer(text,start):
   if t[0]=='{':depth+=1
   elif t[0]=='}':
    depth-=1
    if depth==0:out.append((m[1],m.start(),t.end()));break
 return out

def mask(text):
 spans=[(a,b,n) for n,a,b in methods(text) if n in ACTIVITY_METHODS]
 for a,b,n in reversed(spans):text=text[:a]+'AUTHORIZED_METHOD_'+n+text[b:]
 return text

def verify_activity(before,after):
 helpers=re.compile(r'  // BEGIN COBRA SIX 2103370:[\s\S]*?  // END COBRA SIX 2103370\n')
 assert len(helpers.findall(after))==1
 after=helpers.sub('',after)
 for added in ['    String venueLocation="",gameClock="",gameSituation="";\n',
  '    String venue="",venueLocation="",progress="";long observedAtMs=0L;\n    final Map<String,LinkedHashMap<String,String>> teamStats=new LinkedHashMap<>();\n']:
  assert after.count(added)==1;after=after.replace(added,'')
 assert tokens(mask(before))==tokens(mask(after)), 'Activity tokens changed outside authorized methods/data block'
 changed={}
 left={(n):before[a:b] for n,a,b in methods(before) if n in ACTIVITY_METHODS}
 right={(n):after[a:b] for n,a,b in methods(after) if n in ACTIVITY_METHODS}
 assert left.keys()==right.keys()==ACTIVITY_METHODS.keys(),(left.keys()^ACTIVITY_METHODS.keys())
 for n in left:
  assert tokens(left[n])!=tokens(right[n]),'Declared owner has no change: '+n
  changed[n]={'purpose':ACTIVITY_METHODS[n],'before':digest(left[n].encode()),'after':digest(right[n].encode())}
 return changed

def verify_pro(before,after):
 edits=[('final Action[] player=new Action[8]','final Action[] player=new Action[10]'),
 ('final long[] lastControlClick=new long[8]','final long[] lastControlClick=new long[10]'),
 ('"fullscreen","more","stats","groups"},names={"Pause","Favorite","Subtitles","Audio","Fullscreen","More","Stats","Multi-View"}',
  '"fullscreen","more","stats","groups","pip","stats"},names={"Pause","Favorite","Subtitles","Audio","Fullscreen","More","Stats","Multi-View","PiP","Status"}'),
 ('for(int index:new int[]{0,1,2,3,4,6,7,5})','for(int index:new int[]{0,1,2,3,4,6,7,8,9,5})'),
 ('show&&(i<6||sportsMode)','show&&(i<6||i>=8||sportsMode)'),
 ('','    else if("pip".equals(name)){c.drawRoundRect(2,4,22,20,2,2,p);p.setStyle(Paint.Style.FILL);c.drawRoundRect(12,11,20,18,1,1,p);}\n')]
 for old,new in edits:
  assert after.count(new)==1,new
  after=after.replace(new,old)
 assert tokens(before)==tokens(after),'Pro component changed outside two appended controls/icon'

def verify(base,source,out):
 base=Path(base);source=Path(source)
 before={p.relative_to(base).as_posix():digest(p.read_bytes()) for p in base.rglob('*') if p.is_file()}
 after={p.relative_to(source).as_posix():digest(p.read_bytes()) for p in source.rglob('*') if p.is_file()}
 prefix='tools/android/packaging/xbmc/src/'
 changed=sorted(n for n in before.keys()|after.keys() if before.get(n)!=after.get(n))
 assert changed==[prefix+'CobraProUi.java.in',prefix+'InfinityLiveActivity.java.in'] and before.keys()==after.keys(),changed
 activity=verify_activity((base/(prefix+'InfinityLiveActivity.java.in')).read_text(),(source/(prefix+'InfinityLiveActivity.java.in')).read_text())
 verify_pro((base/(prefix+'CobraProUi.java.in')).read_text(),(source/(prefix+'CobraProUi.java.in')).read_text())
 report={'before':before,'after':after,'changed':changed,'changed_activity_methods':activity,
 'protected_activity_tokens_identical':True,'protected_pro_component_tokens_identical':True,
 'other_android_sources_byte_identical':len(before)-2,'native_source_changed':False,
 'scope_matrix':{'fullscreen_audio':'all Cobra modes, fullscreen retunes only','PiP':'all Cobra modes, explicit mini/fullscreen buttons','control_rail':'Pro fullscreen only','home_game_status':'Pro only','sports_overlay':'Pro fullscreen only','header_theme':'Pro header only'}}
 Path(out).write_text(json.dumps(report,indent=2)+'\n');return report
