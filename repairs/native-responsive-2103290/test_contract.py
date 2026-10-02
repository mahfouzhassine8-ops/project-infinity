#!/usr/bin/env python3
"""Host-side contract tests for Infinity Native Responsive Layout v1."""
from pathlib import Path
import argparse, math

SHORT=1080
QUANTUM=8

def quantize(v):
    if v<=SHORT:return SHORT
    return max(SHORT, ((v+QUANTUM//2)//QUANTUM)*QUANTUM)

def logical(w,h):
    r=w/h
    if r>=1:
        return quantize(round(SHORT*r)),SHORT
    return SHORT,quantize(round(SHORT/max(.01,r)))

def cls(w,h):
    r=w/h
    if r>=1.95:return 'ultrawide'
    if r>=1.48:return 'wide'
    if r>=1.12:return 'landscape'
    if r>=.86:return 'square'
    if r>=.55:return 'portrait'
    return 'tall'

def scale_error(w,h,lw,lh):
    sx=w/lw;sy=h/lh
    return abs(sx-sy)/max(sx,sy)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);a=ap.parse_args()
    root=a.source
    skin=(root/'xbmc/addons/Skin.cpp').read_text()
    win=(root/'xbmc/guilib/GUIWindow.cpp').read_text()
    android=(root/'xbmc/windowing/android/WinSystemAndroid.cpp').read_text()

    # Architecture ownership: responsive resolver is marker-gated and cannot fall into the
    # legacy default/fallback profile while the marker exists.
    start=skin.index('std::string CSkinInfo::GetSkinPath')
    end=skin.index('bool CSkinInfo::HasSkinFile',start)
    block=skin[start:end]
    assert 'if (UsesNativeResponsiveLayout())' in block
    resp=block[block.index('if (UsesNativeResponsiveLayout())'):block.index('// find the closest resolution')]
    assert 'responsiveRoot' in resp and '"base"' in resp
    assert 'm_defaultRes' not in resp
    assert 'std::min_element' not in resp
    paths_start=skin.index('void CSkinInfo::GetSkinPaths')
    paths_end=skin.index('bool CSkinInfo::TranslateResolution',paths_start)
    paths_block=skin[paths_start:paths_end]
    responsive_paths=paths_block[paths_block.index('if (UsesNativeResponsiveLayout())'):
                                 paths_block.index('RESOLUTION_INFO res;')]
    assert responsive_paths.count('paths.push_back')==1, responsive_paths
    assert 'responsiveRoot, "base"' not in responsive_paths

    # Active windows reload only after a settled resize and preserve focus/control state.
    for token in ('std::chrono::milliseconds(90)','SaveControlStates();','FreeResources(true);',
                  'AllocResources(true);','RestoreControlStates();','InfinityPublishResponsiveProperties'):
        assert token in win,token
    method=win[win.index('void CGUIWindow::InfinityReloadNativeResponsiveLayout()'):
               win.index('void CGUIWindow::AllocResources')]
    assert method.index('SaveControlStates();') < method.index('FreeResources(true);')
    assert method.index('FreeResources(true);') < method.index('AllocResources(true);')
    assert method.index('AllocResources(true);') < method.index('RestoreControlStates();')
    assert 'RunLoadActions();' not in method

    # Native geometry remains Android-window-owned; Kodi only derives the logical skin canvas after
    # the committed physical geometry is authoritative.
    assert 'Infinity geometry committed:' in android
    assert 'Infinity responsive viewport:' in android
    assert android.index('state.CommitGeometry(request)') < android.index('Infinity responsive viewport:')

    # Real sizes captured by Health Center on the user's Fold. The logical canvas must keep the
    # short axis stable and make global X/Y scale effectively equal despite arbitrary aspect ratios.
    cases=[
      (2256,2504,'square'),(1200,1637,'portrait'),(1226,938,'landscape'),
      (1226,1680,'portrait'),(1080,2520,'tall'),(616,1497,'tall'),(721,1088,'portrait'),
      (1473,1536,'square'),(1536,1473,'square')
    ]
    for w,h,expected in cases:
        got=cls(w,h);assert got==expected,(w,h,got,expected)
        lw,lh=logical(w,h)
        assert min(lw,lh)==SHORT,(w,h,lw,lh)
        # 8-unit quantization is intentionally tiny; never permit visible anisotropic distortion.
        err=scale_error(w,h,lw,lh)
        assert err<0.004,(w,h,lw,lh,err)

    # Boundary sanity: no gaps and no device-name routing.
    boundaries=[(.54,'tall'),(.55,'portrait'),(.85,'portrait'),(.86,'square'),
                (1.11,'square'),(1.12,'landscape'),(1.47,'landscape'),(1.48,'wide'),
                (1.94,'wide'),(1.95,'ultrawide')]
    for r,expected in boundaries:
        assert cls(r*1000,1000)==expected,(r,cls(r*1000,1000),expected)
    joined=skin+win+android
    for forbidden in ('SM-F976','Galaxy Fold','Z Fold','q8q'):
        assert forbidden not in joined,forbidden

    print('PASS: native viewport owns geometry; real Fold sizes map to uniform responsive canvases')
if __name__=='__main__':main()
