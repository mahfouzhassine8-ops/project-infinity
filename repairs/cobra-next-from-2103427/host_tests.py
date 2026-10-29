"""Prepare focused views/gesture tests from actual production DEX, not mocks of
the layout/gesture implementation. Streams are explicit inert ExoPlayer proxies;
this is Robolectric API35 host evidence, never physical decoder/Fold acceptance.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile,ZIP_DEFLATED

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO/'repairs/dual-experience-isolation-2103420'))
from inventory import save,file_sha


def prepare(work,apk,dex2jar,out,baseline_measure=False):
    out=out.resolve();out.mkdir();errors=out/'translation-errors';errors.mkdir()
    import json
    assert file_sha(apk)==json.loads((HERE/'SCOPE.json').read_text())['baseline_apk_sha256']
    def translate(path,name):
        target=out/(name+'.jar')
        subprocess.run(['java','-cp',str(dex2jar/'lib/*'),'com.googlecode.dex2jar.tools.Dex2jarCmd',str(path),'-o',str(target),'-e',str(errors/(name+'.zip'))],check=True)
        return target
    dex_paths=sorted((work/'owner-dex/COBRA').glob('*.dex'))
    if baseline_measure:
        dex_paths=[]
        with ZipFile(apk) as z:
            for i,name in enumerate(('classes4.dex','classes5.dex')):
                p=out/('baseline-part-'+str(i)+'.dex');p.write_bytes(z.read(name));dex_paths.append(p)
    production=[translate(p,'production-'+p.stem) for p in dex_paths]
    support=[]
    with ZipFile(apk) as z:
        for name in ('classes.dex','classes2.dex','classes3.dex'):
            p=out/name;p.write_bytes(z.read(name));support.append(translate(p,'support-'+p.stem))
    # Use the updated, narrowly worded chooser DEX rather than the old one.
    if not baseline_measure:support[0]=translate(work/'owner-dex/CHOOSER_SHELL/part-0.dex','updated-chooser')
    for label,inputs in (('production',production),('support',support)):
        seen=set()
        with ZipFile(out/(label+'.jar'),'w',ZIP_DEFLATED) as target:
            for jar in inputs:
                with ZipFile(jar) as z:
                    for name in z.namelist():
                        if not name.endswith('.class') or name in seen or name.startswith(('com/google/common/','com/google/thirdparty/')):continue
                        if label=='support' and not name.startswith(('com/projectinfinity/kodi/','androidx/')):continue
                        seen.add(name);target.writestr(name,z.read(name))
    tests=out/'src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    selected=[HERE/'tests/CobraPositionWorkTest.java',HERE/'tests/CobraLogoWorkTest.java'] if baseline_measure else sorted((HERE/'tests').glob('*.java'))
    for path in selected:shutil.copyfile(path,tests/path.name)
    pom=(REPO/'repairs/dual-experience-isolation-2103420/tests/pom.xml').read_text().replace('${runtime.work}/changed-host.jar',str(out/'production.jar')).replace('${baseline.dex}/application-host.jar',str(out/'support.jar'))
    (out/'pom.xml').write_text(pom)
    libs=out/'android-test-libs';libs.mkdir()
    for artifact,name in [('monitor','monitor.jar'),('espresso-idling-resource','espresso.jar')]:
        archives=list((Path.home()/'.m2/repository/androidx/test').rglob(artifact+'-*.aar'))
        if archives:
            with ZipFile(sorted(archives)[-1]) as z:(libs/name).write_bytes(z.read('classes.jar'))
    sdk=Path.home()/'.m2/repository/org/robolectric/android-all-instrumented/15-robolectric-12650502-i7'
    if (sdk/('android-all-instrumented-'+sdk.name+'.jar')).exists():
        (out/'pom.xml').write_text(pom.replace('<systemPropertyVariables>',
          '<systemPropertyVariables><robolectric.offline>true</robolectric.offline><robolectric.dependency.dir>'+str(sdk)+'</robolectric.dependency.dir>'))
    save(out/'INPUTS.json',dict(runtime='Robolectric API35 HOST; actual production DEX; inert explicitly identified player proxies; no native playback/shutdown',baseline_measure=baseline_measure,production_dex={p.name:file_sha(p) for p in dex_paths},test_sources={p.name:file_sha(p) for p in selected},physical_Fold='NOT_RUN'))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('work','apk','dex2jar','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--baseline-measure',action='store_true')
    prepare(**vars(p.parse_args()))
