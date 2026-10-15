#!/usr/bin/env python3
"""Preimage-guarded follow-up for observed Stats failures and Pro header contrast."""
import hashlib
import json
from pathlib import Path
import difflib
HERE=Path(__file__).resolve().parent
PREFIX='tools/android/packaging/xbmc/src/'
EXPECTED='77482b135aff60a4c0c6953bb92b1949c32e447528434df659aa869892ab4c1c'

def sha(text):return hashlib.sha256(text.encode()).hexdigest()

def apply(source,out):
 p=source/PREFIX/'InfinityLiveActivity.java.in';old=p.read_text()
 if sha(old)!=EXPECTED:raise RuntimeError('Delivery correction requires exact passing checkpoint source')
 text=old;edits=[]
 def replace(before,after,member,requirement=4):
  nonlocal text
  if text.count(before)!=1:raise RuntimeError('Delivery preimage mismatch: '+member)
  text=text.replace(before,after,1);edits.append({'member':member,'requirement':requirement,'before':sha(before),'after':sha(after)})
 replace('  private static final class CobraSportsSummary{\n    final ArrayList<String> lines=new ArrayList<>();\n  }',
         '  private static final class CobraSportsSummary{\n    final ArrayList<String> lines=new ArrayList<>();\n    CobraSix.SummaryMetadata proData;\n  }','CobraSportsSummary.proData (new field)')
 before='      JSONObject root=cobraSportsJson(base(spec)+"/summary?event="+URLEncoder.encode(game.id,"UTF-8"));'
 replace(before,before+'\n      out.proData=mCobraSix.readSummaryMetadata(game,root);','CobraEspnSiteSportsRepository.summary: optional projection; original detail parser unchanged')
 start='    boolean stats(CobraSportsGame game) {';end='    void team(LinearLayout rows,CobraSportsTeam team,String side) {'
 if text.count(start)!=1 or text.count(end)!=1:raise RuntimeError('Stats controller boundary mismatch')
 first=text.index(start);last=text.index(end,first);fragment=(HERE/'StatsDelivery.fragment.java').read_text()
 replace(text[first:last],fragment+'\n','CobraSix.stats and new scoped metadata/session helpers')
 before='      if(mCobraModeSub instanceof CobraProUi.Ink)((CobraProUi.Ink)mCobraModeSub).ink(muted);\n    }'
 after='''      if(mCobraModeSub instanceof CobraProUi.Ink)((CobraProUi.Ink)mCobraModeSub).ink(muted);
      // The approved header is reused across theme changes. Refresh only its
      // three existing icon inks; callbacks, glyphs, bounds and other modes stay owned by the original UI.
      for(int i=0;i<mCobraModeToolbar.getChildCount();i++){
        View child=mCobraModeToolbar.getChildAt(i);
        if(child instanceof CobraIconButton){CobraIconButton icon=(CobraIconButton)child;if(icon.ink!=ink){icon.ink=ink;icon.invalidate();}}
      }
    }'''
 replace(before,after,'CobraSix.headerTheme: existing Pro-header icon contrast only',6)
 p.write_text(text)
 delta=''.join(difflib.unified_diff(old.splitlines(True),text.splitlines(True),'saved/'+PREFIX+p.name,'candidate/'+PREFIX+p.name))
 (out/'stats-delivery.patch').write_text(delta)
 (out/'STATS-DELIVERY-DELTA.json').write_text(json.dumps({'checkpoint':'4583f403521dbcc7f4d9734d9f750b9dd64b3824','failed_validation_run':38219841051,'visual_contrast_evidence_run':38221469867,'requirements':[4,6],'changed_file':PREFIX+p.name,'before_sha256':sha(old),'after_sha256':sha(text),'edits':edits,'original_detailed_lines_preserved':True,'pip_groups_tuning_policies_changed':False},indent=2)+'\n')
 print('Applied scoped Stats and Pro-header corrections; PiP/Groups/tuning unchanged')
