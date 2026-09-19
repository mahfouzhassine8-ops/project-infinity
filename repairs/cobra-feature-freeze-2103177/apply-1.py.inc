from pathlib import Path
import argparse,hashlib,json,re
REL=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_BUILD=2103176
BASE_COMMIT='9c26e7aaa92c6c2bbe83a284c3377c6ca61d2224'
EXPECTED='ace1af468acd170a90da48c3cf529c5e13ba11dcb2e5c354dbb115497288385e'
def sha(v):return hashlib.sha256(v if isinstance(v,bytes) else v.encode()).hexdigest()
def once(s,a,b,label):
 c=s.count(a)
 if c!=1:raise RuntimeError(f'{label}: expected one anchor, got {c}')
 return s.replace(a,b,1)
def matches(text,name):
 return list(re.finditer(r'^[ \t]{2,}(?:(?:@Override(?:[ \t]*\n[ \t]+|[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'+re.escape(name)+r'\s*\(',text,re.M))
def span(text,name):
 ms=matches(text,name)
 if len(ms)!=1:raise RuntimeError(f'Method cardinality {name}={len(ms)}')
 start=ms[0].start();i=text.index('{',ms[0].end());d=0;q=None;esc=line=block=False
 while i<len(text):
  c=text[i];n=text[i+1] if i+1<len(text) else ''
  if line:
   if c=='\n':line=False
  elif block:
   if c=='*' and n=='/':block=False;i+=1
  elif q:
   if esc:esc=False
   elif c=='\\':esc=True
   elif c==q:q=None
  elif c=='/' and n=='/':line=True;i+=1
  elif c=='/' and n=='*':block=True;i+=1
  elif c in ('"',"'"):q=c
  elif c=='{':d+=1
  elif c=='}':
   d-=1
   if d==0:return start,i+1
  i+=1
 raise RuntimeError('Unclosed '+name)
def method(text,name):a,b=span(text,name);return text[a:b]
def replace_method(text,name,new):a,b=span(text,name);return text[:a]+new.rstrip()+'\n'+text[b:]

ROOT=Path(__file__).resolve().parent
HELPERS=''.join((ROOT/f'activity-helpers-{i}.java.inc').read_text() for i in range(1,5)).rstrip()

def apply(source,receipt_path,out):
 source=Path(source);out=Path(out);path=source/REL;before_b=path.read_bytes();before=before_b.decode();receipt=json.loads(Path(receipt_path).read_text())
 if receipt.get('version_code')!=BASE_BUILD:raise RuntimeError('Expected exact passed 2103176 source receipt')
 if sha(before_b)!=EXPECTED:raise RuntimeError('2103176 Activity preimage mismatch '+sha(before_b))
 # protect sensitive system-bar/background/provider/file-picker contracts.
 protected=['cobraApplySystemBarsForSurface','cobraInstallBrowseSafeArea','onUserLeaveHint','pauseCobraForBackground','cobraBeginMiniBackgroundPlayback','cobraEndMiniBackgroundPlayback','openCobraUiPackagePicker','openDocumentPicker','loadXtream','parseM3u','cobraReattachObservedSurface']
 guards={n:sha(method(before,n)) for n in protected}
 text=before

 # Settings: group and add final feature controls.
 settings=method(text,'showSettings')
 settings=once(settings,
'''    Button liveRewind = action("LIVE TV REWIND  •  " + cobraLiveRewindLabel());
