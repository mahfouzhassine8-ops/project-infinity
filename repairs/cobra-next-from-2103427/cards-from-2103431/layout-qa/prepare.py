"""Prepare only selected Cards host view tests. Never execute tests/build an APK."""
import argparse,hashlib,json,shutil
from pathlib import Path
from xml.sax.saxutils import escape
HERE=Path(__file__).resolve().parent
SOURCE='9ccc4c362a65118eeba38a8e7e4b0de5723c69af'
APK='3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471'

def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def prepare(classpath,out,candidate=False,baseline_results=None):
    classpath=classpath.resolve();out=out.resolve();assert not out.exists(),'Fresh output only; failure history is retained'
    scope=json.loads((HERE/'SCOPE.json').read_text());assert scope['selected_before_execution']
    binding_path=classpath/('SOURCE-BINDINGS.json' if candidate else 'INPUTS.json');binding=json.loads(binding_path.read_text())
    if candidate:
        assert binding['baseline_signed_source']==SOURCE and binding['baseline_APK_sha256']==APK
        canonical=classpath/'INDEPENDENT-CANONICAL-RESULT.json';assert canonical.is_file()
        assert 'PASS' in json.loads(canonical.read_text())['status']
        assert baseline_results is not None
    else:
        assert binding['source']==SOURCE and binding['APK_sha256']==APK
        for name,pin in binding['DEX_sha256'].items():assert sha(classpath/name)==pin
        for name,pin in binding['translated_jar_SHA256'].items():assert sha(classpath/(name.removesuffix('.dex')+'-translated.jar'))==pin
    out.mkdir(parents=True);test=HERE/'CobraCardsLayoutTest.java';dest=out/'src/test/java/com/projectinfinity/kodi'/test.name;dest.parent.mkdir(parents=True);shutil.copyfile(test,dest)
    for name in ('production.jar','support.jar'):(out/name).symlink_to(classpath/name)
    (out/'android-test-libs').symlink_to(classpath/'android-test-libs',target_is_directory=True)
    pom=(classpath/'pom.xml').read_text().replace(escape(str(classpath)),escape(str(out)))
    if '<artifactId>nativeruntime</artifactId>' not in pom:
        pom=pom.replace('</dependencies>','<dependency><groupId>org.robolectric</groupId><artifactId>nativeruntime</artifactId><version>4.14.1</version><scope>test</scope></dependency><dependency><groupId>org.robolectric</groupId><artifactId>nativeruntime-dist-compat</artifactId><version>1.0.16</version><scope>test</scope></dependency></dependencies>')
    pom=pom.replace('</systemPropertyVariables>',f'<cards.layout.output>{escape(str(out/"measurements"))}</cards.layout.output><cards.candidate>{str(candidate).lower()}</cards.candidate><cards.layout.baseline>{escape(str(baseline_results.resolve())) if baseline_results else ""}</cards.layout.baseline></systemPropertyVariables>')
    (out/'pom.xml').write_text(pom)
    receipt={'phase':'ACTUAL_OWNER_DEX_CARDS_HOST' if candidate else 'EXACT_SIGNED431_CARDS_HOST_BASELINE','source_binding':binding,'source_binding_sha256':sha(binding_path),'test_sha256':sha(test),'prepare_sha256':sha(HERE/'prepare.py'),'scope_sha256':sha(HERE/'SCOPE.json'),'classpath':{n:sha(out/n) for n in ('production.jar','support.jar')},'baseline_results':str(baseline_results.resolve()) if baseline_results else None,'selected_methods':[scope['next_selected_candidate_method']] if candidate and 'next_selected_candidate_method' in scope else scope['selected_candidate_methods'] if candidate else [scope.get('next_selected_baseline_method',scope['selected_baseline_method'])],'behavior':'NOT_RUN','APK':'NOT_BUILT','CI':'NOT_RUN','shutdown':'NOT_RUN'}
    (out/'INPUTS.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--classpath',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--candidate',action='store_true');p.add_argument('--baseline-results',type=Path);prepare(**vars(p.parse_args()))
