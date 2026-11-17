"""Retained exact signed/install-tested QA publisher. Never updates acceptance."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REF='21616dfa94bf7ca9ec52e40119edf95df5e64073'
DRIVER='repairs/infinity-consolidated-2103500-20261115/publish_fastqa.py'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 assert os.environ['GITHUB_ACTIONS']=='true' and os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
 assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103508-cast-source-reader-20261117'
 r=json.loads((HERE/'PUBLICATION-REQUEST.json').read_bytes());review_raw=(HERE/'PUBLICATION-REVIEW.json').read_bytes();assert sha(review_raw)==r['review_sha256'];review=json.loads(review_raw)
 assert review['reviewer']=='Astra' and review['status']=='PASS_EXACT_SIGNED_QA_PUBLICATION'
 fixed={k:r[k] for k in ('install','release_id','accepted_pointer_updated','notes_sha256','signed_install_request_sha256','evidence_sha256','versions')}
 assert sha(json.dumps(fixed,sort_keys=True,separators=(',',':')).encode())==review['request_sha256']
 assert sha(Path(__file__).read_bytes())==review['driver_sha256'] and sha((ROOT/'.github/workflows/infinity-506-cast-hardware-stage.yml').read_bytes())==review['workflow_sha256']
 assert sha((HERE/'INSTALL-REQUEST.json').read_bytes())==r['signed_install_request_sha256']
 assert set(r['evidence_sha256'])=={'QA-ASTRA-REGISTRATION-REVIEW.json','QA-ASTRA-SIGNED-PAIR-REVIEW.json'}
 for name,wanted in r['evidence_sha256'].items():assert sha((HERE/name).read_bytes())==wanted
 notes=(HERE/'INSTALL-AND-LIMITATIONS.md').read_bytes();assert sha(notes)==r['notes_sha256']
 assert r['versions']['recovery']>r['versions']['candidate']>2103509
 helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py';raw=subprocess.check_output(['git','show',REF+':'+helper]);module=types.ModuleType('common_release');module.__file__=str(ROOT/helper);exec(compile(raw,module.__file__,'exec'),module.__dict__);sys.modules['common_release']=module
 raw=subprocess.check_output(['git','show',REF+':'+DRIVER]);assert sha(raw)=='5519eab3b09399d92ee05e3d73cc2033fff08c2115bb9f5ad6c0c36958b0d97c'
 source=raw.decode().replace('2103502',str(r['versions']['candidate'])).replace('2103503',str(r['versions']['recovery']))
 source=source.replace("HERE=Path(__file__).resolve().parent",'HERE=Path('+repr(str(HERE))+')').replace("HERE/'QA-SIGNED-INSTALL-REQUEST.json'","HERE/'INSTALL-REQUEST.json'").replace("HERE/'QA-PUBLICATION-REQUEST.json'","HERE/'PUBLICATION-REQUEST.json'").replace("ROOT/'fastqa-publication'","ROOT/'cast508-reader-publication'")
 start=source.index("instructions=out/'INSTALL-AND-RECOVERY.md';instructions.write_text(");end=source.index('\nassets.append(instructions)',start)
 source=source[:start]+"instructions=out/'INSTALL-AND-RECOVERY.md';instructions.write_text("+repr(notes.decode())+")"+source[end:]
 exec(compile(source,str(ROOT/DRIVER),'exec'),{'__file__':str(ROOT/DRIVER),'__name__':'_retained_QA_publisher'})
if __name__=='__main__':main()
