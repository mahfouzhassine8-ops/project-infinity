"""Isolated Infinity Close writer integration; retain the verified RC7 engine."""
import argparse,copy,difflib,hashlib,importlib.util,json,os,pathlib,re,shutil,subprocess,sys,zipfile
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
RC7='5b4519fa570ef80c0fbb9287c8cb09bd635f1e7babcbb82370e860de0c69643d'
ENGINE='a538ef1cca66a8841ba116e3af028fc76dcebecfcb94ac5db9a0405d023e3fc8'
DEX='9b12109c04ea99375685486e62afcb3e1e2b3beea01b1a87b8de1e2cff7f9603'
SECOND='d4df6604044e7cb66584229562186bf2ed8f0031d2d3efba03bba8ebe38934ca'
TARGET='com/projectinfinity/kodi/InfinityCloseGuardService.smali'
OLD='Lcom/projectinfinity/kodi/InfinityCheckpointProtocol;->atomic(Ljava/io/File;Lorg/json/JSONObject;)V'
NEW=OLD.replace('InfinityCheckpointProtocol','InfinityCheckpointReceipt')
ADDED={'com/projectinfinity/kodi/InfinityCheckpointReceipt.smali','com/projectinfinity/kodi/InfinityCheckpointReceipt$Descriptor.smali'}
def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def run(args,**kw):
 r=subprocess.run([str(x) for x in args],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**kw);print(r.stdout,flush=True);r.check_returncode();return r.stdout
def raw(root):return {p.relative_to(root).as_posix():p.read_text() for p in root.rglob('*.smali')}
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def tools():
 sdk=pathlib.Path(os.environ['ANDROID_HOME']);return sdk/'platforms/android-34/android.jar',sdk/'build-tools/34.0.0'
def baseline():
 files=list(pathlib.Path('signed').glob('*.apk'));assert len(files)==1 and sha(files[0].read_bytes())==RC7
 for line in pathlib.Path('signed/SHA256SUMS').read_text().splitlines():
  pin,name=line.split('  ',1);assert pathlib.Path(name).name==name and sha((pathlib.Path('signed')/name).read_bytes())==pin
 proof=json.load(open('signed/CANDIDATE.json'));assert proof['source_commit']=='d9edecbe843eb92457e26cbeab712f0264c55192' and proof['native_sha256']==ENGINE
 return files[0]
