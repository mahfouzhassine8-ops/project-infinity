"""Compile the isolated Cast component, not an installer or signing workflow.

The official SDK and its private support dependencies are optimized together by
the Android build tools. Existing APK classes/resources are never input program
code. Reject every class-name collision with the exact accepted APK. Generated
resource identifiers live in package 0x80; original 0x7f resources are untouched.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib,json,os,re,shutil,struct,subprocess,sys
from dex_contract import Dex, class_contract
from provided_http import obtain as provided_http
import private_classes

HERE=Path(__file__).resolve().parent
WORK=Path(sys.argv[1]).resolve();APK=Path(sys.argv[2]).resolve()
SDK=WORK/'tools';DEPS=WORK/'maven';OUT=WORK/'component-reuse86';OUT.mkdir(exist_ok=True)
assert hashlib.file_digest(APK.open('rb'),'sha256').hexdigest()=='550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197'
baseline={}
with ZipFile(APK) as z:
 for n in z.namelist():
  if re.fullmatch(r'classes\d*\.dex',n):baseline.update(Dex(z.read(n)).classes)
proof=json.loads((DEPS/'SDK-DEPENDENCIES.json').read_text())
provided=provided_http(WORK)
build_inputs={p.relative_to(HERE.parent).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for p in list(HERE.glob('*.py'))+list((HERE/'tooling').glob('*.java'))+
              [HERE.parent/'research'/name for name in ('CAST-SDK-DEPENDENCIES.json','CAST-PROVIDED-HTTP-APIS.json','CAST-BUILD-ONLY-SHADER.json')]}
(OUT/'BUILD-SOURCES.json').write_text(json.dumps(build_inputs,indent=2)+'\n')
def run(args):subprocess.run([str(x) for x in args],check=True)
program=[];resources=[];packages=[];consumer=[]
for row in proof['artifacts']:
 src=DEPS/row['file'];assert hashlib.sha256(src.read_bytes()).hexdigest()==row['sha256']
 if row['type']=='jar':
  jars=OUT/'jars';jars.mkdir(exist_ok=True);local=jars/(row['coordinate'].replace(':','_')+'.jar')
  local.write_bytes(src.read_bytes())
  # Kotlin/HTTP/Guava belong to Cobra in the accepted payload. Cast must
  # have private program definitions, never import those existing classes.
  # Use the exact newer private Kotlin required by Okio, not SDK's older
  # transitive Kotlin. Nothing in the accepted DEX is upgraded/relabelled.
  if not row['coordinate'].startswith('org.jetbrains.kotlin:'):program.append(local)
  continue
 folder=OUT/row['coordinate'].replace(':','_');folder.mkdir(exist_ok=True)
 with ZipFile(src) as z:
  for n in z.namelist():
   if n.endswith('/') or not (n in ('AndroidManifest.xml','classes.jar','proguard.txt') or n.startswith(('res/','META-INF/proguard/'))):continue
   p=folder/n;assert folder in p.resolve().parents;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
  if (folder/'classes.jar').exists():program.append(folder/'classes.jar')
  text=(folder/'AndroidManifest.xml').read_text()
  package=re.search(r'\bpackage="([A-Za-z0-9_.]+)"',text)
  if package:packages.append(package.group(1))
  if (folder/'res').is_dir():
   archive=folder/'flat.zip';run([SDK/'aapt2','compile','--dir',folder/'res','-o',archive]);resources.append(archive)
  if (folder/'proguard.txt').exists():consumer.append(folder/'proguard.txt')
  consumer.extend((folder/'META-INF/proguard').glob('*'))
manifest=OUT/'AndroidManifest.xml'
manifest.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.projectinfinity.cast.resources"><uses-sdk android:minSdkVersion="30"/><application android:hasCode="false"/></manifest>')
generated=OUT/'generated';generated.mkdir(exist_ok=True)
resource_apk=OUT/'resources.apk'
run([SDK/'aapt2','link','--manifest',manifest,'--package-id','0x80','--auto-add-overlay',
     '--java',generated,'--extra-packages',':'.join(sorted(set(packages))),'-I',SDK/'android.jar',
     '-o',resource_apk]+[x for p in resources for x in ('-R',p)])
classes=OUT/'classes'
if classes.exists():shutil.rmtree(classes)
classes.mkdir()
stubs=OUT/'stubs/com/projectinfinity/kodi';stubs.mkdir(parents=True,exist_ok=True)
(stubs/'Main.java').write_text('package com.projectinfinity.kodi; public class Main extends android.app.NativeActivity {public static Main MainActivity;}')
(stubs/'XBMCJsonRPC.java').write_text('package com.projectinfinity.kodi; public class XBMCJsonRPC {public String request_string(String request){throw new UnsupportedOperationException("compile only");}}')
snapshot=OUT/'source-copy'
if snapshot.exists():shutil.rmtree(snapshot)
snapshot.mkdir()
source_hashes={}
for p in (HERE/'java').rglob('*.java'):
 name=p.relative_to(HERE).as_posix();data=p.read_bytes();source_hashes[name]=hashlib.sha256(data).hexdigest()
 copy=snapshot/name;copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(data)
(OUT/'SOURCE-JAVA.json').write_text(json.dumps(source_hashes,indent=2)+'\n')
sources=list((snapshot/'java').rglob('*.java'))+list(generated.rglob('*.java'))+list(stubs.glob('*.java'))
run(['java','com.sun.tools.javac.Main','-source','8','-target','8','-bootclasspath',os.pathsep.join(str(SDK/n) for n in ('android.jar','core-lambda-stubs.jar')),'-classpath',os.pathsep.join(str(p) for p in [SDK/'android.jar']+program+provided),'-d',classes]+sources)
compile_lib=OUT/'baseline-api-compile-only.jar';feature=OUT/'feature.jar'
with ZipFile(compile_lib,'w',ZIP_DEFLATED) as libs,ZipFile(feature,'w',ZIP_DEFLATED) as app:
 for p in classes.rglob('*.class'):
  name=p.relative_to(classes).as_posix()
  (libs if name in ('com/projectinfinity/kodi/Main.class','com/projectinfinity/kodi/XBMCJsonRPC.class') else app).writestr(name,p.read_bytes())
with ZipFile(compile_lib,'a',ZIP_DEFLATED) as libs:
 # Compile/link against existing APIs; never include a second AndroidX copy.
 # Resource library declarations deliberately have no ConstantValue. Reads
 # must resolve to the accepted APK's actual identifiers, not new 0x80 IDs.
 reused=[];filtered=[]
 resource_stubs=OUT/'resource-api';resource_stubs.mkdir(exist_ok=True)
 for jar in program+provided+[feature]:
  target=OUT/('only-new-'+jar.parent.name+'-'+jar.name)
  with ZipFile(jar) as source,ZipFile(target,'w',ZIP_DEFLATED) as output:
   for name in source.namelist():
    if not name.endswith('.class'):continue
    descriptor='L'+name[:-6]+';'
    private=descriptor.startswith(('Lokhttp3/','Lokio/','Lkotlin/','Lcom/google/common/','Landroidx/','Landroid/support/'))
    if descriptor in baseline and not private:
     reused.append(descriptor)
     if '/R$' in descriptor or descriptor.endswith('/R;'):
      package,leaf=name[:-6].rsplit('/',1)
      fields=baseline[descriptor]['fields'];assert all(t in ('I','[I') for _,t in fields)
      path=resource_stubs/package/(leaf+'.java');path.parent.mkdir(parents=True,exist_ok=True)
      path.write_text('package '+package.replace('/','.')+'; public class '+leaf+' {'+
          ''.join('public static '+('int[]' if t=='[I' else 'int')+' '+n+';' for n,t in fields)+'}')
     else:libs.writestr(name,source.read(name))
    else:output.writestr(name,source.read(name))
  filtered.append(target)
 # R classes are declarations only. Existing original field names/values are
 # owned by immutable baseline DEX, including shared tag/styleable identifiers.
 resource_classes=OUT/'resource-api-classes';resource_classes.mkdir(exist_ok=True)
 resource_sources=list(resource_stubs.rglob('*.java'))
 # Different packages can have the same R$ leaf, so use separate source paths.
 if resource_sources:
  run(['java','com.sun.tools.javac.Main','-source','8','-target','8','-d',resource_classes]+resource_sources)
  for p in resource_classes.rglob('*.class'):libs.writestr(p.relative_to(resource_classes).as_posix(),p.read_bytes())
rules=OUT/'component.pro'
shader=private_classes.prepare(WORK);private_program=[]
for jar in filtered:
 target=jar.with_name('private-'+jar.name)
 run(shader+[jar,target,OUT/'private-resources']);private_program.append(target)
private_consumer=[]
for index,path in enumerate(consumer):
 target=OUT/('private-consumer-'+str(index)+'.pro');target.write_text(private_classes.rules(path.read_text()));private_consumer.append(target)
for jar in provided:
 with ZipFile(jar) as source:
  for name in source.namelist():
   if name.startswith('META-INF/proguard/') and not name.endswith('/'):
    target=OUT/('private-'+jar.stem+'-'+Path(name).name);target.write_text(private_classes.rules(source.read(name).decode()));private_consumer.append(target)
  name='okhttp3/internal/publicsuffix/publicsuffixes.gz'
  if name in source.namelist():
   target=OUT/'private-resources/assets/infinity/cast/privatehttp'/name
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read(name))
rules.write_text('''-keep class com.projectinfinity.kodi.InfinityCast* { *; }
-repackageclasses com.projectinfinity.kodi.castdeps
-keepattributes Signature,InnerClasses,EnclosingMethod,*Annotation*
-printmapping '''+str(OUT/'mapping.txt')+'\n')
dex=OUT/'dex'
if dex.exists():shutil.rmtree(dex)
dex.mkdir()
reuse=os.environ.get('INFINITY_CAST_VERIFIED_COMPONENT')
if reuse:
 candidates=list(Path(reuse).resolve().rglob('COMPONENT-RESULT.json'))
 assert len(candidates)==1, 'Reuse requires exactly one authenticated component receipt'
 verified=candidates[0].parent;receipt=json.loads(candidates[0].read_text())
 assert receipt['status']=='PASS_COMPONENT_COMPILE_AND_EXISTING_API_LINK_CONTRACT'
 assert receipt['baseline_APK_sha256']=='550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197'
 assert receipt['feature_Java_sha256']==source_hashes, 'Java input changed; cannot reuse prior SDK component'
 assert receipt.get('build_inputs')==build_inputs, 'Dependency, rules, shader or component build logic changed; stale component refused'
 assert receipt['resources']['sha256']==hashlib.sha256(resource_apk.read_bytes()).hexdigest(), 'Resource input changed; cannot reuse prior SDK component'
 for name,digest in receipt['dex'].items():
  assert re.fullmatch(r'classes\d*\.dex',name)
  data=(verified/'dex'/name).read_bytes();assert hashlib.sha256(data).hexdigest()==digest
  (dex/name).write_bytes(data)
 print('REUSED_VERIFIED_CAST_COMPONENT_R8_NOT_REPEATED')
else:
 run(['java','-Xmx2g','-cp',SDK/'d8.jar','com.android.tools.r8.R8','--release','--min-api','21',
      '--lib',SDK/'android.jar','--lib',compile_lib,'--output',dex,'--pg-conf',rules]+
     [x for p in private_consumer for x in ('--pg-conf',p)]+private_program)
from audit_sdk_component import verify
verify(APK,SDK,OUT)
