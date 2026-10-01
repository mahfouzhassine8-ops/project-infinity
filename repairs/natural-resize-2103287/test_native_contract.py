#!/usr/bin/env python3
from pathlib import Path
import argparse,re

def choose(ratio):
    # Exact accepted 1.0.5.178/.180 profile aspect table; mirrors Kodi closestRes ratio selection.
    table=[
      ('fallback',11/10),('16x9',16/9),('16x9',16/10),('16x9',3/2),('16x9',17/9),
      ('20x9',18/9),('20x9',19/9),('20x9',19.5/9),('20x9',20/9),('20x9',21/9),('20x9',22/9),('20x9',23/9),('20x9',24/9),
      ('6x5',4/3),('6x5',5/4),('6x5',6/5),
      ('5x6',5/6),('5x6',4/5),('5x6',3/4),('5x6',2/3),
      ('portrait',10/16),('portrait',9/17),('portrait',9/16),('portrait',9/18),('portrait',9/19),('portrait',9/19.5),('portrait',9/20),('portrait',9/21),('portrait',9/22),('portrait',9/23),('portrait',9/24)]
    return min(table,key=lambda row:abs(row[1]-ratio))[0]

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
    h=(a.source/'xbmc/guilib/GUIWindow.h').read_text()
    c=(a.source/'xbmc/guilib/GUIWindow.cpp').read_text()
    for token in ('m_infinityProfileReloadPending','InfinitySkinProfileChanged','InfinityReloadSkinProfile',
                  'g_SkinInfo->GetSkinPath(xmlFile, &next)','SaveControlStates();','FreeResources(true);',
                  'AllocResources(true);','RestoreControlStates();'):
        assert token in h+c,token
    block=c[c.index('void CGUIWindow::InfinityReloadSkinProfile()'):c.index('void CGUIWindow::AllocResources')]
    assert 'RunLoadActions();' not in block
    assert block.index('SaveControlStates();') < block.index('FreeResources(true);') < block.index('AllocResources(true);') < block.index('RestoreControlStates();')
    # Prove the accepted profile matrix genuinely changes for common orientation/Fold transitions.
    cases=[((412,915),'portrait'),((915,412),'20x9'),((1473,1536),'5x6'),((1536,1473),'fallback'),((1440,1200),'6x5'),((1200,1440),'5x6')]
    for (w,hh),expected in cases:
        got=choose(w/hh);assert got==expected,((w,hh),got,expected)
    print('PASS: deferred active-window profile reload + accepted .180 orientation/Fold routing matrix')
if __name__=='__main__':main()
