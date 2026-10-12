#!/usr/bin/env python3
"""Four authorized Cobra 2103372 corrections, with exact source preimage."""
import hashlib, json, re
from pathlib import Path

RUNTIME='tools/android/packaging/xbmc/src/'
PREIMAGE='484b73bc677090a70667daa6c62e895402d4fed5a2f8dcdbe9a1f4e510d9f861'
RETIRED=['showCobraSportsHub','cobraSportsPrepareHeader','cobraSportsRenderCurrent',
 'cobraSportsRenderHub','cobraSportsAddSection','cobraSportsAddSoccerSection',
 'showCobraSportsSoccer','cobraSportsAddLeagueSection','cobraSportsGameCard',
 'cobraSportsTeamMark','showCobraSportsGame','cobraSportsAddTeamRow','showCobraSportsLeague']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise RuntimeError(message)

def span(text,name):
 matches=list(re.finditer(r'^  private [^\n{;=]*\b'+re.escape(name)+r'\([^\n]*?\)\s*\{',text,re.M))
 require(len(matches)==1,'Expected exactly one method: '+name)
 start=matches[0].start();pos=matches[0].end()-1;depth=0;state='code';i=pos
 while i<len(text):
  c=text[i];n=text[i:i+2]
  if state=='line':
   if c=='\n':state='code'
  elif state=='block':
   if n=='*/':state='code';i+=1
  elif state in ('string','char'):
   if c=='\\':i+=1
   elif c==('"' if state=='string' else "'"):state='code'
  elif n=='//':state='line';i+=1
  elif n=='/*':state='block';i+=1
  elif c=='"':state='string'
  elif c=="'":state='char'
  elif c=='{':depth+=1
  elif c=='}':
   depth-=1
   if depth==0:return start,i+1
  i+=1
 raise RuntimeError('Unbalanced method '+name)

