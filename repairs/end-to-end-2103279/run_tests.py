import json,subprocess
from pathlib import Path
names=json.loads(Path('audit279/test-classes.json').read_text());args=['./gradlew','--no-daemon','--console=plain',':xbmc:testReleaseUnitTest']
for name in names:args+=['--tests',name]
with Path('audit279/android-product-tests.log').open('w') as f:
 p=subprocess.Popen(args,cwd='build279',stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 for line in p.stdout:print(line,end='',flush=True);f.write(line)
 raise SystemExit(p.wait())
