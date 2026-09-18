#!/usr/bin/env python3
"""Exact, reversible audit corrections after the original 2103162 preflight.

The locked 2103161 source is never edited. The original patch still runs first;
this stage checks full preimages, verifies the exact locally tested postimages,
retains originals, and updates the final source receipt used by the APK audit.
"""
from pathlib import Path
import argparse, hashlib, json

SOURCE_DIR = Path('tools/android/packaging/xbmc/src')
PREIMAGES = {
 'InfinityLiveActivity.java.in':'161cae1abb0fcfdfa640c617c6257b72497481dfd6f9fa4362f279cacc746da9',
 'InfinityCobraDeviceBridge.java.in':'e2df01ee33a991ed975ad2f4025f27708be5f8061b5e9cdb622c695dc4df994b',
 'CobraVisualTheme.java.in':'66918332ddc0f2b8505543cfc8d248606b3dc0de98f8940607dc6b5bd7928618',
 'CobraVisualCatalog.java.in':'5c02b52fc93029d538738911d3148b4f8bd0c29403b43f52321196ef63ed886e',
}
POSTIMAGES = {
 'InfinityLiveActivity.java.in':'16e75d481a662af6747260feab5f3377acd34f565274b7c768eeb293a8426640',
 'InfinityCobraDeviceBridge.java.in':'58668d619eced74015e84a872d1a398af55a17d83df3e7a6dd32ca0ff5c995d4',
 'CobraVisualTheme.java.in':'5716dae9799401c9ebe893e4008b1c6e6d3fd6d9abc6cade2826c280ef36d4bc',
 'CobraVisualCatalog.java.in':'d9411565610879ba810cb7e7a2d37026fa8519fac5204ae327aa3c11313ee7a0',
}

def digest(data): return hashlib.sha256(data).hexdigest()

def edit(text, changes):
    original=text; journal=[]
    for old,new in changes:
        if text.count(old)!=1: raise RuntimeError('Hardening anchor mismatch: '+repr(old[:110]))
        text=text.replace(old,new,1);journal.append((old,new))
    reverse=text
    for old,new in reversed(journal):
        if not new or reverse.count(new)!=1: raise RuntimeError('Hardening reverse anchor ambiguous')
        reverse=reverse.replace(new,old,1)
    if reverse!=original: raise RuntimeError('Hardening changed bytes outside exact edits')
    return text

