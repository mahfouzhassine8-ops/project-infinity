#!/usr/bin/env python3
"""Apply audited Cobra 2103153 UI/guide/session delta to exact locked 2103152.

Only InfinityLiveActivity changes. Kodi C/C++, Main, platform bridge, signing,
source URLs/credentials, recording services and Infinity skin stay outside it.
The baseline SHA is an exact preimage guard, not a permissive textual matcher.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from infinity_cobra_2103152_player_reboot_lock import method_end

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASELINE_SHA256 = '3a41d3c81a15e79cc4cfa1803675225824e915e6d42e002802aff68fe43ad666'
MODULES = ('common', 'guide-data', 'guide-ui', 'playback', 'multi', 'player-ui', 'lifecycle')


def method_span(text: str, name: str) -> tuple[int, int]:
    pattern = re.compile(r'^  (?:@Override(?:[ \t]*\n  |[ \t]+))?(?:private|public|protected) [^\n;=(){}]*\b' + re.escape(name) + r'\s*\(', re.M)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f'{name}: expected one method, found {len(matches)}')
    return matches[0].start(), method_end(text, matches[0].start())


def inject(text: str, name: str, anchor: str, replacement: str) -> str:
    a,b = method_span(text,name)
    block = text[a:b]
    if block.count(anchor) != 1:
        raise RuntimeError(f'{name}: exact hook preimage mismatch')
    return text[:a] + block.replace(anchor,replacement,1) + text[b:]


def patch(text: str) -> tuple[str, list[str]]:
    actual = hashlib.sha256(text.encode('utf-8')).hexdigest()
    if actual != BASELINE_SHA256:
        raise RuntimeError(f'Locked 2103152 preimage mismatch: {actual}')
    modules = ROOT / 'patches/cobra-2103153'
    fields = (modules / 'fields.java.inc').read_text(encoding='utf-8')
    anchor = '  private final Handler mMain = new Handler(Looper.getMainLooper());\n'
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor + fields + '\n',1)
    changed: list[str] = []
    additions: list[str] = []
    for module in MODULES:
        raw = (modules / (module+'.java.inc')).read_text(encoding='utf-8')
        parts = re.split(r'^// @(replace [A-Za-z0-9_]+|append)\s*\n',raw,flags=re.M)
        if parts[0].strip() or len(parts)%2 != 1:
            raise RuntimeError(f'{module}: invalid module markers')
        for label,block in zip(parts[1::2],parts[2::2]):
            if label == 'append':
                additions.append(block.strip('\n'))
                continue
            name = label.split()[1]
            if name in changed:
                raise RuntimeError(f'Duplicate replacement: {name}')
            a,b = method_span(text,name)
            text = text[:a] + block.rstrip() + '\n' + text[b:]
            changed.append(name)
    pos = text.rfind('\n}')
    if pos<0: raise RuntimeError('Outer Activity terminator missing')
    text = text[:pos] + '\n\n' + '\n\n'.join(additions) + text[pos:]
    text = inject(text,'loadM3u','    String playlist = httpGet(source.playlistUrl);',
                  '    String playlist = httpGet(source.playlistUrl);\n    cobraDiscoverPlaylistGuide(source,playlist);')
    text = inject(text,'closePlayer','    clearCobraPlayerLockState(false);',
                  '    closeCobraActionSheet();closeCobraPlayerDrawer();closeCobraMultiPicker(true);\n    mMain.removeCallbacks(mHideChrome);mMain.removeCallbacks(mStallWatchdog);\n    clearCobraPlayerLockState(false);')
    text = inject(text,'closePlayer','    mPlayerChrome = null;',
                  '    mPlayerChrome = null;\n    mCobraPlayerProgram=null;mCobraPlayerSchedule=null;mCobraPlayerUpcoming=null;mCobraPlayerProgramProgress=null;')
    text = inject(text,'resumeCobraAfterBackground','    mBackgroundStopped = false;',
                  '    mBackgroundStopped = false;\n    cobraStartPresentationTicker();')
    # Integration checks found two presentation details that must not regress:
    # retain direct preview captions, and undock the canvas after selecting an added tile.
    text = inject(text,'cobraPreviewPanel',
                  '    for(Button b:new Button[]{pause,fav,mute,more,full})',
                  '    CobraIconButton captions=cobraIcon("cc","Preview captions",true,v->toggleCobraPreviewCaptions());\n'
                  '    for(Button b:new Button[]{pause,fav,captions,mute,more,full})')
    text = inject(text,'rebuildCobraMultiPreservingSessions',
                  '    setMultiAudio(audio);cobraLayoutMultiTiles();cobraStartPresentationTicker();',
                  '    setMultiAudio(audio);cobraLayoutPlayerPanels();cobraLayoutMultiTiles();cobraStartPresentationTicker();')
    text = inject(text,'startCobraPreview',
                  '}catch(Exception failure){setCobraPreviewLabel("Preview unavailable");}',
                  '}catch(Exception failure){stopCobraPreviewPlayerOnly();setCobraPreviewLabel("Preview unavailable");}')
    text = inject(text,'startSinglePlayer',
                  '}catch(Exception error){showError("Playback failed",',
                  '}catch(Exception error){releaseSinglePlayer();showError("Playback failed",')
    # A healthy complete XMLTV schedule takes precedence over a short fallback.
    text = inject(text,'cobraResolveEpg',
                  '    if(data.programs.containsKey("@stream:"+channel.id))key="@stream:"+channel.id;\n'
                  '    else if(!epg.isEmpty()&&data.programs.containsKey(epg))key=epg;',
                  '    if(!epg.isEmpty()&&data.programs.containsKey(epg))key=epg;')
    text = inject(text,'cobraResolveEpg',
                  '    mCobraResolvedEpg.put(channel.id,key);return key;',
                  '    if(key.isEmpty()&&data.programs.containsKey("@stream:"+channel.id))key="@stream:"+channel.id;\n'
                  '    mCobraResolvedEpg.put(channel.id,key);return key;')
    # Long viewing sessions refresh the guide too, not only navigation/launch.
    marker = '        mCobraLastTickerMinute = minute;\n'
    assert text.count(marker) == 1
    text = text.replace(marker, marker +
        '        for(LiveSource source:mSources)if(mFeatures.sourceEnabled(source.id))loadGuideAsync(source);\n'
        '        if(mGuidePreviewChannel!=null)cobraRequestShortEpg(mGuidePreviewChannel);\n'
        '        if(mPlaying!=null)cobraRequestShortEpg(mPlaying);\n', 1)
    changed += ['loadM3u','closePlayer','resumeCobraAfterBackground']
    verify(text)
    return text,changed


def verify(text: str) -> None:
    for name in ('openPlayerOverlay','programFor','showGuideGrid','loadGuideAsync','rebuildCobraMultiPreservingSessions','releaseMulti'):
        method_span(text,name)
    def body(name: str) -> str:
        a,b = method_span(text,name); return text[a:b]
    for name in ('cobraLayoutMultiTiles','cobraLayoutPlayerPanels','cobraLayoutGuide','cobraRenderGuideBrowser','setMultiAudio'):
        value=body(name)
        for forbidden in ('.prepare(','.release(','.stop(','.pause(','.setMediaItem(','.setVideoTextureView(','.clearVideoTextureView('):
            if forbidden in value: raise RuntimeError(f'{name}: forbidden playback mutation {forbidden}')
    if 'releaseMulti(' in body('rebuildCobraMultiPreservingSessions'):
        raise RuntimeError('Whole Multi-View teardown remains in reflow')
    for name in ('showPlayerSettingsDrawer','showCobraMultiTileActions','showProgramGuide','showCobraAspectPicker','showTrackChooser'):
        if 'new AlertDialog' in body(name): raise RuntimeError(name+': stock dialog remains')
    settings=body('showPlayerSettingsDrawer')
    for forbidden in ('beginMultiView','showGuide','showProgramGuide'):
        if forbidden in settings: raise RuntimeError('Duplicate player settings destination: '+forbidden)
    if 'showCobraPrimaryView' in body('loadGuideAsync'):
        raise RuntimeError('EPG refresh still rebuilds the player screen')
    for token in ('cobra_persistent_guide_shell','cobra_player_channel_drawer','cobra_player_refined_chrome','CobraTileStore<CobraVideoTile>',
                  'Guide HTTP ','requiredNow','requiredNext','start_timestamp','cobraPruneShortGuideCache','Unlock controls'):
        if token not in text: raise RuntimeError('Missing contract: '+token)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--receipt',type=Path)
    args=parser.parse_args()
    live=args.source.resolve()/LIVE
    before=live.read_text(encoding='utf-8')
    after,changed=patch(before)
    # No writes until every preimage and postcondition has passed.
    live.write_text(after,encoding='utf-8')
    receipt={'baseline':2103152,'candidate':2103153,'before_sha256':BASELINE_SHA256,
             'after_sha256':hashlib.sha256(after.encode()).hexdigest(),'changed_methods':changed,
             'native_engine_changed':False,'device_playback_verified':False,
             'remaining_device_gate':['three/four streams and provider connection limit','portrait/cover/Fold touch','EPG source coverage']}
    if args.receipt:
        args.receipt.parent.mkdir(parents=True,exist_ok=True)
        args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS: exact 2103152 delta applied; guide, player drawer, themed sheets and stable Multi-View source verified')

if __name__=='__main__': main()
