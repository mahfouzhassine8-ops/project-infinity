#!/usr/bin/env python3
"""Final two-method ownership audit, chained after exact 230 corrective recipe."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('base230',ROOT/'apply.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def patch(before):
 s=before
 def edit(name,fn):
  nonlocal s
  a,b=base.parent.span(s,name);s=s[:a]+fn(s[a:b])+s[b:]
 edit('playChannel',lambda x:base.once(x,'    if(channel==null||!isCobraAsyncAlive())return;', '''    if(channel==null||!isCobraAsyncAlive())return;
    if(mCobraMultiFullscreenActive){
      // Explicit channel selection replaces/reuses only the promoted tile. Never
      // take the ordinary single-player route that releases every Multi-View peer.
      int selected=cobraMultiIndex(mCobraMultiFullscreenKey);
      if(selected<0||!cobraReturnToMultiFromFullscreen())return;
      if(mCobraTiles.get(channel.id)==null)replaceCobraMultiTileClean(selected,channel);
      cobraPromoteMultiTileFullscreen(channel.id);return;
    }'''))
 edit('cobraRestartLiveChannel',lambda x:base.once(x,'    if(!isCobraAsyncAlive()||!cobraLiveChannel(channel)||!expectedKey.equals(cobraPreferenceKey(channel)))return;', '''    if(!isCobraAsyncAlive()||!cobraLiveChannel(channel)||!expectedKey.equals(cobraPreferenceKey(channel)))return;
    if(mCobraMultiFullscreenActive&&channel.id.equals(mCobraMultiFullscreenKey)){
      // The tile registry owns this player even while fullscreen. Relinquish the
      // fullscreen alias before the existing explicit one-tile restart replaces it.
      String key=mCobraMultiFullscreenKey;
      if(!cobraReturnToMultiFromFullscreen())return;
      cobraRetryMultiTile(key);cobraPromoteMultiTileFullscreen(key);return;
    }'''))
 def strip(text):
  for name in ['playChannel','cobraRestartLiveChannel']:
   a,b=base.parent.span(text,name);text=text[:a]+'/* reviewed ownership '+name+' */'+text[b:]
  return text
 assert strip(before)==strip(s),'Unreviewed ownership delta'
 return s

def main():
 p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True);a=p.parse_args();act=a.shell/base.ACT
 before=act.read_text();assert h(before)=='9c5c092d3c00933f40336a2f5ed06ca795dc8c121886f80bd4a3252e6eb34ef3','Wrong first-stage 230 source'
 audit=Path('audit230/source-preservation.json');data=json.loads(audit.read_text());assert data['after']==h(before)
 after=patch(before);act.write_text(after);data['after']=h(after)
 data['changed_members']+=['playChannel','cobraRestartLiveChannel']
 data['ownership_followup']={'before':h(before),'after':h(after),'unreviewed_bytes_identical':True,'reason':'Promoted fullscreen manual restart/channel recall must preserve tile registry and healthy peers'}
 audit.write_text(json.dumps(data,indent=2)+'\n')
 rp=Path('engine/background-resume-source.json');r=json.loads(rp.read_text());assert r['version_code']==2103230;r['files'][base.ACT]['after']=h(after);rp.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 for n,row in r['files'].items():assert base.sha(a.shell/n)==row['after'],n
 print('PASS: two reviewed manual-ownership corrections; all remaining bytes unchanged')
if __name__=='__main__':main()