CHANGES = {
 'InfinityLiveActivity.java.in': [
  ('  private CobraIconButton mCobraPlayerRotationButton;',
   '  private CobraIconButton mCobraPlayerRotationButton;\n  // Orientation can only be owned by a resumed, live fullscreen Activity.\n  private boolean mCobraRotationResumed=false;\n  private boolean mCobraRotationMultiWindow=false;'),
  ('    return pip||multiWindow||television||mBackgroundStopped;',
   '    return pip||mInPictureInPicture||multiWindow||mCobraRotationMultiWindow||television||mBackgroundStopped\n        ||!mCobraRotationResumed||!isCobraAsyncAlive();'),
  ('    cobraApplyPlayerRotation("resume");',
   '    mCobraRotationResumed=true;cobraApplyPlayerRotation("resume");'),
  ('    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"pause");',
   '    mCobraRotationResumed=false;cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"pause");'),
  ('    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"stop");',
   '    mCobraRotationResumed=false;cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"stop");'),
  ('    if(inMultiWindowMode)cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"multi-window-enter");else cobraApplyPlayerRotation("multi-window-exit");',
   '    mCobraRotationMultiWindow=inMultiWindowMode;\n    if(inMultiWindowMode)cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"multi-window-enter");else cobraApplyPlayerRotation("multi-window-exit");'),
  ('  private void cobraTogglePlayerRotation(){\n',
   '  private void cobraTogglePlayerRotation(){\n    if(mCobraPlayerLocked||mPlayerOverlay==null||!isCobraAsyncAlive())return;\n'),
  ('  @Override protected void onDestroy() {\n',
   '  @Override protected void onDestroy() {\n    mCobraRotationResumed=false;cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"destroy");mCobraPlayerRotationButton=null;\n'),
  ('  private void closeFullscreenToCobraView() {\n    if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}',
   '  private void closeFullscreenToCobraView() {\n    if(mCobraPlayerLocked){showCobraPlayerUnlockAffordance();return;}\n    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"fullscreen-preview");mCobraPlayerRotationButton=null;'),
  ('  private void openMultiView(List<Channel> channels) {\n    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"multi-view");mCobraPlayerRotationButton=null;\n    if(channels==null||channels.size()<2||channels.size()>4||!isCobraAsyncAlive())return;',
   '  private void openMultiView(List<Channel> channels) {\n    if(channels==null||channels.size()<2||channels.size()>4||!isCobraAsyncAlive())return;\n    cobraRequestPlayerOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED,"multi-view");mCobraPlayerRotationButton=null;'),
  ('    rows.addView(cobraSheetRow("source","Built-in appearance",',
   '    LinearLayout builtinRow=cobraSheetRow("source","Built-in appearance",'),
  ('          });\n        }));\n\n    rows.addView(cobraSheetRow("favorite","Installed visual theme",',
   '          });\n        });builtinRow.setTag("cobra_theme_builtin");rows.addView(builtinRow);\n\n    LinearLayout installedRow=cobraSheetRow("favorite","Installed visual theme",'),
  ('          });\n        }));\n\n    rows.addView(cobraSheetRow("add","Install / replace theme ZIP",\n        "Choose a Cobra visual-theme package",false,dark,()->openCobraUiPackagePicker()));',
   '          });\n        });installedRow.setTag("cobra_theme_installed");rows.addView(installedRow);\n\n    LinearLayout installRow=cobraSheetRow("add","Install / replace theme ZIP",\n        "Choose a Cobra visual-theme package",false,dark,()->openCobraUiPackagePicker());\n    installRow.setTag("cobra_theme_install");rows.addView(installRow);\n    // The sheet factory paints before rows are added; bind the completed subtree too.\n    vtheme().tree(rows,"sheet.theme-management");'),
  ('publishCobraUi(()->{toast("Visual theme installed. Reopen menus for layout changes; playback is not restarted.");if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&mPlayerOverlay==null&&mMultiOverlay==null){cobraRestyleGuide();cobraRenderGuideBrowser();}});',
   'publishCobraUi(()->{\n            status("Visual theme installed");toast("Visual theme installed. Playback is not restarted.");\n            if(mPlayerOverlay==null&&mMultiOverlay==null&&mStage!=null&&mStage.findViewWithTag("cobra_theme_management")!=null){showSettings();}\n            else if(mCobraGuideShell!=null&&mCobraGuideShell.isAttachedToWindow()&&mPlayerOverlay==null&&mMultiOverlay==null){cobraRestyleGuide();cobraRenderGuideBrowser();}\n          });'),
  ('  private int mCobraLastRequestedOrientation=Integer.MIN_VALUE;\n',
   '  // No separate Activity orientation cache; the device bridge owns it.\n'),
  ('  private void cobraRequestPlayerOrientation(int requested,String reason){\n    if(mCobraLastRequestedOrientation==requested)return;\n    try{\n      setRequestedOrientation(requested);\n      mCobraLastRequestedOrientation=requested;\n      android.util.Log.i("InfinityRotation","Cobra player rotation="\n          +(requested==android.content.pm.ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR?"unlocked":"follow-device")\n          +" reason="+reason);\n    }catch(IllegalStateException|SecurityException error){\n      android.util.Log.w("InfinityRotation","Android rejected Cobra player orientation request",error);\n    }\n  }',
   '  private void cobraRequestPlayerOrientation(int requested,String reason){\n    // InfinityCobraDeviceBridge is the one existing Activity orientation owner.\n    // Permission is sticky until recomputed, so its queued policy/window refreshes\n    // cannot re-enable rotation after a pause, exit or fullscreen handoff.\n    if(mDeviceBridge!=null)mDeviceBridge.setPlayerRotationEligible(\n        requested==android.content.pm.ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR,reason);\n  }'),
 ],
 'CobraVisualTheme.java.in': [
  ('static void reset(Context c)throws Exception{synchronized(STORE_LOCK){JSONObject old=readPointer(c),p=new JSONObject();p.put("active","");p.put("previous",old.optString("active",""));',
   'static void reset(Context c)throws Exception{synchronized(STORE_LOCK){JSONObject old=readPointer(c),p=new JSONObject();if(old.optString("active","").isEmpty())return;p.put("active","");p.put("previous",old.optString("active",""));'),
 ],
 'CobraVisualCatalog.java.in': [
  ('favorite_on|multi|lock|unlock|aspect|fullscreen','favorite_on|multi|lock|unlock|rotate|aspect|fullscreen'),
 ],
 'InfinityCobraDeviceBridge.java.in': [
  ('  private boolean paused;','  private boolean paused;\n  private boolean playerRotationEligible=false;'),
  ('  public int widthClass() {',
   '  /** Refresh rotation only. The existing bridge retains orientation ownership. */\n  public void setPlayerRotationEligible(boolean eligible,String reason) {\n    playerRotationEligible=eligible;\n    applyRotation(reason==null?"player-rotation":reason);\n  }\n\n  public int widthClass() {'),
  ('    boolean unlock = !paused && !television && !constrainedWindow() &&',
   '    boolean unlock = playerRotationEligible && !paused && !activity.isFinishing() && !activity.isDestroyed() && !television && !constrainedWindow() &&'),
  ('  public void close() {','  public void close() {\n    paused=true;playerRotationEligible=false;'),
 ],
}

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    pending={};proof={};originals={}
    receipt=json.loads(a.receipt.read_text())
    for name,expected in PREIMAGES.items():
        file=a.source/SOURCE_DIR/name;before=file.read_bytes()
        if digest(before)!=expected:raise RuntimeError('Not exact 2103162 hardening preimage: '+name+' '+digest(before))
        after=edit(before.decode(),CHANGES[name]).encode()
        if digest(after)!=POSTIMAGES[name]:raise RuntimeError('Locally tested postimage mismatch: '+name+' '+digest(after))
        pending[file]=after;originals[file]=before
        rel=str(SOURCE_DIR/name);proof[rel]={'before':digest(before),'after':digest(after),'exact_edits':len(CHANGES[name]),'reverse_proof':True}
        if rel in receipt['files']:receipt['files'][rel]['after']=digest(after)
        else:receipt['files'][rel]={'before':digest(before),'after':digest(after)}
    if b'setRequestedOrientation(' in pending[a.source/SOURCE_DIR/'InfinityLiveActivity.java.in']:
        raise RuntimeError('Duplicate Activity orientation requester')
    if pending[a.source/SOURCE_DIR/'InfinityCobraDeviceBridge.java.in'].count(b'activity.setRequestedOrientation(')!=1:
        raise RuntimeError('Expected exactly one device-bridge orientation requester')
    a.out.mkdir(parents=True,exist_ok=True)
    for file,before in originals.items():
        saved=a.out/'source-before'/file.name;saved.parent.mkdir(exist_ok=True);saved.write_bytes(before)
    try:
        for file,content in pending.items():file.write_bytes(content)
        receipt['hardening']={'single_existing_rotation_owner':True,'resumed_rotation_gate':True,'fullscreen_preview_release':True,'idempotent_theme_reset':True,'settings_install_refresh':True,'theme_row_roles':True,'native_changed':False}
        a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    except Exception:
        for file,before in originals.items():file.write_bytes(before)
        raise
    (a.out/'source-audit.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('PASS: exact hardening preimages/postimages +',sum(len(v) for v in CHANGES.values()),'reversible edits; one rotation owner; final receipt updated')
if __name__=='__main__':main()
