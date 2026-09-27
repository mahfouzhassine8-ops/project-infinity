#!/usr/bin/env python3
"""Stage all 28 previously-passed regression tests and their test-only harnesses.
Nothing here is part of the signed production APK.
"""
from pathlib import Path
import argparse,shutil,re

p=argparse.ArgumentParser()
p.add_argument('--build-dir',type=Path,required=True)
p.add_argument('--source257',type=Path,required=True)
p.add_argument('--source258',type=Path,required=True)
p.add_argument('--source259',type=Path,required=True)
p.add_argument('--source260',type=Path,required=True)
p.add_argument('--evidence',type=Path,required=True)
a=p.parse_args()

root=a.build_dir.resolve()
out=root/'xbmc/src/test/java/com/projectinfinity/kodi'
out.mkdir(parents=True,exist_ok=True)

def one(root:Path,name:str)->Path:
    hits=list(root.resolve().rglob(name))
    assert len(hits)==1,(name,[str(x) for x in hits])
    return hits[0]

# Exact test classes from the four previously-passed generations.
for source,name in [
    (a.source257,'GlassChooserTest.java'),
    (a.source258,'GlassOptionsTest.java'),
    (a.source259,'GlassHealthFinishTest.java'),
    (a.source260,'RecoveryFixedTest.java')]:
    shutil.copy2(one(source,name),out/name)

# Test-only Options harness, reconstructed from the preserved callback evidence.
original=one(a.source259,'Splash-before.java.in').read_text()
cb=one(a.source258,'settings-callback.java.inc').read_text()
constants=[]
for name in ['INFINITY_EXPERIENCE_PREFS','INFINITY_EXPERIENCE_DEFAULT']:
    match=re.search(r'private static final String '+name+r'\s*=\s*([^;]+);',original)
    assert match,name
    constants.append('  static final String '+name+' = '+match.group(1)+';')
options_harness='package com.projectinfinity.kodi;\npublic class OptionsActionHarness extends android.app.Activity {\n'+'\n'.join(constants)+'''
  String launched;int health,recovery;
  private void launchInfinityExperience(String experience){launched=experience;}
  private void showInfinityHealthCenter(){health++;}
  private void showCobraRecovery(){recovery++;}
  android.content.DialogInterface.OnClickListener listener(String experience){
    final boolean cobra="live".equals(experience);
    return '''+cb+''';
  }
}
'''
(out/'OptionsActionHarness.java').write_text(options_harness)

# Test-only Health harness from the exact preserved Health row/action body.
arrays=one(a.source259,'health-rows-and-actions.java.inc').read_text()
health_harness='''package com.projectinfinity.kodi;
public class HealthActionHarness extends android.app.Activity {
  String textTitle,textBody;int exports,copies;
  private void infinityShowHealthText(String title,String body){textTitle=title;textBody=body;}
  private String infinityHealthExitHistory(boolean trace){return "test exit history";}
  private String infinityHealthBuildInfo(){return "test build info";}
  private void infinityExportHealthReport(){exports++;}
  private void infinityCopyHealthReport(){copies++;}
  InfinityGlassHealth openHealth(boolean light){
    final InfinityGlassHealth dialog=new InfinityGlassHealth(this,"Infinity Health Center","DIAGNOSTICS  •  RECOVERY",()->light);
'''+arrays+'''
    dialog.menu(rows,actions);dialog.show();return dialog;
  }
}
'''
(out/'HealthActionHarness.java').write_text(health_harness)

# Test-only Recovery harness from the exact 2103260 preserved recovery method.
recovery_method=one(a.source260,'recovery-method.java.inc').read_text()
recovery_harness='''package com.projectinfinity.kodi;
public class RecoveryActionHarness extends android.app.Activity {
  boolean light,safe,once;int launches,restored;String launched;
  private void launchInfinityExperience(String name,boolean safe,boolean once){this.launched=name;this.safe=safe;this.once=once;launches++;}
  static final class CobraPresentationSafety {
    static void restoreBuiltIn(RecoveryActionHarness owner,Object unused){owner.restored++;}
  }
  private InfinityGlassRecovery.Builder cobraRecoveryDialog(){return new InfinityGlassRecovery.Builder(this,()->light,null,true);}
  void openRecovery(){showCobraRecovery();}
'''+recovery_method+'\n}\n'
(out/'RecoveryActionHarness.java').write_text(recovery_harness)

# Dependencies are appended only after the production APK has already compiled/signed.
with (root/'xbmc/build.gradle').open('a') as f:
    f.write('''\nandroid.testOptions.unitTests.includeAndroidResources = true
android.testOptions.unitTests.all {
    maxHeapSize = "3g"
    systemProperty "glass.evidence", "'''+str(a.evidence.resolve())+'''"
    testLogging { events "passed", "failed", "skipped"; exceptionFormat "full" }
}
dependencies {
    testImplementation 'junit:junit:4.13.2'
    testImplementation 'org.robolectric:robolectric:4.14.1'
}
''')
print('PASS: staged 28 locked UI regressions plus exact test-only Options/Health/Recovery harnesses')
