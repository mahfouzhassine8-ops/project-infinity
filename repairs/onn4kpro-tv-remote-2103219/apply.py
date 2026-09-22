#!/usr/bin/env python3
"""2103219 onn. 4K Pro / Google TV remote responsiveness pass.

Parent: exact 2103218 TV source.
Scope: TV-only Android presentation/input responsiveness. No mobile/Fold changes.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

VERSION=2103219
OLD_VERSION=2103218
OLD_NAME='1.0.9-Cobra-Onn4KPro-TV-ARMv7-RC1'
NEW_NAME='1.0.9-Cobra-Onn4KPro-TV-Remote-RC2'
SOURCE='tools/android/packaging/xbmc/'

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(path): return sha_bytes(Path(path).read_bytes())
def require(v,m):
    if not v: raise RuntimeError(m)
def once(text,old,new,label):
    require(text.count(old)==1,f'{label} anchor drift ({text.count(old)})')
    return text.replace(old,new,1)

def apply(shell:Path):
    receipt_path=Path('engine/background-resume-source.json')
    receipt=json.loads(receipt_path.read_text())
    require(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
            'Expected exact 2103218 TV source replay')
    require(receipt.get('tv_variant') is True and receipt.get('tv_target_abi')=='armeabi-v7a',
            'Expected exact ARMv7 TV parent')

    gradle=shell/(SOURCE+'build.gradle.in')
    live=shell/(SOURCE+'src/InfinityLiveActivity.java.in')
    manifest=shell/(SOURCE+'AndroidManifest.xml.in')
    for p in (gradle,live,manifest):
        require(p.is_file(),'Missing TV source input: '+str(p))

    g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','TV remote versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','TV remote versionName')
    gradle.write_text(g)

    s=live.read_text()

    s=once(
        s,
        'static final long MICRO=120L, PANEL=190L, STAGGER=22L;',
        'static final long MICRO=55L, PANEL=95L, STAGGER=6L;',
        'TV motion spec'
    )

    old_focus='''private void cobraPolishFocusable(View view){
    if(view==null)return;
    view.setOnFocusChangeListener((v,focused)->{
      float stateAlpha=v.getAlpha();cobraResetMotion(v);
      if(!v.isEnabled()){v.setAlpha(stateAlpha);return;}
      if(!cobraMotionEnabled()){v.setScaleX(focused?1.018f:1f);v.setScaleY(focused?1.018f:1f);v.setAlpha(focused?1f:.97f);return;}
      v.animate().setStartDelay(0L).scaleX(focused?1.018f:1f).scaleY(focused?1.018f:1f)
          .alpha(focused?1f:.97f).setDuration(focused?CobraMotionSpec.MICRO:100L)
          .setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
    });
  }'''
    new_focus='''private void cobraPolishFocusable(View view){
    if(view==null)return;
    view.setFocusable(true);view.setFocusableInTouchMode(false);
    view.setOnFocusChangeListener((v,focused)->{
      float stateAlpha=v.getAlpha();cobraResetMotion(v);
      if(!v.isEnabled()){v.setAlpha(stateAlpha);return;}
      // TV remote fast path: focus must move on the key event, not after a focus animation.
      v.setScaleX(focused?1.012f:1f);v.setScaleY(focused?1.012f:1f);v.setAlpha(focused?1f:.985f);
    });
  }'''
    s=once(s,old_focus,new_focus,'TV immediate focus')

    old_inspect='private void cobraInspectProgramme(Channel channel,GuideProgram program){mCobraInspectedChannel=channel;mCobraInspectedProgram=program;cobraRefreshModeDetails();}'
    new_inspect='''private static final String COBRA_TV_REMOTE_BUILD="cobra_tv_remote_optimized_2103219";
  private Channel mCobraTvPendingInspectChannel;
  private GuideProgram mCobraTvPendingInspectProgram;
  private final Runnable mCobraTvApplyProgrammeFocus=()->{
    Channel channel=mCobraTvPendingInspectChannel;GuideProgram program=mCobraTvPendingInspectProgram;
    if(channel==null)return;
    mCobraInspectedChannel=channel;mCobraInspectedProgram=program;cobraRefreshModeDetails();
  };
  private void cobraInspectProgramme(Channel channel,GuideProgram program){
    mCobraTvPendingInspectChannel=channel;mCobraTvPendingInspectProgram=program;
    mMain.removeCallbacks(mCobraTvApplyProgrammeFocus);
    mMain.postDelayed(mCobraTvApplyProgrammeFocus,45L);
  }'''
    s=once(s,old_inspect,new_inspect,'TV guide focus debounce')

    s=once(
        s,
        'Math.min(i*CobraMotionSpec.STAGGER,66L)).setDuration(160L)',
        'Math.min(i*CobraMotionSpec.STAGGER,18L)).setDuration(90L)',
        'TV child entrance motion'
    )

    drawer_anchor='boolean grouped="cobra_drawer_navigation_group".equals(parent.getTag());row.setMinimumHeight(dp(56));row.setPadding(dp(10),dp(8),dp(10),dp(8));'
    drawer_new='boolean grouped="cobra_drawer_navigation_group".equals(parent.getTag());row.setFocusable(true);row.setFocusableInTouchMode(false);row.setClickable(true);row.setMinimumHeight(dp(56));row.setPadding(dp(10),dp(8),dp(10),dp(8));'
    s=once(s,drawer_anchor,drawer_new,'TV drawer D-pad focus')

    live.write_text(s)

    require('cobra_tv_remote_optimized_2103219' in s,'TV remote marker missing')
    require('postDelayed(mCobraTvApplyProgrammeFocus,45L)' in s,'TV guide debounce missing')
    require('v.setScaleX(focused?1.012f:1f)' in s,'TV immediate focus missing')
    require('PANEL=95L' in s and 'STAGGER=6L' in s,'TV motion tuning missing')
    require('row.setFocusable(true);row.setFocusableInTouchMode(false);row.setClickable(true)' in s,
            'TV drawer focus contract missing')

    for rel in (SOURCE+'build.gradle.in',SOURCE+'src/InfinityLiveActivity.java.in'):
        require(rel in receipt['files'],'Source receipt missing '+rel)
        receipt['files'][rel]['after']=sha(shell/rel)

    receipt.update(
        version_code=VERSION,
        version_name=NEW_NAME,
        source_parent=OLD_VERSION,
        candidate_locked=False,
        physical_device_verified=False,
        runtime_device_tested=False,
        tv_variant=True,
        tv_target='onn. 4K Pro / Google TV',
        tv_target_abi='armeabi-v7a',
        tv_remote_optimized=True,
        tv_remote_focus_immediate=True,
        tv_guide_focus_debounce_ms=45,
        tv_motion_micro_ms=55,
        tv_motion_panel_ms=95,
        tv_motion_stagger_ms=6,
        mobile_parent_untouched=True,
        same_package=True,
        same_signer_required=True,
        playback_feature_set_preserved=True,
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')

    for name,row in receipt['files'].items():
        require(sha(shell/name)==row['after'],'Final 2103219 source receipt drift: '+name)

    Path('audit219').mkdir(exist_ok=True)
    Path('audit219/tv-remote-source.json').write_text(json.dumps({
        'build':VERSION,
        'version_name':NEW_NAME,
        'parent_build':OLD_VERSION,
        'target':'onn. 4K Pro / Google TV',
        'target_abi':'armeabi-v7a',
        'scope':'TV-only Cobra remote responsiveness',
        'mobile_fold_untouched':True,
        'focus_animation_on_dpad':False,
        'guide_focus_debounce_ms':45,
        'motion_micro_ms':55,
        'motion_panel_ms':95,
        'motion_stagger_ms':6,
        'drawer_remote_focusable':True,
        'marker':'cobra_tv_remote_optimized_2103219',
        'physical_device_verified':False,
    },indent=2,sort_keys=True)+'\n')
    print('PASS: 2103219 TV-only Cobra remote responsiveness source applied; arm64/mobile untouched')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--shell',type=Path,required=True)
    a=p.parse_args()
    apply(a.shell)

if __name__=='__main__':
    main()
