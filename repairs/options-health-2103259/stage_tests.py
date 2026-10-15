#!/usr/bin/env python3
from pathlib import Path
import argparse,shutil,re
p=argparse.ArgumentParser();p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
root=a.build_dir.resolve();here=Path(__file__).resolve().parent;project=Path.cwd()
out=root/'xbmc/src/test/java/com/projectinfinity/kodi';out.mkdir(parents=True,exist_ok=True)
shutil.copy2(project/'source258/repair-source/GlassOptionsTest.java',out/'GlassOptionsTest.java')
shutil.copy2(project/'source257/repair-source/GlassChooserTest.java',out/'GlassChooserTest.java')
shutil.copy2(here/'GlassHealthFinishTest.java',out/'GlassHealthFinishTest.java')
original=(project/'audit259/Splash-before.java.in').read_text();cb=(project/'source258/settings-callback.java.inc').read_text()
constants=[]
for name in ['INFINITY_EXPERIENCE_PREFS','INFINITY_EXPERIENCE_DEFAULT']:
    match=re.search(r'private static final String '+name+r'\s*=\s*([^;]+);',original);assert match,name
    constants.append('  static final String '+name+' = '+match.group(1)+';')
harness='package com.projectinfinity.kodi;\npublic class OptionsActionHarness extends android.app.Activity {\n'+'\n'.join(constants)+'''
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
(out/'OptionsActionHarness.java').write_text(harness)
arrays=(project/'audit259/health-rows-and-actions.java.inc').read_text()
health='''package com.projectinfinity.kodi;
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
(out/'HealthActionHarness.java').write_text(health)
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
