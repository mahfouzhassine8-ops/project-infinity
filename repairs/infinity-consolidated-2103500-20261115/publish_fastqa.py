"""Publish only the exact signed QA pair after PackageManager install-over passes."""
from pathlib import Path
import json,os,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/release'))
import common_release as c
HERE=Path(__file__).resolve().parent
c.require(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REPOSITORY')==c.REPO,'CI_ONLY_PUBLICATION')
r=c.load(HERE/'QA-PUBLICATION-REQUEST.json');pair=c.load(HERE/'QA-SIGNED-INSTALL-REQUEST.json');c.require(r['accepted_pointer_updated'] is False and pair['shutdown'] is False and pair['application_startup'] is False,'QA_PUBLICATION_ONLY')
installroot=c.obtain(r['install'],'qa500-installed-proof');receipt=c.load(c.unique(installroot,'INSTALL-OVER-AND-RECOVERY.json'))
c.require(receipt['status']=='PASS_ACTUAL_ANDROID_IN_PLACE_INSTALL_AND_FORWARD_RECOVERY' and len(receipt['steps'])==3,'ACTUAL_INSTALL_OVER_AND_RECOVERY_REQUIRED')
out=ROOT/'fastqa-publication';out.mkdir(exist_ok=False);assets=[];evidence=out/'evidence';evidence.mkdir()
for index,kind in enumerate(('baseline','candidate','recovery')):
 row=pair['inputs'][kind];c.require(receipt['steps'][index]['APK_sha256']==row['APK_sha256'],'EXACT_TESTED_INSTALL_INPUT')
 if kind=='baseline':continue
 source=c.obtain(row,'qa500-publish-'+kind);version={'candidate':2103502,'recovery':2103503}[kind];apk=c.unique(source,'Infinity-'+str(version)+'-Combined-Original-Signer.apk')
 c.require(c.sha(apk)==row['APK_sha256'],'SIGNED_APK_DIGEST');c.signature(apk);assets.append(apk)
 for name in ('BUILD-RECEIPT.json','PRESERVATION.json','SIGNATURE.txt','release-authority.json'):
  target=evidence/kind/name;target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes((source/name).read_bytes())
(evidence/'INSTALL-OVER-AND-RECOVERY.json').write_text(json.dumps(receipt,indent=2)+'\n')
sha=out/'SHA256SUMS';sha.write_text(''.join(c.sha(p)+'  '+p.name+'\n' for p in assets));assets.append(sha)
instructions=out/'INSTALL-AND-RECOVERY.md';instructions.write_text('Install 2103502 over the existing Infinity app. Do not uninstall or clear data.\n\n2103503 is forward recovery restoring signed2103500 functionality; use it only if recovery is needed. Its higher version code permits installation over2103502.\n\nIncludes only shutdown observer, narrow Silent Mode promotion filtering and Cast discovery. Continue Playing, Otaku Watchlist and Empty Shell remain deferred and unchanged. Physical Fold/TV acceptance remains pending. Cobra2103445 is preserved.\n')
assets.append(instructions)
archive=out/'INFINITY-2103502-QA-VERIFICATION.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for p in evidence.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(evidence))
assets.append(archive)
repo=['--repo',c.REPO];tag='infinity-2103502-fast-qa'
before=c.api('releases/tags/'+tag)
c.require(before['draft'] is True and before['assets']==[],'INITIAL_PUBLICATION_REQUIRES_EMPTY_DRAFT')
subprocess.run(['gh','release','upload',tag,*map(str,assets),*repo],check=True)
current=c.api('releases/tags/'+tag)
c.require(current['draft'] is True,'RELEASE_MUST_STILL_BE_DRAFT')
expected={p.name:'sha256:'+c.sha(p) for p in assets}
c.require({a['name'] for a in current['assets']}==set(expected),'EXACT_RELEASE_ASSETS')
for a in current['assets']:c.require(a['digest']==expected[a['name']],'UPLOADED_RELEASE_DIGEST:'+a['name'])
subprocess.run(['gh','release','edit',tag,*repo,'--draft=false','--prerelease','--latest=false'],check=True)
final=c.api('releases/tags/'+tag)
c.require(not final['draft'] and final['prerelease'],'QA_PRERELEASE_PUBLICATION')
c.save(out/'PUBLICATION-RECEIPT.json',dict(status='PASS_ORIGINAL_SIGNED_QA_PAIR_PUBLICATION',release_url=final['html_url'],assets=[{k:a[k] for k in ('name','digest','size','browser_download_url')} for a in final['assets']],accepted_pointer_updated=False,physical_acceptance='PENDING_OWNER'))
