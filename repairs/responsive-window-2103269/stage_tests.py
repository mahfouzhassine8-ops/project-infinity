from pathlib import Path
import argparse,subprocess,sys,shutil
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--inherited',action='store_true');a=p.parse_args();here=Path(__file__).parent
args=[sys.executable,str(here.parent/'display-player-2103268/stage_tests.py'),'--build',str(a.build),'--evidence',str(a.evidence)]
if a.inherited:args+=['--inherited']
subprocess.run(args,check=True)
out=a.build/'xbmc/src/test/java/com/projectinfinity/kodi';shutil.copy2(here/'ResponsiveWindowTest.java',out/'ResponsiveWindowTest.java')
with (a.build/'xbmc/build.gradle').open('a') as f:f.write('\nandroid.testOptions.unitTests.all { systemProperty "responsive.evidence", "'+str((a.evidence/'responsive').resolve())+'" }\n')