def apply(source,out):
 path=source/RUNTIME/'InfinityLiveActivity.java.in'
 require(sha(path)==PREIMAGE,'Not exact delivered 2103372 source')
 before=path.read_text();text=before
 def replace(old,new):
  nonlocal text
  require(text.count(old)==1,'Ambiguous correction preimage: '+old[:100])
  text=text.replace(old,new)
 def method(name,body):
  nonlocal text
  a,b=span(text,name);text=text[:a]+body+text[b:]

 # Remove the retired standalone dashboard, its subpages, dedicated cards and callbacks.
 for name in RETIRED:
  a,b=span(text,name);text=text[:a]+text[b:]
 # The refresh owner already updates approved Pro Sports. Remove obsolete redraw calls.
 text=text.replace('if(cobraSportsVisible())cobraSportsRenderCurrent();','cobraProOnSportsDataChanged();')
 text=text.replace('cobraSportsRenderCurrent();','')
 replace('private boolean cobraProPlayerSportsEnabled(){return cobraTouchFirstDevice()&&"focus".equals(cobraGuideViewMode());}',
         'private boolean cobraProPlayerSportsEnabled(){return cobraTouchFirstDevice()&&mCobraProActive&&"focus".equals(mCobraGuideStyle);}')
 # Saved sports ownership is valid only in the active Pro experience; it cannot restore a retired screen.
 replace('    return mCobraDrawerOwner;\n  }',
 '''    if(COBRA_OWNER_SPORTS.equals(mCobraDrawerOwner)&&!cobraProPlayerSportsEnabled()){
      mCobraDrawerOwner=COBRA_OWNER_LIVE;
      if(mPrefs!=null)mPrefs.edit().putString(COBRA_DRAWER_OWNER_PREF,COBRA_OWNER_LIVE).apply();
    }
    return mCobraDrawerOwner;
  }''')
 replace('else if("SPORTS".equals(destination))owner=COBRA_OWNER_SPORTS;',
         'else if("SPORTS".equals(destination))owner=cobraProPlayerSportsEnabled()?COBRA_OWNER_SPORTS:COBRA_OWNER_LIVE;')
 replace('if(COBRA_OWNER_SPORTS.equals(owner)){if(!cobraProPlayerSportsEnabled())stopCobraPreview();mCobraInternalScreen="internal";showCobraSportsHub();return;}',
         'if(COBRA_OWNER_SPORTS.equals(owner)){cobraOpenProSportsSection();return;}')
 replace('if(upper.contains("SPORTS")){showCobraSportsHub();return;}',
         'if(upper.contains("SPORTS")){if(cobraProPlayerSportsEnabled())cobraOpenProSportsSection();else showCobraPrimaryView();return;}')
 replace('if(COBRA_OWNER_SPORTS.equals(owner))return title.startsWith("COBRA • SPORTS")||(mCobraProActive&&mCobraProSportsActive&&mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow());',
         'if(COBRA_OWNER_SPORTS.equals(owner))return cobraProPlayerSportsEnabled()&&mCobraProSportsActive&&mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow();')
 replace('''      if("COBRA • SPORTS".equals(title)||(mCobraProActive&&mCobraProSportsActive)){moveTaskToBack(true);return true;}
      showCobraSportsHub();return true;''',
 '''      if(mCobraProSportsActive){moveTaskToBack(true);return true;}
      cobraOpenProSportsSection();return true;''')
 replace('()->{closeCobraActionSheet();showCobraSportsHub();}',
         '()->{closeCobraActionSheet();cobraOpenProSportsSection();}')
 method('cobraSportsVisible','''  private boolean cobraSportsVisible(){
    if(!cobraProPlayerSportsEnabled()||!mCobraPlaybackPolicy.resumed||isCobraInPictureInPicture())return false;
    if(mCobraPlayerDrawer!=null&&"SPORTS".equals(mCobraDrawerFilter))return true;
    if(cobraScoreTickerEnabled()&&(mPlayerOverlay!=null||mCobraProActive))return true;
    if(mMultiOverlay!=null)return !mCobraSportsMultiAssignments.isEmpty();
    return mPlayerOverlay==null&&(mCobraProSportsActive||cobraProSportsHeroActive());
  }''')
 # Renderers always remove an old overlay first, then require active Pro to create another.
 replace('if(g==null||!cobraSportsMultiOverlay())continue;',
         'if(!cobraProPlayerSportsEnabled()||g==null||!cobraSportsMultiOverlay())continue;')
 replace('mCobraScorePending.clear();mCobraScoreContext="";return;',
         'mCobraScorePending.clear();mCobraScoreContext="";mCobraScoreWatchedGame="";return;')
 # Cover direct experience entry, not only the view-picker callback.
 replace('if(!CobraModeLayout.valid(mCobraGuideStyle))mCobraGuideStyle="mobile";',
         'if(!CobraModeLayout.valid(mCobraGuideStyle))mCobraGuideStyle="mobile";\n    if(!"focus".equals(mCobraGuideStyle))cobraClearProSportsPresentation();')
 replace('mCobraProSportsAdapter=null;mCobraProActive=false;mCobraProPlaybackOwned=false;mCobraProHeroBrowsing=false;',
         'mCobraProSportsAdapter=null;mCobraProActive=false;mCobraProPlaybackOwned=false;mCobraProHeroBrowsing=false;cobraClearProSportsPresentation();')
 replace('mCobraProObserved=null;mCobraProListener=null;mCobraProActive=false;mCobraProHeroUi=null;mCobraProOverlay=null;',
         'mCobraProObserved=null;mCobraProListener=null;mCobraProActive=false;mCobraProHeroUi=null;mCobraProOverlay=null;cobraClearProSportsPresentation();')
 # Fence in-flight sports actions as well as already-visible score presentation.
 replace('private void cobraSportsResolveAsync(CobraSportsGame game,CobraSportsResolverCallback consumer){',
         'private void cobraSportsResolveAsync(CobraSportsGame game,CobraSportsResolverCallback consumer){if(!cobraProPlayerSportsEnabled())return;')
 replace('private void cobraSportsOpenSmartMultiView(String scope,String focusId){',
         'private void cobraSportsOpenSmartMultiView(String scope,String focusId){if(!cobraProPlayerSportsEnabled())return;')
 replace('private void cobraSportsLaunchSmartMulti(LinkedHashMap<String,CobraSportsGame> selected,List<CobraSportsChannelInfo> snapshot){',
         'private void cobraSportsLaunchSmartMulti(LinkedHashMap<String,CobraSportsGame> selected,List<CobraSportsChannelInfo> snapshot){if(!cobraProPlayerSportsEnabled())return;')
 replace('if(channel==null||game==null||!game.live()||!cobraChannelAllowed(channel))return false;',
         'if(!cobraProPlayerSportsEnabled()||channel==null||game==null||!game.live()||!cobraChannelAllowed(channel))return false;')
 # Existing selected game/reminder data stays intact. Presentation and pending actions are cleared.
 anchor='  private boolean cobraProPlayerSportsEnabled()'
 pos=text.index(anchor)
 text=text[:pos]+'''  private void cobraOpenProSportsSection(){
    if(!cobraProPlayerSportsEnabled())return;
    closeCobraExperienceDrawer();mCobraGuideRoute="channels";cobraShowGuideShell();cobraProFilter(4);
  }
  private void cobraClearProSportsPresentation(){
    if(cobraProPlayerSportsEnabled())return;
    ++mCobraSportsActionSerial;
    cobraRemoveScoreTicker();mCobraScoreSeen.clear();mCobraScorePending.clear();
    mCobraScoreContext="";mCobraScoreWatchedGame="";
    mMain.removeCallbacks(mCobraSportsTick);
    if(mCobraPlayerDrawer!=null&&mCobraPlayerDrawer.findViewWithTag("cobra_player_tab_SPORTS")!=null)closeCobraPlayerDrawer();
    if("SPORTS".equals(mCobraDrawerFilter))mCobraDrawerFilter="ALL";
    if(mCobraMultiPickerFilter.startsWith("SPORTS")){closeCobraMultiPicker(false);mCobraMultiPickerFilter="ALL";}
    cobraSportsRefreshMultiOverlays();cobraDrawerOwner();
  }

'''+text[pos:]
 for name in RETIRED:require(not re.search(r'\b'+name+r'\b',text),'Retired reference survived: '+name)
 require('COBRA • SPORTS' not in text,'Retired dashboard title survived')
 path.write_text(text)
 out.mkdir(parents=True,exist_ok=True)
 (out/'TARGETED-DELTA.json').write_text(json.dumps({'parent_source_sha256':PREIMAGE,'source_sha256':sha(path),
  'removed_dashboard_methods':RETIRED,'findings':[1,2,3,4],'physical_acceptance':False},indent=2)+'\n')
 return text

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);a=p.parse_args();apply(a.source,a.out)
