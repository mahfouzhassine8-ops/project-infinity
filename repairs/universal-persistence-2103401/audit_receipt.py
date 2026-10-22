"""Independent downloaded RC8 source/member/DEX audit, retaining the RC7 audit."""
import argparse,hashlib,importlib.util,json,os,pathlib,subprocess,sys,tempfile,zipfile
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser()
 for name in ['candidate','rc7','input','protected','overlay','jars','out']:p.add_argument('--'+name,type=pathlib.Path,required=True)
 for name in ['source-commit','build-run']:p.add_argument('--'+name,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 audit=load('native_member_audit',HERE/'audit_artifact.py');build=load('receipt_scope',HERE/'receipt_build.py');sha=build.sha
 subprocess.run([sys.executable,str(HERE/'audit_artifact.py'),'--candidate',str(a.rc7),'--input',str(a.input),'--protected',str(a.protected),'--overlay',str(a.overlay),'--out',str(a.out/'rc7-revalidated'),'--source-commit','d9edecbe843eb92457e26cbeab712f0264c55192','--build-run','39862996414'],check=True,stdout=subprocess.DEVNULL)
 r=json.loads((a.candidate/'CANDIDATE.json').read_text());assert r['source_commit']==a.source_commit and r['build_run']==a.build_run
 assert r['incremental_parent_sha256']==build.RC7 and r['native_sha256']==build.ENGINE and not r['physical_fold_verified'] and not r['final_lock']
 for line in (a.candidate/'SHA256SUMS').read_text().splitlines():
  pin,name=line.split('  ',1);assert pathlib.Path(name).name==name and audit.file_hash(a.candidate/name)==pin
 apks=list(a.candidate.glob('*.apk'));assert len(apks)==1;apk=apks[0];assert audit.file_hash(apk)==r['apk_sha256']
 rc7=list(a.rc7.glob('*.apk'));assert len(rc7)==1 and audit.file_hash(rc7[0])==build.RC7
 before=audit.members(rc7[0]);after=audit.members(apk);original=audit.members(a.input/'Infinity-2103401-Fold-Corrective-EXPERIMENTAL.apk')
 delta=[dict(path=n,before=before.get(n),after=after.get(n)) for n in sorted(before.keys()|after.keys()) if before.get(n)!=after.get(n)]
 assert {x['path'] for x in delta}=={'classes.dex','META-INF/INFINITY.RSA','META-INF/INFINITY.SF','META-INF/MANIFEST.MF'}
 assert delta==json.loads((a.candidate/'RC7-RC8-APK-DELTA.json').read_text())['changed']
 full=[dict(path=n,before=original.get(n),after=after.get(n)) for n in sorted(original.keys()|after.keys()) if original.get(n)!=after.get(n)]
 assert len(full)==6 and full==json.loads((a.candidate/'APK-DELTA.json').read_text())['changed']
 assert before['lib/arm64-v8a/libkodi.so']==after['lib/arm64-v8a/libkodi.so']==build.ENGINE
 source=json.loads((a.candidate/'NATIVE-SOURCE-MAP.json').read_text());assert source==json.loads((a.rc7/'NATIVE-SOURCE-MAP.json').read_text()) and len(source)==9404
 with zipfile.ZipFile(a.candidate/'Infinity-Universal-Source-and-Evidence.zip') as z:
  assert sorted(n[7:] for n in z.namelist() if n.startswith('native/'))==sorted(source)
  for n,pin in source.items():assert sha(z.read('native/'+n))==pin
  for name in ['InfinityCheckpointReceipt.java','PreserveReceiptDex.java','receipt_build.py','ReceiptRaceProbe.java']:
   assert z.read('repair/'+name)==(HERE/name).read_bytes(),name
 pins=json.loads((HERE/'RECEIPT-TOOL-PINS.json').read_text());assert {p.name:audit.file_hash(p) for p in a.jars.glob('*.jar')}==pins
 cp=os.pathsep.join(str(p.resolve()) for p in sorted(a.jars.glob('*.jar')))
 norm=load('existing_encoding_only_guard',ROOT/'repairs/cobra-clean-restart/bytecode_guard.py').normalize
 maps=[]
 with tempfile.TemporaryDirectory(prefix='receipt-dex-audit-') as d:
  d=pathlib.Path(d)
  for label,file in [('rc7',rc7[0]),('candidate',apk)]:
   dest=d/label;dest.mkdir()
   with zipfile.ZipFile(file) as z:(dest/'classes.dex').write_bytes(z.read('classes.dex'))
   subprocess.run(['java','-cp',cp,'org.jf.baksmali.Main','disassemble','--sequential-labels',str(dest/'classes.dex'),'-o',str(dest/'decoded')],check=True,stdout=subprocess.DEVNULL)
   maps.append(build.raw(dest/'decoded'))
  old,new=maps;assert set(new)==set(old)|build.ADDED
  changed=[n for n in old if norm(old[n])!=norm(new[n])];assert changed==[build.TARGET],changed
  assert new[build.TARGET].count(build.NEW)==6 and build.OLD not in new[build.TARGET]
  assert norm(old[build.TARGET])==norm(new[build.TARGET].replace(build.NEW,build.OLD))
  helper_hashes={n:sha(norm(new[n]).encode()) for n in build.ADDED}
 proof=json.loads((a.candidate/'DEX-PRESERVATION.json').read_text());assert proof['candidate_dex_sha256']==after['classes.dex'] and proof['changed_call_count']==6 and proof['changed_classes']==changed and set(proof['added_classes'])==build.ADDED
 gates=json.loads((a.candidate/'ACTUAL-ANDROID17-RECEIPT-GATES.json').read_text());assert gates['passed'] and gates['source_commit']==a.source_commit
 assert gates['input_hashes']['candidate.dex']==after['classes.dex'] and gates['input_hashes']['original.dex']==before['classes.dex']
 assert gates['results']['original']['actual_atomic_failures']>0 and gates['results']['candidate']['actual_atomic_failures']==0 and gates['results']['candidate']['negative_controls']==6
 result=dict(passed=True,source_commit=a.source_commit,build_run=a.build_run,candidate_apk_sha256=r['apk_sha256'],verified_native_sources=9404,native_rc7_engine_unchanged=True,
  input_apk_member_delta=full,rc7_incremental_member_delta=delta,changed_original_classes=changed,protected_original_classes=len(old)-1,
  original_coordinator_instructions_unchanged_except_six_call_targets=True,original_shared_protocol_and_installer_unchanged=True,
  added_class_semantic_hashes=helper_hashes,receipt_component_gates=gates,physical_fold_verified=False,final_lock=False)
 cumulative=json.loads((a.out/'rc7-revalidated/CUMULATIVE-2103400-DELTA.json').read_text())
 prior={x['path']:x for x in cumulative['apk_changed']}
 # The original protected-member hashes were independently checked above.
 for row in delta:
  n=row['path'];base=prior[n]['before'] if n in prior else row['before']
  if base==row['after']:prior.pop(n,None)
  else:prior[n]=dict(path=n,before=base,after=row['after'],origin='this repair changes parent member')
 cumulative.update(candidate_sha256=r['apk_sha256'],apk_changed=[prior[n] for n in sorted(prior)],
  java_scope=proof,scope='Protected 2103400 to RC8; pre-existing 2103401 changes distinguished')
 (a.out/'CUMULATIVE-2103400-DELTA.json').write_text(json.dumps(cumulative,indent=2)+'\n')
 (a.out/'INDEPENDENT-RC8-PRESERVATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,apk_sha256=r['apk_sha256'],changed_members=len(full),protected_classes=len(old)-1)))
if __name__=='__main__':main()
