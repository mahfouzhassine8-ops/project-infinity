#!/usr/bin/env python3
"""Explicitly update only old expectations superseded by the user's 2103201 request.

Historical repository tests remain unchanged. This runs on pinned CI checkouts
after their original parent gates, records every delta, and retains case identities.
"""
from pathlib import Path
import argparse,hashlib,json,re

FILES={
 'repair197/repairs/cobra-original-player-menu-2103197/tests/Cobra2103197OriginalPlayerMenuTest.java':'15f63792d8b9edc02a14e8b09284b49ee8936443ce019e6d4ec6603eae5510af',
 'audit198/repairs/cobra-complete-product-audit-2103198/tests/Cobra2103198CompleteProductAuditTest.java':'5764a1e2620f6ffe256527a90de4decda9068631126f6a8b030e54633b535dc8',
 'audit199/repairs/cobra-power-audit-2103199/tests/Cobra2103199DisplayRegressionTest.java':'f1d6a1bca83038c23cc8400494d064874420c8caf6a9a9808d2f33b9404e58e7',
 'audit199/repairs/cobra-power-audit-2103199/tests/display_geometry_host.py':'ef21522db133b9af8b738ce30648e34001d9d141510592202f657f1aafad07f4',
 'repair194/repairs/cobra-fold-adaptive-aspect-2103194/tests/Cobra2103194FoldAdaptiveAspectTest.java':'f0e7854812493a1a94a682b198f3009f2ee38375745502708a8cb1968dabdd26',
 'audit199/repairs/cobra-power-audit-2103199/tests/host_timeshift.py':'6ec7aca0070a1d7b5d37743fd3df235a0e97a6c06b98a7433094ca145efc3a40',
}
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def replace(s,old,new,count=1):
    if s.count(old)!=count:raise RuntimeError('Expectation anchor count changed: '+old)
    return s.replace(old,new)

def adapted(name,s):
    if 'Cobra2103197OriginalPlayerMenuTest' in name:
        s=replace(s,'"Audio & subtitles","Aspect / Display","Cast / Route"','"Audio & subtitles","Cast / Route"',2)
        s=replace(s,'"Player options","RECENT CHANNELS","Video & display","Player settings settings"','"Player options","RECENT CHANNELS","Video & display","Player settings settings","Aspect / Display"')
        s=replace(s,'      assertTrue(countText(root(a),"Restart current program")<=1);','      assertEquals(0,countText(root(a),"Aspect / Display"));\n      assertTrue(countText(root(a),"Restart current program")<=1);')
        s=replace(s,'      View row=clickableAncestor(findText(root(a),"Aspect / Display"));assertNotNull(row);assertTrue(row.isClickable());','      // 2103201: the existing Display button is now the single fullscreen aspect entry.\n      assertNull(findText(root(a),"Aspect / Display"));\n      call(a,"cobraBuildPlayerChrome");\n      View row=findDescription(o,"Display");assertNotNull(row);assertTrue(row.isClickable());')
        s=replace(s,'"Preferred audio language","Subtitles"','"Preferred audio language","Preferred subtitles"')
    elif 'Cobra2103198CompleteProductAuditTest' in name:
        s=replace(s,'"Audio & subtitles","Aspect / Display","Cast / Route"','"Audio & subtitles","Cast / Route"')
        s=replace(s,'"Player options","RECENT CHANNELS","Video & display","Player settings settings"','"Player options","RECENT CHANNELS","Video & display","Player settings settings","Aspect / Display"')
        s=replace(s,'"Preferred audio language","Subtitles"','"Preferred audio language","Preferred subtitles"')
    elif 'Cobra2103199DisplayRegressionTest' in name:
        s=replace(s,'    if(mode==12&&Math.min(w,h)>=600&&Math.max(source/(w/(double)h),(w/(double)h)/source)<=1.18){double z=Math.min(1.06,Math.max(w/rw,h/rh));rw*=z;rh*=z;}','    // 2103201 user contract: Fold Adaptive fits the whole frame without crop.')
    elif name.endswith('display_geometry_host.py'):
        s=replace(s,'    else if(mode==12){\n      double mismatch=Math.max(source/(w/(double)h),(w/(double)h)/source);\n      if(Math.min(w,h)>=600&&mismatch<=1.18){double z=Math.min(1.06,Math.max(w/rw,h/rh));rw*=z;rh*=z;}\n    }','    // 2103201 Fold Adaptive retains the proportional whole-frame fit above.')
        s=replace(s,'      if(mode==12){ok(s[0]<=1.06001&&s[1]<=1.06001,"Fold bounded crop");}','      if(mode==12){ok(s[0]<=1.00001&&s[1]<=1.00001,"Fold whole frame inside viewport");close(Math.max(s[0],s[1]),1,"Fold reaches one viewport edge");}')
    elif name.endswith('host_timeshift.py'):
        s=replace(s,"names=['cobraTimeshiftTimelineAvailable',","names=['cobraReadyTimelineProxy','cobraResetTimelineGesture','cobraTimeshiftTimelineAvailable',")
        s=replace(s,' private boolean mCobraProviderCatchupActive=false,mCobraTimeshiftDragging=false;',
          ' private boolean mCobraProviderCatchupActive=false,mCobraTimeshiftDragging=false;\n private boolean mCobraTimelineCancelled; private ExoPlayer mCobraTimelineDragPlayer; private CobraLocalTimeshiftSession mCobraTimelineDragSession;')
    elif 'Cobra2103194FoldAdaptiveAspectTest' in name:
        s=replace(s,'1.06f','1.0f',4)
        s=s.replace('public class Cobra2103194FoldAdaptiveAspectTest {','public class Cobra2103194FoldAdaptiveAspectTest {\n // Legacy case names retained; 2103201 strengthens the bound to whole-frame fit.')
    else:raise RuntimeError(name)
    return s

def main(root,out):
    changes={};pending=[]
    for name,expected in FILES.items():
        p=root/name;s=p.read_text()
        if digest(s)!=expected:raise RuntimeError('Pinned inherited test preimage changed: '+name)
        after=adapted(name,s)
        identities=lambda text:re.findall(r'@Test(?:\s*@[^\n]+)?\s+public void (\w+)\s*\(',text)
        if identities(s)!=identities(after):raise RuntimeError('Inherited test identities changed: '+name)
        changes[name]={'before':expected,'after':digest(after),'case_names_unchanged':True}
        pending.append((p,after))
    for p,s in pending:p.write_text(s)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'reason':'Explicit user approval: remove redundant player aspect entry, clarify subtitle preference, use whole-frame Fold fit. Host harness additionally extracts new production dependencies without changing its 14 assertions.','old_expectations_updated_not_silently_dropped':True,'changes':changes},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.root,a.out)
