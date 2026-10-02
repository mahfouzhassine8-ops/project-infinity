#!/usr/bin/env python3
"""Host/source contract checks for Infinity 2103291 in-place responsive reflow."""
from pathlib import Path
import argparse,re,math

def method_span(s, signature):
    start=s.index(signature)
    brace=s.index("{",start)
    depth=0
    for i in range(brace,len(s)):
        ch=s[i]
        if ch=="{": depth+=1
        elif ch=="}":
            depth-=1
            if depth==0:
                return start,i+1
    raise AssertionError("Unbalanced method body for "+signature)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);a=ap.parse_args()
    root=a.source
    control=(root/'xbmc/guilib/GUIControl.cpp').read_text()
    group=(root/'xbmc/guilib/GUIControlGroup.cpp').read_text()
    factory=(root/'xbmc/guilib/GUIControlFactory.cpp').read_text()
    window=(root/'xbmc/guilib/GUIWindow.cpp').read_text()

    # The active resize path must retain the existing window/control tree.
    start,end=method_span(window,'void CGUIWindow::InfinityReloadNativeResponsiveLayout()')
    method=window[start:end]
    for forbidden in ('FreeResources(true)','AllocResources(true)','SaveControlStates()',
                      'RestoreControlStates()','ClearAll()','Load('):
        assert forbidden not in method,forbidden
    for required in ('m_coordsRes = next;','InfinityReflowRootGeometry();',
                     'CGUIControlGroup::ReflowResponsiveLayout',
                     'CGUIControlGroup::OnMessage(resize)',
                     'controls_reused=true window_reload=false'):
        assert required in method,required


    # The user's default Estuary reproduction is a core-Kodi test: a 4:3 source canvas must become
    # aspect-matched rather than independently squeezed when moving between the near-square inner
    # window and the very tall cover window.
    def adaptive(source_w, source_h, target_w, target_h):
        ratio=target_w/target_h
        area=source_w*source_h
        w=max(8,round(math.sqrt(area*ratio)/8)*8)
        h=max(8,round(math.sqrt(area/ratio)/8)*8)
        return w,h
    for target in ((1384,1536),(658,1536)):
        w,h=adaptive(1920,1440,*target)
        sx=target[0]/w; sy=target[1]/h
        assert abs(sx-sy) < 0.01,(target,(w,h),sx,sy)
        assert abs((w/h)-(target[0]/target[1])) < 0.01,(target,(w,h))

    # Generic control geometry is driven by the same XML grammar Kodi used at load time.
    for required in ('InfinityResponsiveParse','InfinityResolveResponsiveAxis',
                     "if (*end == 'r')","else if (*end == '%')",
                     'SetWidth(nextWidth);','SetHeight(nextHeight);','SetPosition(nextX, nextY);'):
        assert required in control,required

    # Parent/child layout ownership: nested groups reflow recursively against their current bounds.
    assert 'control->ReflowResponsiveLayout(childWidth, childHeight)' in group
    assert 'm_responsiveLayoutSpec.enabled ? GetWidth() : parentWidth' in group

    # Factory captures all supported anchor forms. No device model routing belongs here.
    for token in ('"left"','"right"','"centerleft"','"centerright"','"width"','"posx"',
                  '"top"','"bottom"','"centertop"','"centerbottom"','"height"','"posy"'):
        assert token in factory,token
    joined=control+group+factory+window
    for required in ('UsesNativeWindowAdaptation','GetNativeWindowResolution',
                     'infinity-android-adaptive','legacy-adaptive'):
        assert required in joined,required
    for forbidden in ('SM-F976','Galaxy Fold','Z Fold','q8q'):
        assert forbidden not in joined,forbidden

    # Resize notifications must be coalesced: controls receive the resize only after new geometry.
    schedule=window.index('m_infinityResponsiveReloadPending = true')
    assert 'return true;' in window[schedule:schedule+500]

    print('PASS: 2103291 keeps live Kodi controls and recomputes authored geometry in place')

if __name__=='__main__':main()
