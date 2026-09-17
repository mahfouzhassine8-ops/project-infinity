#!/usr/bin/env python3
"""2103153: fail-closed source transform over the exact locked 2103152 Android Activity.

No native Kodi, Infinity skin, resource-ID, signer, or JNI edits. Source fragments
are ordinary reviewed Java. Preimages, changed method list and hashes are emitted.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from infinity_cobra_2103152_player_reboot_lock import method_end

ROOT=Path(__file__).resolve().parents[1]
LIVE=Path('tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in')
BASE_SHA='3a41d3c81a15e79cc4cfa1803675225824e915e6d42e002802aff68fe43ad666'
PARTS=('core','epg','sheets','guide','multiview','player','integration')

def method_span(text: str,name: str)->tuple[int,int]:
    pattern=r'^  (?:(?:private|protected|public|static|final|synchronized)\s+)+[^;={}\n]*?\b'+re.escape(name)+r'\s*\([^;{}]*?\)\s*(?:throws\s+[^{}]+)?\{'
    matches=list(re.finditer(pattern,text,re.M))
    if len(matches)!=1:raise RuntimeError(f'{name}: expected one method, found {len(matches)}')
    a=matches[0].start();return a,method_end(text,a)

def patch(text: str)->tuple[str,dict]:
    if hashlib.sha256(text.encode()).hexdigest()!=BASE_SHA:raise RuntimeError('Not the exact locked 2103152 generated Activity; refuse mixed preimages')
    before=text;changed=[];appended=[]
    for part in PARTS:
        content=(ROOT/'patches/infinity-cobra-2103153'/f'{part}.java').read_text()
        for match in re.finditer(r'^// COBRA-(APPEND|REPLACE(?: \w+)?)\n(.*?)(?=^// COBRA-|\Z)',content,re.M|re.S):
            action,body=match.groups()
            if action=='APPEND':appended.append(body.rstrip());continue
            name=action.split()[1];a,b=method_span(text,name)
            if name in changed:raise RuntimeError('Duplicate replacement '+name)
            text=text[:a]+body.rstrip()+text[b:];changed.append(name)
    def edit(name,old,new):
        nonlocal text
        a,b=method_span(text,name);block=text[a:b]
        if block.count(old)!=1:raise RuntimeError(f'{name}: unique insertion anchor missing: {old[:60]}')
        text=text[:a]+block.replace(old,new,1)+text[b:]
        if name not in changed:changed.append(name)
    def at_start(name,code):
        a,b=method_span(text,name);block=text[a:b];brace=block.index('{')
        edit(name,block,block[:brace+1]+'\n'+code+block[brace+1:])
    edit('loadXtream','    String statusValue = userInfo.optString("status", "");','    mPrefs.edit().putInt("cobra_provider_limit:"+source.id,Math.max(0,userInfo.optInt("max_connections",0))).apply();\n    String statusValue = userInfo.optString("status", "");')
    at_start('parseM3u' ,'    captureCobraPlaylistGuide(source,data);')
    at_start('onDestroy','    closeCobraAsyncWork();\n    mMain.removeCallbacks(mCobraUiTick);\n    mCobraGuideReadIo.shutdownNow();\n    mMain.removeCallbacks(mHideChrome);\n    closeCobraSheet();\n    closePlayerSettingsDrawer();\n    stopCobraPreviewPlayerOnly();')
    at_start('closePlayer','    closeCobraSheet();\n    closePlayerSettingsDrawer();\n    mMain.removeCallbacks(mStallWatchdog);\n    mMain.removeCallbacks(mHideChrome);')
    at_start('playVodUrl','    stopCobraPreviewPlayerOnly();')
    at_start('returnToInfinity','    stopCobraPreviewPlayerOnly();')
    edit('pauseCobraForBackground','    rememberAndPauseCobraPlayer(mPlayer);','    rememberAndPauseCobraPlayer(mPlayer);\n    rememberAndPauseCobraPlayer(mCobraPreviewPlayer);\n    rememberAndPauseCobraPlayer(mCobraTransferPlayer);')
    # Compact top-level shell frees useful height on cover screens without touching its navigation contracts.
    edit('buildShell','    mStage.setPadding(dp(isCompact() ? 12 : 22), dp(14),\n        dp(isCompact() ? 12 : 22), dp(14));','    mStage.setPadding(dp(8), dp(4), dp(8), dp(4));')
    edit('buildShell','        LinearLayout.LayoutParams.MATCH_PARENT, dp(62));','        LinearLayout.LayoutParams.MATCH_PARENT, dp(48));')
    edit('buildShell','    headerParams.bottomMargin = dp(8);','    headerParams.bottomMargin = dp(2);')
    edit('buildShell','        LinearLayout.LayoutParams.MATCH_PARENT, dp(38));','        LinearLayout.LayoutParams.MATCH_PARENT, dp(24));')
    edit('buildShell','    statusParams.bottomMargin = dp(10);','    statusParams.bottomMargin = dp(4);')
    edit('buildShell','    mStatus.setPadding(dp(16), dp(6), dp(16), dp(6));','    mStatus.setPadding(dp(10), 0, dp(10), 0);\n    mStatus.setSingleLine(true);\n    mStatus.setEllipsize(android.text.TextUtils.TruncateAt.END);')
    edit('buildShell','    mHeader.setPadding(dp(18), dp(8), dp(18), dp(8));','    mHeader.setPadding(dp(12), dp(4), dp(12), dp(4));\n    mHeader.setTextSize(18);')
    # The lock guard consumes keys deliberately; pressing OK twice exposes then activates Unlock.
    edit('ensureCobraPlayerLockOverlay','        showCobraPlayerUnlockAffordance();\n        return true;','        boolean visible=mCobraPlayerUnlockButton!=null && mCobraPlayerUnlockButton.getVisibility()==View.VISIBLE;\n        if (visible && (keyCode==KeyEvent.KEYCODE_DPAD_CENTER || keyCode==KeyEvent.KEYCODE_ENTER)) unlockCobraPlayer();\n        else showCobraPlayerUnlockAffordance();\n        return true;')
    end=text.rfind('}')
    text=text[:end]+'\n\n'+'\n\n'.join(appended)+'\n'+text[end:]
    # Fail closed if any legacy EPG consumer was missed.
    if 'mGuidePrograms.get(' in text:raise RuntimeError('Unmigrated in-memory guide consumer remains')
    for method in ('isCobraAsyncAlive','submitCobraIo','publishCobraUi','closeCobraAsyncWork','onPause','onResume','onStop','startCobraPlayer','rememberAndPauseCobraPlayer','resumeCobraAfterBackground','saveVodProgress','playCatchup','showTrackChooser'):
        a,b=method_span(before,method);c,d=method_span(text,method)
        if before[a:b]!=text[c:d]:raise RuntimeError('Protected method changed: '+method)
    receipt={'baseline_activity_sha256':BASE_SHA,'after_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'changed_methods':sorted(changed),'native_changes':False,'device_runtime_acceptance':'required',
        'source_parts':{name:hashlib.sha256((ROOT/'patches/infinity-cobra-2103153'/f'{name}.java').read_bytes()).hexdigest() for name in PARTS}}
    return text,receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,default=Path('preflight/cobra-2103153-source-audit.json'));args=p.parse_args()
    file=args.source/LIVE;text,receipt=patch(file.read_text());file.write_text(text)
    args.receipt.parent.mkdir(parents=True,exist_ok=True);args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS: exact 2103152 preimage transformed; persistent guide/session source audit emitted')
if __name__=='__main__':main()
