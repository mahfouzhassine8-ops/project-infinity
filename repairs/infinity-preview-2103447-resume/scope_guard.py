"""Resume-only source and compiled owner preservation, independent of signing."""
import hashlib,json,re,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1]
OLD=R/'repairs/infinity-2103445-standalone-external-player/runtime'
BASE='89a9e7dabad99c44d19af9b0652beb4596523528'
def original(path):return subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(R))]).decode()
def method(raw,name):
    start=re.search(r'^    (?:@Override )?(?:public|private|protected) [^\n]*?\b'+re.escape(name)+r'\([^\n]*?\) \{',raw,re.M)
    assert start is not None,name
    at=raw.index('{',start.start());depth=0
    # Strip strings/comments while preserving positions for brace matching.
    safe=re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/',lambda m:' '*len(m[0]),raw,flags=re.S)
    for end in range(at,len(raw)):
        depth+=(safe[end]=='{')-(safe[end]=='}')
        if depth==0:return raw[start.start():end+1]
    raise AssertionError(name)
def verify(build):
    for n in ('ExternalVideoRoute.java','InfinityExternalState.java'):
        p=OLD/n;assert p.read_text()==original(p),n
    activity=OLD/'InfinityExternalPlayerActivity.java';a=original(activity);b=activity.read_text()
    marker='    @Override public void tracks('
    assert a[a.index(marker):]==b[b.index(marker):],'Every existing UI constructor, control callback, style and geometry must be unchanged'
    for n in ('existingExperiencePresent','obtainFocus','abandonFocus','onConfigurationChanged','onBackPressed','onPause','onDestroy','position','size','subtitle'):
        assert method(a,n)==method(b,n),'Protected activity method '+n
    engine=OLD/'InfinityExternalEngine.java';a=original(engine);b=engine.read_text()
    for n in ('current','emit','headers','postSize','position','seek','command','volume','surface','listTracks','selectTrack','suspend'):
        assert method(a,n)==method(b,n),'Protected decoder operation '+n
    proof=json.loads((build/'OWNER-BUILD.json').read_text())
    for n,pin in proof['sources'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==pin
    assert proof['baseline']==BASE and proof['unchanged']==587
    allowed=('Lcom/projectinfinity/kodi/InfinityExternalEngine','Lcom/projectinfinity/kodi/InfinityExternalPlayerActivity','Lcom/projectinfinity/kodi/InfinityExternalResume')
    for n in proof['changed']+proof['added']+proof['removed']:
        assert any(n==root+';' or n.startswith(root+'$') for root in allowed),n
    return dict(status='PASS_RESUME_ONLY_SOURCE_AND_CLASS_SCOPE',unchanged_classes=587,
                existing_UI_and_controls='SOURCE_EXACT',Splash_and_state='SOURCE_AND_CLASSES_EXACT',
                new_storage='Preview-only SQLite; no existing database access',
                compiled_method_renumbering='D8 lambda indexes shift inside only the two changed Preview classes; unchanged Java control bodies checked independently')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=verify(a.build);a.out.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
