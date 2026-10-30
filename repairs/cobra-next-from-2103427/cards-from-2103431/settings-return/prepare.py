"""Prepare exact signed431 native-shell baseline only; never mutate production."""
import argparse,hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):
    with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()

def prepare(baseline,out):
    baseline=baseline.resolve();out=out.resolve();scope=json.loads((HERE/'SCOPE.json').read_text());b=json.loads((baseline/'INPUTS.json').read_text())
    assert b['source']==scope['baseline_source'] and b['APK_sha256']==scope['baseline_APK_sha256']
    for name,pin in b['DEX_sha256'].items():assert sha(baseline/name)==pin
    out.mkdir(parents=True,exist_ok=False)
    for name in ('production.jar','support.jar'):shutil.copyfile(baseline/name,out/name)
    shutil.copytree(baseline/'android-test-libs',out/'android-test-libs')
    tests=out/'src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True);test=HERE/'CobraSettingsReturnBaselineTest.java';shutil.copyfile(test,tests/test.name)
    pom=(baseline/'pom.xml').read_text().replace(str(baseline),str(out)).replace('projection.output','settings.output');(out/'pom.xml').write_text(pom)
    record={'phase':'EXACT_SIGNED431_NATIVE_HOST_BASELINE','source':b['source'],'APK_sha256':b['APK_sha256'],'DEX_sha256':b['DEX_sha256'],'production_jar_sha256':sha(out/'production.jar'),'support_jar_sha256':sha(out/'support.jar'),'test_sha256':sha(test),'selected_test':scope['selected_test'],'production_changes':'NONE','APK_build':'NOT_RUN','shutdown':'NOT_RUN'}
    (out/'INPUTS.json').write_text(json.dumps(record,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('baseline','out'):p.add_argument('--'+name,type=Path,required=True)
    prepare(**vars(p.parse_args()))
