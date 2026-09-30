#!/usr/bin/env python3
from pathlib import Path
import argparse,runpy,shutil,sys,json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
UPSTREAM=ROOT/'repairs/sports-data-2103271/stage_tests.py'

def replace_once(text,old,new,label):
    count=text.count(old)
    if count!=1:raise AssertionError(f'{label}: expected one preimage, found {count}')
    return text.replace(old,new,1)

def adapt_inherited(out,evidence):
    changes=[]
    p=out/'ProVisualTest.java';s=p.read_text();before=s
    s=replace_once(s,'allFiveFiltersExistAndDispatchExactlyOnce','allSixFiltersExistAndDispatchExactlyOnce','ProVisual name')
    s=replace_once(s,'for(int i=0;i<5;i++){assertEquals(CobraProUi.Filters.LABELS[i],f.buttons[i].getContentDescription());','for(int i=0;i<6;i++){assertEquals(CobraProUi.Filters.LABELS[i],f.buttons[i].getContentDescription());','ProVisual six-loop')
    s=replace_once(s,'assertEquals(Arrays.asList(0,1,2,3,4),calls);','assertEquals(Arrays.asList(0,1,2,3,4,5),calls);','ProVisual six-calls')
    s=replace_once(s,'for(CobraProUi.Action a:s.filters.buttons){assertEquals(0,a.getTop());assertTrue(a.getWidth()>=78);}','for(CobraProUi.Action a:s.filters.buttons){assertEquals(0,a.getTop());assertTrue(a.getWidth()>=48);}','ProVisual compact widths')
    s=replace_once(s,'assertTrue(s.filters.buttons[4].getRight()-s.filters.getScrollX()<=s.filters.getWidth());','assertTrue(s.filters.buttons[5].getRight()-s.filters.getScrollX()<=s.filters.getWidth());','ProVisual search index')
    s=replace_once(s,'assertTrue(s.filters.getHeight()>=86);for(CobraProUi.Action a:s.filters.buttons){assertTrue(a.getWidth()>=156);','assertTrue(s.filters.getHeight()>=82);for(CobraProUi.Action a:s.filters.buttons){assertTrue(a.getWidth()>=48);','ProVisual large-font geometry')
    p.write_text(s);changes.append(dict(file=p.name,before_len=len(before),after_len=len(s),reason='six Pro tabs; Sports inserted before Search'))

    p=out/'ProActionHarness.java';s=p.read_text();before=s
    s=replace_once(s,'int state,starts,refreshes,directory,searches,layouts;','int state,starts,refreshes,directory,sports,searches,layouts;','Harness counters')
    s=replace_once(s,'''    if(index==3){cobraOpenTvDirectory(false);return;}
    if(index==4){cobraShowChannelSearch();return;}
    cobraRememberModeScroll();mCategory=index==1?"FAVORITES":index==2?"RECENT":"ALL";mSearch="";mCobraGuideRoute="channels";''','''    if(index==3){cobraOpenTvDirectory(false);return;}
    if(index==4){sports++;cobraRenderGuideBrowser();return;}
    if(index==5){cobraShowChannelSearch();return;}
    cobraRememberModeScroll();mCategory=index==1?"FAVORITES":index==2?"RECENT":"ALL";mSearch="";mCobraGuideRoute="channels";''','Harness filter routes')
    s=replace_once(s,'seen.contains(channel.id)||mCobraProSlots.size()>=COBRA_PRO_MAX_SLOTS','seen.contains(channel.id)||mCobraProSlots.size()>=COBRA_PRO_MAX_SLOTS-1','Harness regular slot cap')
    p.write_text(s);changes.append(dict(file=p.name,before_len=len(before),after_len=len(s),reason='model new Sports route and reserve one hero source'))

    p=out/'ProActionsTest.java';s=p.read_text();before=s
    s=replace_once(s,'extractedFiveFiltersUseExistingRoutesWithoutRetuning','extractedSixFiltersUseExistingRoutesWithoutRetuning','ProActions name')
    s=replace_once(s,'h.filter(3);h.filter(4);assertEquals(1,h.directory);assertEquals(1,h.searches);assertEquals(3,h.layouts);','h.filter(3);h.filter(4);h.filter(5);assertEquals(1,h.directory);assertEquals(1,h.sports);assertEquals(1,h.searches);assertEquals(4,h.layouts);','ProActions routes')
    s=s.replace('assertEquals(6,h.mCobraProSlots.size());','assertEquals(5,h.mCobraProSlots.size());')
    if s.count('assertEquals(5,h.mCobraProSlots.size());')!=2:raise AssertionError('ProActions slot-cap adaptation count')
    p.write_text(s);changes.append(dict(file=p.name,before_len=len(before),after_len=len(s),reason='six routes and five regular hero slots + one permanent Sports source'))

    evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'pro-sports-inherited-adaptations.json').write_text(json.dumps(changes,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--inherited',action='store_true');a=p.parse_args()
    argv=[str(UPSTREAM),'--build',str(a.build),'--evidence',str(a.evidence)]
    if a.inherited:argv.append('--inherited')
    old=sys.argv;sys.argv=argv
    try:runpy.run_path(str(UPSTREAM),run_name='__main__')
    finally:sys.argv=old
    out=a.build/'xbmc/src/test/java/com/projectinfinity/kodi';adapt_inherited(out,a.evidence)
    shutil.copy2(HERE/'ProSportsIntegrationTest.java',out/'ProSportsIntegrationTest.java')
    print('Staged ProSportsIntegrationTest and superseded inherited Pro expectations for six tabs + reserved Live Sports hero source.')
if __name__=='__main__':main()
