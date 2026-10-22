"""Prepare and execute an isolated production-DEX receipt race on Android 17."""
import argparse,hashlib,json,os,pathlib,shlex,shutil,subprocess,zipfile
HERE=pathlib.Path(__file__).resolve().parent
def run(cmd,**kw):return subprocess.check_output([str(x) for x in cmd],text=True,stderr=subprocess.STDOUT,**kw)
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','android']);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();o=a.out
 if a.mode=='prepare':
  o.mkdir();inputs=o/'inputs';inputs.mkdir();apk=list(pathlib.Path('signed').glob('*.apk'));assert len(apk)==1
  assert hashlib.sha256(apk[0].read_bytes()).hexdigest()=='5b4519fa570ef80c0fbb9287c8cb09bd635f1e7babcbb82370e860de0c69643d'
  with zipfile.ZipFile(apk[0]) as z:
   for name in ['classes.dex','classes2.dex']:(inputs/name).write_bytes(z.read(name))
  android=pathlib.Path(os.environ['ANDROID_HOME']);jar=android/'platforms/android-34/android.jar';tools=android/'build-tools/34.0.0';classes=o/'classes';classes.mkdir()
  print(run(['javac','--release','8','-g:none','-Xlint:all,-options','-Werror','-cp',jar,'-d',classes,HERE/'ReceiptRaceProbe.java']))
  dex=o/'probe-dex';dex.mkdir();print(run([tools/'d8','--release','--min-api','26','--lib',jar,'--output',dex,*classes.glob('*.class')]))
  shutil.copyfile(dex/'classes.dex',inputs/'probe.dex')
  cp=pathlib.Path('receipt-tools-classpath.txt').read_text().strip();decoded=o/'decoded'
  for name in ['classes.dex','classes2.dex']:print(run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',inputs/name,'-o',decoded]))
  refs=[]
  for f in decoded.rglob('*.smali'):
   for line in f.read_text().splitlines():
    if 'InfinityCheckpointProtocol;->atomic(' in line:refs.append({'class':f.relative_to(decoded).as_posix(),'call':line.strip()})
  (o/'WRITER-CALLERS.json').write_text(json.dumps(refs,indent=2)+'\n')
  (o/'INPUTS.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in inputs.iterdir()},indent=2)+'\n')
  jars=o/'tool-jars';jars.mkdir()
  for name in cp.split(os.pathsep):shutil.copyfile(name,jars/pathlib.Path(name).name)
  shutil.copyfile(jar,o/'android-34.jar')
 else:
  devices=[s.split()[0] for s in run(['adb','devices']).splitlines()[1:] if s.endswith('\tdevice')];assert len(devices)==1 and devices[0].startswith('emulator-')
  assert run(['adb','shell','getprop','ro.kernel.qemu']).strip()=='1'
  assert run(['adb','shell','getprop','ro.build.version.sdk']).strip()=='37'
  target='/data/local/tmp/infinity-receipt-race-'+os.environ['GITHUB_RUN_ID']
  run(['adb','shell','mkdir',target]);run(['adb','push',str(o/'inputs')+'/.',target]);run(['adb','shell','chmod','444',target+'/probe.dex',target+'/classes.dex',target+'/classes2.dex'])
  cp=':'.join(target+'/'+x for x in ['probe.dex','classes.dex','classes2.dex'])
  result=run(['adb','shell','CLASSPATH='+shlex.quote(cp)+' /system/bin/app_process -Xverify:all /system/bin ReceiptRaceProbe '+shlex.quote(target+'/fixture')],timeout=90)
  (o/'ACTUAL-ANDROID17-RACE.log').write_text(result);print(result)
  rows=[x.removeprefix('RECEIPT_RACE_RESULT=') for x in result.splitlines() if x.startswith('RECEIPT_RACE_RESULT=')];assert len(rows)==1
  report=json.loads(rows[0]);assert report['passed'];report['source_commit']=os.environ['GITHUB_SHA'];report['apk_sha256']='5b4519fa570ef80c0fbb9287c8cb09bd635f1e7babcbb82370e860de0c69643d'
  (o/'ACTUAL-ANDROID17-RACE.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
