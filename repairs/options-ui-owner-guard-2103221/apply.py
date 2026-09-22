#!/usr/bin/env python3
"""2103221: restore premium chooser option UI and enforce drawer-owned section at Live TV fallback.

Parent: successful 2103220.
Scope:
- Replace both Infinity and Cobra gear option dialogs with an in-app Infinity-style surface.
- Preserve every existing option/action and Smart Return placement/implementation.
- Add a central guard so legacy primary/Live-TV fallbacks cannot override a non-Live drawer owner.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

VERSION=2103221
OLD_VERSION=2103220
OLD_NAME='1.0.9-Cobra-Active-Section-Lifecycle-RC1'
NEW_NAME='1.0.9-Cobra-Options-UI-Owner-Guard-RC1'
SOURCE='tools/android/packaging/xbmc/src/'
NATIVE='db92b30f5523cacd9029aa21d7b52c8bc7819e4cd5c1dea76d4bfcdcf9205375'

def hb(b): return hashlib.sha256(b).hexdigest()
def sha(p): return hb(Path(p).read_bytes())
def req(v,m):
    if not v: raise RuntimeError(m)
def once(s,a,b,label):
    req(s.count(a)==1,f'{label} anchor drift ({s.count(a)})')
    return s.replace(a,b,1)

def method_span(text,name):
    matches=list(re.finditer(
        r'^  (?:(?:@Override(?:[ \t]*\n  |[ \t]+))?)(?:public|private|protected) [^\n;=(){}]*\b'
        +re.escape(name)+r'\s*\(',text,re.M))
    req(len(matches)==1,f'Method cardinality {name}={len(matches)}')
    start=matches[0].start();i=text.index('{',matches[0].end());depth=0;quote=None;escape=line=block=False
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if line:
            if c=='\n': line=False
        elif block:
            if c=='*' and n=='/': block=False;i+=1
        elif quote:
            if escape: escape=False
            elif c=='\\': escape=True
            elif c==quote: quote=None
        elif c=='/' and n=='/': line=True;i+=1
        elif c=='/' and n=='*': block=True;i+=1
        elif c in ('"',"'"): quote=c
        elif c=='{': depth+=1
        elif c=='}':
            depth-=1
            if depth==0: return start,i+1
        i+=1
    raise RuntimeError('Unclosed '+name)

def method(text,name):
    a,b=method_span(text,name);return text[a:b]
def replace_method(text,name,new):
    a,b=method_span(text,name);return text[:a]+new.rstrip()+'\n'+text[b:]

SPLASH_PROTECT=[
 'showInfinityHealthCenter',
 'infinityShowHealthText',
 'infinityHealthExitHistory',
 'infinityHealthReport',
 'showInfinityExperienceChooser',
 'showStyledInfinityExperienceChooser',
 'chooserExperienceCard',
]
ACTIVITY_PROTECT=[
 'cobraRefreshAmbient',
 'cobraApplyNightCinema',
 'cobraShowVodDetails',
 'openSeries',
 'startSinglePlayer',
 'playChannel',
 'cobraStartLocalTimeshift',
 'loadXtream',
 'loadM3u',
 'showSettings',
 'cobraShowSmartReturnSetting',
 'cobraTrySmartReturn',
 'cobraSaveSmartReturn',
]
def hashes(text,names): return {n:hb(method(text,n).encode()) for n in names}

ROW_HELPER=r'''  private android.widget.LinearLayout chooserOptionRow(
      android.app.Dialog dialog,String tag,String title,String detail,int accent,Runnable action)
  {
    final int textColor=android.graphics.Color.parseColor("#F4F8FF");
    final int mutedColor=android.graphics.Color.parseColor("#91A4BB");
    final int rowFill=android.graphics.Color.parseColor("#111F2F");
    final int rowLine=android.graphics.Color.parseColor("#2B4157");
    android.widget.LinearLayout row=new android.widget.LinearLayout(this);
    row.setOrientation(android.widget.LinearLayout.HORIZONTAL);
    row.setGravity(android.view.Gravity.CENTER_VERTICAL);
    row.setPadding(chooserDp(16),chooserDp(10),chooserDp(12),chooserDp(10));
    row.setMinimumHeight(chooserDp(66));
    row.setFocusable(true);row.setClickable(true);row.setTag(tag);
    row.setBackground(chooserSurface(rowFill,rowLine,16));

    android.widget.LinearLayout copy=new android.widget.LinearLayout(this);
    copy.setOrientation(android.widget.LinearLayout.VERTICAL);
    android.widget.TextView heading=chooserStyledText(title,textColor,15,true,android.view.Gravity.START);
    heading.setLetterSpacing(.02f);copy.addView(heading,new android.widget.LinearLayout.LayoutParams(-1,-2));
    if(detail!=null&&!detail.isEmpty()){
      android.widget.TextView sub=chooserStyledText(detail,mutedColor,11,false,android.view.Gravity.START);
      android.widget.LinearLayout.LayoutParams sp=new android.widget.LinearLayout.LayoutParams(-1,-2);
      sp.topMargin=chooserDp(3);copy.addView(sub,sp);
    }
    row.addView(copy,new android.widget.LinearLayout.LayoutParams(0,-2,1));
    android.widget.TextView arrow=chooserStyledText("›",accent,24,false,android.view.Gravity.CENTER);
    arrow.setImportantForAccessibility(android.view.View.IMPORTANT_FOR_ACCESSIBILITY_NO);
    row.addView(arrow,new android.widget.LinearLayout.LayoutParams(chooserDp(28),chooserDp(38)));
    row.setOnFocusChangeListener((v,focused)->v.setBackground(
        chooserSurface(rowFill,focused?accent:rowLine,16)));
    row.setOnClickListener(v->{dialog.dismiss();action.run();});
    return row;
  }
'''

OPTIONS_METHOD=r'''  private void showExperienceCardSettings(String experience)
  {
    final boolean cobra="live".equals(experience);
    final String label=cobra?"Cobra":"Infinity";
    final int accent=android.graphics.Color.parseColor(cobra?"#2FD7E9":"#B59A5A");
    final int panelFill=android.graphics.Color.parseColor("#09131F");
    final int textColor=android.graphics.Color.parseColor("#F4F8FF");
    final int mutedColor=android.graphics.Color.parseColor("#91A4BB");

    final android.app.Dialog dialog=new android.app.Dialog(this);
    dialog.requestWindowFeature(android.view.Window.FEATURE_NO_TITLE);

    android.widget.LinearLayout panel=new android.widget.LinearLayout(this);
    panel.setOrientation(android.widget.LinearLayout.VERTICAL);
    panel.setPadding(chooserDp(18),chooserDp(18),chooserDp(18),chooserDp(14));
    panel.setTag(cobra?"experience-options-cobra":"experience-options-infinity");
    panel.setBackground(chooserSurface(panelFill,accent,24));

    android.widget.LinearLayout headingRow=new android.widget.LinearLayout(this);
    headingRow.setOrientation(android.widget.LinearLayout.HORIZONTAL);
    headingRow.setGravity(android.view.Gravity.CENTER_VERTICAL);
    ExperienceMark mark=new ExperienceMark(cobra,accent);
    headingRow.addView(mark,new android.widget.LinearLayout.LayoutParams(chooserDp(58),chooserDp(42)));
    android.widget.LinearLayout headingCopy=new android.widget.LinearLayout(this);
    headingCopy.setOrientation(android.widget.LinearLayout.VERTICAL);
    android.widget.TextView heading=chooserStyledText(label+" options",textColor,21,true,android.view.Gravity.START);
    heading.setLetterSpacing(.05f);headingCopy.addView(heading);
    android.widget.TextView subtitle=chooserStyledText(
        cobra?"Cobra launch, recovery and diagnostics":"Infinity launch and diagnostics",
        mutedColor,11,false,android.view.Gravity.START);
    android.widget.LinearLayout.LayoutParams subtitleLp=new android.widget.LinearLayout.LayoutParams(-1,-2);
    subtitleLp.topMargin=chooserDp(2);headingCopy.addView(subtitle,subtitleLp);
    android.widget.LinearLayout.LayoutParams headingCopyLp=new android.widget.LinearLayout.LayoutParams(0,-2,1);
    headingCopyLp.leftMargin=chooserDp(10);headingRow.addView(headingCopy,headingCopyLp);
    panel.addView(headingRow,new android.widget.LinearLayout.LayoutParams(-1,-2));

    android.view.View line=new android.view.View(this);
    line.setBackgroundColor((accent&0x00ffffff)|0x55000000);
    android.widget.LinearLayout.LayoutParams lineLp=new android.widget.LinearLayout.LayoutParams(-1,chooserDp(1));
    lineLp.topMargin=chooserDp(14);lineLp.bottomMargin=chooserDp(10);panel.addView(line,lineLp);

    Runnable remember=()->{
      getSharedPreferences(INFINITY_EXPERIENCE_PREFS,MODE_PRIVATE).edit()
          .putString(INFINITY_EXPERIENCE_DEFAULT,experience).apply();
      launchInfinityExperience(experience);
    };
    Runnable onceLaunch=()->launchInfinityExperience(experience);
    Runnable ask=()->{
      getSharedPreferences(INFINITY_EXPERIENCE_PREFS,MODE_PRIVATE).edit()
          .remove(INFINITY_EXPERIENCE_DEFAULT).apply();
      android.widget.Toast.makeText(this,
          "Infinity will ask which experience to open next time.",
          android.widget.Toast.LENGTH_SHORT).show();
    };

    android.widget.LinearLayout rememberRow=chooserOptionRow(dialog,
        "experience-option-remember","Remember & launch "+label,
        "Make "+label+" the default experience",accent,remember);
    panel.addView(rememberRow,new android.widget.LinearLayout.LayoutParams(-1,-2));

    android.widget.LinearLayout launchRow=chooserOptionRow(dialog,
        "experience-option-once","Launch "+label+" just this time",
        "Open now without changing your default",accent,onceLaunch);
    android.widget.LinearLayout.LayoutParams itemLp=new android.widget.LinearLayout.LayoutParams(-1,-2);
    itemLp.topMargin=chooserDp(8);panel.addView(launchRow,itemLp);

    android.widget.LinearLayout askRow=chooserOptionRow(dialog,
        "experience-option-ask","Ask every time",
        "Show Choose Your Experience at the next launch",accent,ask);
    android.widget.LinearLayout.LayoutParams askLp=new android.widget.LinearLayout.LayoutParams(-1,-2);
    askLp.topMargin=chooserDp(8);panel.addView(askRow,askLp);

    android.widget.LinearLayout healthRow=chooserOptionRow(dialog,
        "experience-option-health","Infinity Health Center",
        "Crashes, exits, diagnostics and device information",accent,this::showInfinityHealthCenter);
    android.widget.LinearLayout.LayoutParams healthLp=new android.widget.LinearLayout.LayoutParams(-1,-2);
    healthLp.topMargin=chooserDp(8);panel.addView(healthRow,healthLp);

    if(cobra){
      android.widget.LinearLayout recoveryRow=chooserOptionRow(dialog,
          "experience-option-recovery","Cobra Recovery",
          "Recovery tools without changing your normal Cobra settings",accent,this::showCobraRecovery);
      android.widget.LinearLayout.LayoutParams recoveryLp=new android.widget.LinearLayout.LayoutParams(-1,-2);
      recoveryLp.topMargin=chooserDp(8);panel.addView(recoveryRow,recoveryLp);
    }

    android.widget.TextView cancel=chooserStyledText("CANCEL",accent,13,true,android.view.Gravity.CENTER);
    cancel.setFocusable(true);cancel.setClickable(true);cancel.setTag("experience-options-cancel");
    cancel.setBackground(chooserSurface(android.graphics.Color.TRANSPARENT,accent,14));
    cancel.setOnClickListener(v->dialog.dismiss());
    android.widget.LinearLayout.LayoutParams cancelLp=new android.widget.LinearLayout.LayoutParams(-1,chooserDp(46));
    cancelLp.topMargin=chooserDp(12);panel.addView(cancel,cancelLp);

    dialog.setContentView(panel);
    android.view.Window window=dialog.getWindow();
    if(window!=null){
      window.setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(android.graphics.Color.TRANSPARENT));
      window.addFlags(android.view.WindowManager.LayoutParams.FLAG_DIM_BEHIND);
      android.view.WindowManager.LayoutParams attrs=window.getAttributes();
      attrs.dimAmount=.68f;window.setAttributes(attrs);
    }
    dialog.setCanceledOnTouchOutside(true);
    dialog.show();
    window=dialog.getWindow();
    if(window!=null){
      int screen=getResources().getDisplayMetrics().widthPixels;
      int width=Math.min(screen-chooserDp(28),chooserDp(520));
      window.setLayout(Math.max(chooserDp(280),width),android.view.WindowManager.LayoutParams.WRAP_CONTENT);
      window.setGravity(android.view.Gravity.CENTER);
    }
    rememberRow.requestFocus();
  }'''

def patch_splash(path):
    s=path.read_text();before=hashes(s,SPLASH_PROTECT)
    req('chooserOptionRow(' not in s,'Options helper already exists')
    a,_=method_span(s,'showExperienceCardSettings')
    s=s[:a]+ROW_HELPER+'\n'+s[a:]
    s=replace_method(s,'showExperienceCardSettings',OPTIONS_METHOD)
    m=method(s,'showExperienceCardSettings')
    req('android.app.AlertDialog.Builder' not in m,'Stock Android options dialog survived')
    req('CobraVisualRenderer.DialogBuilder' not in m,'Legacy themed AlertDialog survived')
    for token in (
        'experience-options-cobra','experience-options-infinity',
        'experience-option-remember','experience-option-once','experience-option-ask',
        'experience-option-health','experience-option-recovery',
        'Remember & launch ','Launch ','Ask every time',
        'showInfinityHealthCenter','showCobraRecovery'
    ):
        req(token in s,'Options UI contract missing: '+token)
    req('Smart Return' not in m and 'cobra_smart_return' not in m,
        'Smart Return leaked back into chooser gear options')
    path.write_text(s)
    req(hashes(s,SPLASH_PROTECT)==before,'Protected chooser/Health behavior changed')

def add_owner_guard_to_method(text,name,guard):
    m=method(text,name)
    brace=m.find('{')
    req(brace>=0,'No method body for '+name)
    if '2103221 drawer-owner guard' in m: return text
    new=m[:brace+1]+'\n'+guard+m[brace+1:]
    return replace_method(text,name,new)

def patch_activity(path):
    s=path.read_text();before=hashes(s,ACTIVITY_PROTECT)
    req('COBRA_ACTIVE_SECTION_PREF' in s and 'cobraReturnToActiveSection()' in s,
        '2103220 active-section owner missing')
    primary_guard='''    // 2103221 drawer-owner guard: old primary fallback may not override the drawer-selected section.
    if(mPrefs!=null&&mStage!=null&&!COBRA_SECTION_LIVE.equals(cobraActiveSection())){
      cobraReturnToActiveSection();return;
    }
'''
    live_guard='''    // 2103221 drawer-owner guard: Live TV may become top-level only after a Live TV drawer selection.
    if(mPrefs!=null&&mStage!=null&&!COBRA_SECTION_LIVE.equals(cobraActiveSection())){
      cobraReturnToActiveSection();return;
    }
'''
    s=add_owner_guard_to_method(s,'showCobraPrimaryView',primary_guard)
    s=add_owner_guard_to_method(s,'cobraOpenLiveTv',live_guard)

    # The preference write remains exactly drawer-owned.
    req(s.count('cobraSelectActiveSection(destination);')==1,
        'Active section owner has a writer outside the drawer')
    drawer=method(s,'cobraDrawerDestination')
    req('cobraSelectActiveSection(destination);' in drawer,'Drawer owner write lost')
    for token in ('2103221 drawer-owner guard','showCobraPrimaryView','cobraOpenLiveTv'):
        req(token in s,'Owner guard contract missing: '+token)
    path.write_text(s)
    req(hashes(s,ACTIVITY_PROTECT)==before,'Smart Return/playback/settings behavior changed')

def identity(shell):
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';g=gradle.read_text()
    g=once(g,f'versionCode {OLD_VERSION}',f'versionCode {VERSION}','versionCode')
    g=once(g,'versionName "'+OLD_NAME+'"','versionName "'+NEW_NAME+'"','versionName')
    gradle.write_text(g)
    runtime=Path('scripts/infinity_background_resume.py');r=runtime.read_text()
    r=once(r,f'VERSION_CODE = {OLD_VERSION}',f'VERSION_CODE = {VERSION}','runtime code')
    r=once(r,"RELEASE = '"+OLD_NAME+"'","RELEASE = '"+NEW_NAME+"'",'runtime name')
    runtime.write_text(r)
    pack=Path('scripts/package_background_resume.py');p=pack.read_text()
    old='Infinity-'+OLD_NAME;new='Infinity-'+NEW_NAME
    req(p.count(old)>=2,'packager identity drift')
    pack.write_text(p.replace(old,new))
    return gradle

def apply(shell):
    receipt_path=Path('engine/background-resume-source.json')
    receipt=json.loads(receipt_path.read_text())
    req(receipt.get('version_code')==OLD_VERSION and receipt.get('version_name')==OLD_NAME,
        'Expected exact successful 2103220 replay')

    activity=shell/(SOURCE+'InfinityLiveActivity.java.in')
    splash=shell/(SOURCE+'Splash.java.in')
    smart=shell/(SOURCE+'CobraSmartReturn.java.in')
    main=shell/(SOURCE+'Main.java.in')
    for p in (activity,splash,smart,main): req(p.is_file(),'Missing '+str(p))

    smart_before=sha(smart);main_before=sha(main)
    patch_splash(splash);patch_activity(activity);gradle=identity(shell)
    req(sha(smart)==smart_before,'Smart Return file changed')
    req(sha(main)==main_before,'Kodi Main changed')
    req(receipt.get('native_engine_sha256')==NATIVE,'Native engine drift')

    for name in (SOURCE+'InfinityLiveActivity.java.in',SOURCE+'Splash.java.in',
                 SOURCE+'CobraSmartReturn.java.in',SOURCE+'Main.java.in'):
        req(name in receipt['files'],'Receipt missing '+name)
        receipt['files'][name]['after']=sha(shell/name)
    rel='tools/android/packaging/xbmc/build.gradle.in'
    receipt['files'][rel]['after']=sha(gradle)
    receipt.update(
        version_code=VERSION,version_name=NEW_NAME,source_parent=OLD_VERSION,
        candidate_locked=False,physical_device_verified=False,runtime_device_tested=False,
        native_engine_rebuilt=False,native_engine_reused_from_2103209=True,native_engine_sha256=NATIVE,
        chooser_options_custom_ui=True,chooser_options_stock_alertdialog=False,
        infinity_options_custom_ui=True,cobra_options_custom_ui=True,
        chooser_option_actions_preserved=True,smart_return_untouched=True,
        smart_return_file_sha256=smart_before,
        active_section_owner=True,active_section_changes_only_from_drawer=True,
        primary_live_fallback_owner_guard=True,cobra_open_live_owner_guard=True,
        media_return_context_preserved=True,live_tv_blue_ambient_unchanged=True,
        health_center_unchanged=True,playback_unchanged=True,providers_unchanged=True
    )
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    for name,row in receipt['files'].items():
        req(sha(shell/name)==row['after'],'Receipt drift '+name)

    Path('audit221').mkdir(exist_ok=True)
    Path('audit221/scope.json').write_text(json.dumps({
        'build':VERSION,'parent':OLD_VERSION,
        'infinity_options_custom_ui':True,'cobra_options_custom_ui':True,
        'stock_alert_dialog_removed_from_experience_options':True,
        'preserved_actions':['Remember & launch','Launch just this time','Ask every time',
                             'Infinity Health Center','Cobra Recovery (Cobra only)'],
        'smart_return_untouched':True,'smart_return_sha256':smart_before,
        'active_section_changes_only_from_drawer':True,
        'legacy_primary_live_fallback_guarded':True,
        'cobra_open_live_guarded':True,
        'acceptance':[
          'Infinity gear opens dark Infinity-styled options surface',
          'Cobra gear opens dark Cobra/Infinity-styled options surface',
          'No white stock Android options dialog',
          'Drawer > Movies; Android exit/back/reopen Cobra => Movies',
          'Drawer > TV Shows; Android exit/back/reopen Cobra => TV Shows',
          'Only a top-level drawer selection changes active section'
        ],
        'native_engine_rebuilt':False,'playback_unchanged':True,
        'providers_unchanged':True,'health_center_unchanged':True,
        'status':'TEST CANDIDATE'
    },indent=2)+'\n')
    print('PASS: 2103221 options UI restored and active-section Live TV fallback centrally guarded')

def main():
    p=argparse.ArgumentParser();p.add_argument('--shell',type=Path,required=True)
    apply(p.parse_args().shell)
if __name__=='__main__':main()
