#!/usr/bin/env python3
from pathlib import Path
import argparse

def profile(w,h,multi=False):
    compact=(h<280 and w>=280) or (multi and (h<440 or w<520))
    adaptive=(not compact and h>0 and w>=280 and (w/float(h)>=0.68 or w>=600))
    return compact,adaptive

def card_bounds(w,h,light=True):
    compact,adaptive=profile(w,h)
    assert adaptive and not compact
    margin=18;gap=18;brand=28 if h>=360 else 0;header=20+36+brand
    usable_w=max(1,w-2*margin);usable_h=max(1,h-header-margin)
    ir=(385/670) if light else (400/581)
    cr=(385/670) if light else (403/581)
    card_h=usable_h;iw=max(1,round(card_h*ir));cw=max(1,round(card_h*cr));room=max(2,usable_w-gap)
    if iw+cw>room:
        fit=room/float(iw+cw);iw=max(1,round(iw*fit));cw=max(1,room-iw)
        card_h=max(1,min(usable_h,round(min(iw/ir,cw/cr))))
        iw=max(1,round(card_h*ir));cw=max(1,round(card_h*cr))
    total=iw+gap+cw;x=max(margin,(w-total)//2);y=header+max(0,(usable_h-card_h)//2)
    a=(x,y,x+iw,y+card_h);b=(x+iw+gap,y,x+iw+gap+cw,y+card_h)
    assert 0<=a[0]<a[2]<=w and 0<=b[0]<b[2]<=w
    assert 0<=a[1]<a[3]<=h and 0<=b[1]<b[3]<=h
    assert a[2]<b[0]
    return a,b,total/w

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);args=ap.parse_args()
    shell=args.root/'shell-kodi/tools/android/packaging/xbmc/src'
    chooser=(shell/'InfinityGlassChooser.java.in').read_text()
    splash=(shell/'Splash.java.in').read_text()
    assert 'setOnLongClickListener(v->{actions.themes();return true;});' not in chooser
    assert 'root.setOnLongClickListener(v->{vtheme().manager(this);return true;});' not in splash
    assert '"Cobra Theme controls"' in splash
    assert 'getCurrentWindowMetrics().getBounds()' in splash
    # Phone/cover masters stay intact.
    assert profile(412,915)==(False,False)
    assert profile(320,720)==(False,False)
    # Fold inner / square / tablet / landscape reflow.
    assert profile(491,512)==(False,True)
    assert profile(600,800)==(False,True)
    assert profile(800,600)==(False,True)
    assert profile(960,540)==(False,True)
    # Small split/freeform becomes compact rather than clipping.
    assert profile(400,300,True)==(True,False)
    for light in (True,False):
        a,b,coverage=card_bounds(491,512,light)
        assert coverage>.80,(light,a,b,coverage)
        for size in ((600,800),(800,600),(960,540)):
            card_bounds(*size,light)
    print('PASS: chooser profile matrix, card bounds, and explicit-only theme controls')
if __name__=='__main__':main()
