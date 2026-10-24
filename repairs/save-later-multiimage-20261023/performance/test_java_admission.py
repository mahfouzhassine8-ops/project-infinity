"""Exercise the compiled installed-source verifier against exact source sets.

Host Java only. No Android, checkpoint, shutdown or application scenario runs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

HARNESS = '''import java.io.File;
import java.lang.reflect.Method;
public final class VerifyController {
 public static void main(String[] args) throws Exception {
  Class<?> owner=Class.forName("com.projectinfinity.kodi.InfinityInstalledCheckpointInstaller");
  Method verify=owner.getDeclaredMethod("verify",File.class);verify.setAccessible(true);
  Object result=verify.invoke(null,new File(args[0]));
  System.out.println(result==null?"REJECTED":result.toString());
 }
}
'''


def run(final, baseline32, baseline33, baseline34, dex, out):
    with tempfile.TemporaryDirectory(prefix='infinity-admission-harness-') as temporary:
        work = Path(temporary)
        source = work / 'VerifyController.java'
        source.write_text(HARNESS)
        subprocess.run(['javac', '--release', '8', '-d', str(work), str(source)], check=True)
        cp = str(work) + ':' + str((dex / 'helper-classes').resolve())
        def verify(path):
            return subprocess.check_output(['java', '-cp', cp, 'VerifyController', str(path)], text=True).strip()
        for path, version in ((baseline32, '0.3.5.32'), (baseline33, '0.3.5.33'), (baseline34, '0.3.5.34'), (final, '0.3.5.35')):
            assert verify(path) == version
        pins = json.loads((final / 'script.infinity.uirepair/CONTROLLER-PREIMAGES.json').read_text())
        for name in sorted(pins):
            path = final / 'script.infinity.commandcenter' / name
            original = path.read_bytes()
            assert hashlib.sha256(original).hexdigest() == pins[name]
            path.write_bytes(original + b'\n')
            try:
                assert verify(final) == 'REJECTED', name
            finally:
                path.write_bytes(original)
    report = {'host': 'PASS', 'scope': 'actual newly compiled Java installed-source verifier',
              'accepted_exact_versions': ['0.3.5.32', '0.3.5.33', '0.3.5.34', '0.3.5.35'],
              'CC35_individual_tamper_rejections': len(pins),
              'controller_dex_sha256': json.loads((dex / 'DEX-PRESERVATION.json').read_text())['final_dex_sha256'],
              'android': 'NOT RUN', 'shutdown': 'NOT RUN; independent', 'physical_fold': 'NOT RUN'}
    out.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('final', 'baseline32', 'baseline33', 'baseline34', 'dex', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