def prepare(o):
 apk=baseline();assert not o.exists();o.mkdir();w=o/'work';w.mkdir();inputs=o/'inputs';inputs.mkdir();jar,bt=tools()
 cp=os.pathsep.join(str(x.resolve()) for x in sorted(pathlib.Path('investigation/receipt-evidence/tool-jars').glob('*.jar')));assert cp
 (o/'classpath.txt').write_text(cp)
 with zipfile.ZipFile(apk) as z:
  for name,pin in [('classes.dex',DEX),('classes2.dex',SECOND)]:
   data=z.read(name);assert sha(data)==pin;(inputs/('original.dex' if name=='classes.dex' else name)).write_bytes(data)
 source=w/'source';source.mkdir();classes=w/'classes';classes.mkdir()
 shutil.copyfile(HERE/'InfinityCheckpointReceipt.java',source/'InfinityCheckpointReceipt.java')
 (source/'InfinityCheckpointEvidence.java').write_text('package com.projectinfinity.kodi; final class InfinityCheckpointEvidence { static void mirror(java.io.File f,org.json.JSONObject r){} }\n')
 run(['javac','--release','8','-g:none','-Xlint:all,-options','-Werror','-cp',jar,'-d',classes,*source.glob('*.java')])
 produced=[p for p in classes.rglob('*.class') if p.name.startswith('InfinityCheckpointReceipt')]
 assert {p.name for p in produced}=={'InfinityCheckpointReceipt.class','InfinityCheckpointReceipt$Descriptor.class'}
 helper=w/'helper-dex';helper.mkdir()
 run([bt/'d8','--release','--min-api','21','--lib',jar,'--output',helper,*produced])
 decoded=w/'original-smali';hd=w/'helper-smali'
 for dex,out in [(inputs/'original.dex',decoded),(helper/'classes.dex',hd)]:run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',dex,'-o',out])
 old=raw(decoded);helpers=raw(hd);assert set(helpers)==ADDED and not set(old)&ADDED
 original=old[TARGET];assert sha(original.encode())=='72feadffca6798a3d558e48e9c52021c662f0899f5af29dc872add6991760b18'
 assert original.count(OLD)==6 and NEW not in original
 changed=original.replace(OLD,NEW);assert changed.replace(NEW,OLD)==original
 methods=re.findall(r'(?ms)^\.method [^\n]*\n.*?^\.end method',original)
 callers=[m.splitlines()[0] for m in methods if OLD in m];assert len(callers)==6
 modified=w/'modified-smali';shutil.copytree(decoded,modified);(modified/TARGET).write_text(changed)
 for name,body in helpers.items():(modified/name).write_text(body)
 assembled=w/'assembled.dex';final=inputs/'candidate.dex'
 run(['java','-cp',cp,'org.jf.smali.Main','assemble','--api','21',modified,'-o',assembled])
 adapter=w/'adapter';adapter.mkdir()
 run(['javac','--release','8','-g:none','-cp',cp,'-d',adapter,HERE/'PreserveReceiptDex.java'])
 field_log=run(['java','-cp',str(adapter)+os.pathsep+cp,'org.jf.dexlib2.writer.pool.PreserveReceiptDex',inputs/'original.dex',assembled,final,'21'])
 (o/'EXACT-FIELDS.log').write_text(field_log)
 assert 'PRESERVED_CLASSES='+str(len(old)-1) in field_log
 fields=sum(len(re.findall(r'^\.field ',s,re.M)) for s in old.values());assert 'VERIFIED_EXACT_FIELD_DEFINITIONS='+str(fields) in field_log
 verified=w/'verified-smali';run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',final,'-o',verified]);after=raw(verified)
 # Reuse the existing strict encoding-only comparison, without editing it.
 guard=load('existing_encoding_guard',ROOT/'repairs/cobra-clean-restart/bytecode_guard.py');guard.selftest();norm=guard.normalize
 assert set(after)==set(old)|ADDED
 differences=[n for n in old if norm(old[n])!=norm(after[n])];assert differences==[TARGET],differences
 assert norm(after[TARGET].replace(NEW,OLD))==norm(original)
 assert all(norm(after[n])==norm(helpers[n]) for n in ADDED)
 assert after[TARGET].count(NEW)==6 and OLD not in after[TARGET]
 (o/'JAVA-CALLSITE.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),'input/'+TARGET,'candidate/'+TARGET)))
 shutil.copyfile(HERE/'InfinityCheckpointReceipt.java',o/'InfinityCheckpointReceipt.java')
 for name in ADDED:(o/pathlib.Path(name).name).write_text(after[name])
 report=dict(source_commit=os.environ['GITHUB_SHA'],parent_apk_sha256=RC7,original_dex_sha256=DEX,candidate_dex_sha256=sha(final.read_bytes()),
  changed_classes=[TARGET],added_classes=sorted(ADDED),changed_callsite_methods=callers,changed_call_count=6,
  all_other_original_class_definitions_preserved=True,original_field_definitions_verified=fields,protected_classes=len(old)-1,
  original_protocol_and_installer_unchanged=True,other_dex_sha256=SECOND,
  unchanged_native_engine_sha256=ENGINE,native_build_commit='d9edecbe843eb92457e26cbeab712f0264c55192',native_build_run=39862996414,
  helper_java_sha256=sha((HERE/'InfinityCheckpointReceipt.java').read_bytes()),physical_fold_verified=False,final_lock=False)
 save(o/'DEX-PRESERVATION.json',report)
 pc=w/'probe-classes';pc.mkdir();run(['javac','--release','8','-g:none','-Xlint:all,-options','-Werror','-cp',jar,'-d',pc,HERE/'ReceiptRaceProbe.java'])
 pd=w/'probe-dex';pd.mkdir();run([bt/'d8','--release','--min-api','21','--lib',jar,'--output',pd,*pc.glob('*.class')]);shutil.copyfile(pd/'classes.dex',inputs/'probe.dex')
 save(o/'INPUTS.json',{x.name:sha(x.read_bytes()) for x in inputs.iterdir()})
def android(o):
 import shlex
 pins=json.load(open(o/'INPUTS.json'));assert {x.name:sha(x.read_bytes()) for x in (o/'inputs').iterdir()}==pins
 devices=[s.split()[0] for s in run(['adb','devices']).splitlines()[1:] if s.endswith('\tdevice')];assert len(devices)==1 and devices[0].startswith('emulator-')
 assert run(['adb','shell','getprop','ro.kernel.qemu']).strip()=='1' and run(['adb','shell','getprop','ro.build.version.sdk']).strip()=='37'
 target='/data/local/tmp/infinity-receipt-candidate-'+os.environ['GITHUB_RUN_ID'];run(['adb','shell','mkdir',target]);run(['adb','push',str(o/'inputs')+'/.',target]);run(['adb','shell','chmod','444',*[target+'/'+n for n in pins]])
 reports={}
 for variant in ['original','candidate']:
  cp=':'.join(target+'/'+x for x in ['probe.dex',variant+'.dex','classes2.dex'])
  result=run(['adb','shell','CLASSPATH='+shlex.quote(cp)+' /system/bin/app_process -Xverify:all /system/bin ReceiptRaceProbe '+shlex.quote(target+'/fixture-'+variant)+' '+variant],timeout=90)
  (o/(variant+'-ANDROID17.log')).write_text(result)
  rows=[s.removeprefix('RECEIPT_RACE_RESULT=') for s in result.splitlines() if s.startswith('RECEIPT_RACE_RESULT=')];assert len(rows)==1;reports[variant]=json.loads(rows[0]);assert reports[variant]['passed']
 assert reports['original']['actual_atomic_failures']>0 and reports['candidate']['actual_atomic_failures']==0 and reports['candidate']['negative_controls']==6
 save(o/'ACTUAL-ANDROID17-RECEIPT-GATES.json',dict(passed=True,source_commit=os.environ['GITHUB_SHA'],input_hashes=pins,results=reports,physical_fold_verified=False))
def package(o):
 parent=baseline();proof=json.load(open(o/'DEX-PRESERVATION.json'));gate=json.load(open(o/'ACTUAL-ANDROID17-RECEIPT-GATES.json'));assert gate['passed'] and gate['source_commit']==proof['source_commit']==os.environ['GITHUB_SHA']
 dex=(o/'inputs/candidate.dex').read_bytes();assert sha(dex)==proof['candidate_dex_sha256']==gate['input_hashes']['candidate.dex']
 sys.path.insert(0,str(HERE));import package as prior
 delivery=prior.delivery;assert all(os.environ.get(k) for k in delivery.KEYS),'Permanent signer required'
 _,bt=tools();signature_before=delivery.verify_signature(parent,bt);unsigned=o/'unsigned.apk';signed=o/'Infinity-2103401-Universal-Persistence-RC8-NOT-ACCEPTED.apk'
 with zipfile.ZipFile(parent) as a,zipfile.ZipFile(unsigned,'w',allowZip64=True) as b:
  for info in a.infolist():
   if not prior.SIGNATURE.fullmatch(info.filename):b.writestr(copy.copy(info),dex if info.filename=='classes.dex' else a.read(info))
 prior.delta(parent,unsigned,{'classes.dex':dex});run(['bash',ROOT/'scripts/sign-infinity71.sh',unsigned,signed]);signature=delivery.verify_signature(signed,bt)
 incremental=prior.delta(parent,signed,{'classes.dex':dex});unsigned.unlink();badging=delivery.command([bt/'aapt','dump','badging',signed]);assert "versionCode='2103401'" in badging and 'application-debuggable' not in badging
 receipt=dict(source_commit=os.environ['GITHUB_SHA'],build_run=os.environ['GITHUB_RUN_ID'],protected_baseline=2103400,parent_sha256=prior.PARENT,
  incremental_parent_sha256=RC7,apk_sha256=sha(signed.read_bytes()),native_sha256=ENGINE,native_engine_recompiled=False,
  native_build_commit=proof['native_build_commit'],native_build_run=proof['native_build_run'],permanent_certificate_sha256=delivery.CERT,signature_schemes_verified=[1,2,3],
  changed_payload_members=['classes.dex',prior.ENGINE,prior.RECORDER],java_change_scope='Six Infinity Close coordinator call targets and two new receipt helper classes only',
  assets_manifest_other_libraries_byte_identical=True,provider_code_changed=False,user_profile_changed=False,android_receipt_component_validated=True,
  android_full_close_validated=False,physical_fold_verified=False,final_lock=False,distribution='INTERNAL QA ONLY; not accepted')
 out=pathlib.Path('internal-qa');assert not out.exists();out.mkdir();shutil.move(signed,out/signed.name)
 save(out/'CANDIDATE.json',receipt);save(out/'RC7-RC8-APK-DELTA.json',incremental)
 # Preserve full input-relative member hashes with the exact extra DEX delta.
 original=json.load(open('signed/APK-DELTA.json'));hashes={x['path']:x['sha256'] for x in original['byte_identical_members']};hashes.update({x['path']:x['before'] for x in original['changed']})
 changes=[];same=[]
 with zipfile.ZipFile(out/signed.name) as z:
  assert set(z.namelist())==set(hashes)
  for name in sorted(hashes):
   digest=sha(z.read(name))
   if digest==hashes[name]:same.append(dict(path=name,sha256=digest))
   else:changes.append(dict(path=name,before=hashes[name],after=digest))
 assert {x['path'] for x in changes}=={'classes.dex',prior.ENGINE,prior.RECORDER,'META-INF/INFINITY.RSA','META-INF/INFINITY.SF','META-INF/MANIFEST.MF'}
 save(out/'APK-DELTA.json',dict(changed=changes,byte_identical_members=same,signing_block='verified separately'))
 for n in ['NATIVE-SOURCE-MAP.json','SOURCE-DELTA.json','ENGINE-PROOF.json','UNIVERSAL-TESTS.json','EXISTING-REGRESSIONS.json']:shutil.copyfile(pathlib.Path('signed')/n,out/n)
 for n in ['DEX-PRESERVATION.json','ACTUAL-ANDROID17-RECEIPT-GATES.json','JAVA-CALLSITE.patch','EXACT-FIELDS.log']:shutil.copyfile(o/n,out/n)
 (out/'RC7-SIGNATURE.txt').write_text(signature_before);(out/'FINAL-SIGNATURE.txt').write_text(signature);(out/'APK-BADGING.txt').write_text(badging)
 with zipfile.ZipFile('signed/Infinity-Universal-Source-and-Evidence.zip') as a,zipfile.ZipFile(out/'Infinity-Universal-Source-and-Evidence.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as b:
  pins=json.load(open('signed/NATIVE-SOURCE-MAP.json'));assert len(pins)==9404
  for name,pin in pins.items():
   data=a.read('native/'+name);assert sha(data)==pin;b.writestr('native/'+name,data)
  for p in HERE.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:b.write(p,'repair/'+p.relative_to(HERE).as_posix())
  for p in out.iterdir():
   if p.suffix in ('.json','.txt','.patch','.log'):b.write(p,'receipts/'+p.name)
 (out/'SHA256SUMS').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file()))
 print(json.dumps(receipt,indent=2))
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','android','package']);p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('receipt-candidate'));a=p.parse_args();globals()[a.mode](a.out)
if __name__=='__main__':main()
