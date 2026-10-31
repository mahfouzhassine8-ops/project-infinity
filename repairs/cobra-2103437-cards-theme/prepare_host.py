"""Isolated Cards source-overlay rendering. Not Android or signed-APK acceptance."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import shutil,subprocess
repo=Path(__file__).resolve().parents[2];h=Path(__file__).parent
base=Path('/workspace/cobra-evidence/drawer435-candidate-host-v2');out=Path('/tmp/cards438/host');out.mkdir()
with ZipFile(base/'production.jar') as src,ZipFile(out/'production.jar','w',ZIP_DEFLATED) as dst:
 changes={str(p.relative_to('/tmp/cards438/classes')):p for p in Path('/tmp/cards438/classes').rglob('*.class')}
 for n in src.namelist():
  if n not in changes:dst.writestr(n,src.read(n))
 for n,p in changes.items():dst.writestr(n,p.read_bytes())
shutil.copyfile(base/'support.jar',out/'support.jar');shutil.copytree(base/'android-test-libs',out/'android-test-libs')
pom=(base/'pom.xml').read_text().replace(str(base),str(out));(out/'pom.xml').write_text(pom)
t=out/'src/test/java/com/projectinfinity/kodi';t.mkdir(parents=True)
shutil.copyfile(repo/'repairs/cobra-next-from-2103427/cards-from-2103431/layout-qa/CobraCardsLayoutTest.java',t/'CobraCardsLayoutTest.java')
shutil.copyfile(h/'CardsThemeTest.java',t/'CardsThemeTest.java')
