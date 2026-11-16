"""Reuse the verified original-signed QA publisher after install-over evidence."""
from pathlib import Path
import hashlib,json,os,subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
REFERENCE='21616dfa94bf7ca9ec52e40119edf95df5e64073'
DRIVER='repairs/infinity-consolidated-2103500-20261115/publish_fastqa.py'

def main():
    assert os.environ['GITHUB_ACTIONS']=='true'
    assert os.environ['GITHUB_REPOSITORY']=='mahfouzhassine8-ops/project-infinity'
    assert os.environ['GITHUB_REF']=='refs/heads/work/infinity-2103502-six-repairs-20261116'
    request=json.loads((HERE/'QA-PUBLICATION-REQUEST.json').read_bytes())
    review_raw=(HERE/'PUBLICATION-REVIEW.json').read_bytes()
    assert hashlib.sha256(review_raw).hexdigest()==request['review_sha256']
    review=json.loads(review_raw)
    assert review['reviewer']=='Astra' and review['status']=='PASS_EXACT_SIGNED_QA_PUBLICATION'
    canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    fixed={name:request[name] for name in ('install','release_id','accepted_pointer_updated','notes_sha256',
                                          'signed_install_request_sha256','evidence_sha256')}
    assert hashlib.sha256(canonical(fixed)).hexdigest()==review['request_sha256']
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==review['driver_sha256']
    assert hashlib.sha256((ROOT/'.github/workflows/infinity-502-combined-stage.yml').read_bytes()).hexdigest()==review['workflow_sha256']
    assert hashlib.sha256((HERE/'QA-SIGNED-INSTALL-REQUEST.json').read_bytes()).hexdigest()==request['signed_install_request_sha256']
    assert set(request['evidence_sha256'])=={'QA-ASTRA-REGISTRATION-REVIEW.json','QA-ASTRA-SIGNED-PAIR-REVIEW.json'}
    for name,expected in request['evidence_sha256'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==expected,name
    notes=(HERE/'QA-INSTALL-AND-LIMITATIONS.md').read_bytes()
    assert hashlib.sha256(notes).hexdigest()==request['notes_sha256']
    helper='repairs/infinity-movies-continue-cast-2103486-20261112/release/common_release.py'
    assert (ROOT/helper).read_bytes()==subprocess.check_output(['git','show',REFERENCE+':'+helper],cwd=ROOT)
    raw=subprocess.check_output(['git','show',REFERENCE+':'+DRIVER],cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest()==review['original_driver_sha256']
    source=raw.decode().replace('2103502','2103504').replace('2103503','2103505')
    original='HERE=Path(__file__).resolve().parent'
    assert source.count(original)==1
    source=source.replace(original,'HERE=Path('+repr(str(HERE))+')')
    start=source.index("instructions=out/'INSTALL-AND-RECOVERY.md';instructions.write_text(")
    end=source.index('\nassets.append(instructions)',start)
    source=source[:start]+"instructions=out/'INSTALL-AND-RECOVERY.md';instructions.write_text("+repr(notes.decode())+")"+source[end:]
    exec(compile(source,str(ROOT/DRIVER),'exec'),{'__file__':str(ROOT/DRIVER),'__name__':'_retained_QA_publication'})

if __name__=='__main__':main()
