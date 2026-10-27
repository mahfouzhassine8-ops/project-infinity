import argparse
from pathlib import Path
import shutil
from inventory import HERE,ROOT,save,file_sha
from prepare_runtime import wiring

def prepare(out):
    out.mkdir();source=out/'src/main/java/com/projectinfinity/kodi';source.mkdir(parents=True)
    tests=out/'src/test/java/com/projectinfinity/kodi';tests.mkdir(parents=True)
    for p in (HERE/'runtime').glob('*.java'):shutil.copyfile(p,source/p.name)
    (source/'OwnerDurabilityWiring.java').write_text(wiring())
    for name in ('ProductionBoundaryTest.java',):shutil.copyfile(HERE/'tests'/name,tests/name)
    shutil.copyfile(ROOT/'repairs/essential-first-2103377/tests/HostFilesystemShadow.java',tests/'HostFilesystemShadow.java')
    shutil.copyfile(HERE/'tests/pom.xml',out/'pom.xml')
    save(out/'TEST-INPUTS.json',{str(p.relative_to(out)):file_sha(p) for p in out.rglob('*.java')})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);prepare(**vars(p.parse_args()))
