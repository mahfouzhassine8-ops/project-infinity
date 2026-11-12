"""Key-free dependency feasibility check. Downloads only official Maven artifacts.

No APK, original class, resource or installed data is modified. Existing AndroidX
versions are pinned, not upgraded to satisfy the new feature. The resolved graph
and every artifact SHA-256 are recorded for review before any packaging.
"""
from pathlib import Path
import hashlib, json, re, sys, urllib.request, xml.etree.ElementTree as ET

OUT=Path(sys.argv[1]).resolve();OUT.mkdir(parents=True,exist_ok=True)
NS={'m':'http://maven.apache.org/POM/4.0.0'}
PIN={
 'androidx.core:core':'1.8.0',
 'androidx.lifecycle:lifecycle-runtime':'2.3.1',
 'androidx.arch.core:core-runtime':'2.1.0',
 'androidx.versionedparcelable:versionedparcelable':'1.1.1',
 'androidx.annotation:annotation-experimental':'1.3.1',
}
def version(v):
 if v.startswith('[') and v.endswith(']') and ',' not in v:v=v[1:-1]
 assert re.fullmatch(r'[0-9][A-Za-z0-9.\-]*',v),('Unpinned Maven version',v)
 return v
def key(v):return tuple((1,int(s)) if s.isdigit() else (0,s) for s in re.findall(r'\d+|[^\d]+',v))
def fetch(group,artifact,v,extension):
 folder=OUT/(group+':'+artifact+':'+v);folder.mkdir(exist_ok=True)
 dest=folder/(artifact+'-'+v+'.'+extension)
 if not dest.exists():
  base='https://dl.google.com/dl/android/maven2/' if group.startswith(('androidx.','android.arch.','com.google.android.','com.google.firebase')) else 'https://repo.maven.apache.org/maven2/'
  url=base+group.replace('.','/')+'/'+artifact+'/'+v+'/'+dest.name
  with urllib.request.urlopen(url,timeout=30) as response:dest.write_bytes(response.read())
 return dest
selected={'com.google.android.gms:play-services-cast-framework':'21.3.0'}
poms={}
changed=True
while changed:
 changed=False
 for ga,v in list(selected.items()):
  g,a=ga.split(':');p=fetch(g,a,v,'pom');r=ET.fromstring(p.read_bytes());poms[(ga,v)]=r
  for d in r.findall('m:dependencies/m:dependency',NS):
   if d.findtext('m:scope','compile',NS) in ('test','provided') or d.findtext('m:optional','false',NS)=='true':continue
   ng=d.findtext('m:groupId',None,NS);na=d.findtext('m:artifactId',None,NS)
   nv=version(d.findtext('m:version','',NS));n=ng+':'+na
   if n in PIN:
    assert key(PIN[n])>=key(nv),('Protected baseline too old',n,PIN[n],nv)
    nv=PIN[n]
   if n not in selected or key(nv)>key(selected[n]):selected[n]=nv;changed=True
proof=[]
for ga,v in sorted(selected.items()):
 g,a=ga.split(':');r=poms.get((ga,v)) or ET.fromstring(fetch(g,a,v,'pom').read_bytes())
 extension=r.findtext('m:packaging','jar',NS)
 assert extension in ('jar','aar'),(ga,extension)
 artifact=fetch(g,a,v,extension)
 proof.append(dict(coordinate=ga+':'+v,type=extension,file=str(artifact.relative_to(OUT)),
                   sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),preserve_existing=ga in PIN))
lock=Path(__file__).resolve().parents[1]/'research/CAST-SDK-DEPENDENCIES.json'
if lock.exists():
 expected=json.loads(lock.read_text())['artifacts']
 assert [(r['coordinate'],r['type'],r['sha256']) for r in proof]==[(r['coordinate'],r['type'],r['sha256']) for r in expected], 'SDK artifacts changed from reviewed lock'
(OUT/'SDK-DEPENDENCIES.json').write_text(json.dumps(dict(schema=1,sdk='21.3.0',
 protected_baseline_versions=PIN,artifacts=proof,packaged=False,Android='NOT_RUN'),indent=2)+'\n')
print('RESOLVED',len(proof),'pinned official artifacts; NOT an APK or Android verification')
