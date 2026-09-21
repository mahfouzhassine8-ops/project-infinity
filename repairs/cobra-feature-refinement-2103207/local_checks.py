"""Local checks are syntax/patch/fixture gates, NOT Android/device test results."""
from pathlib import Path
import importlib.util,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parent
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
    ci=load('ci207',ROOT/'ci.py');r=ci.review()
    assert len(r['files'])==3
    subprocess.run(['java',str(ROOT/'ParseJava.java'),str(ROOT.parent/'cobra-2103207-work/tools/android/packaging/xbmc/src')],check=True)
    subprocess.run(['java',str(ROOT/'ParseJava.java'),str(ROOT/'tests')],check=True)
    adapt=load('adapt207',ROOT/'adapt_tests.py')
    with tempfile.TemporaryDirectory(prefix='cobra207-fixtures-') as tmp:
        target=Path(tmp);source=ROOT.parent/'cobra-ci-inputs/audit206/repairs'
        for relative in ['cobra-player-polish-2103201/tests/Cobra2103201SubtitleTest.java','cobra-final-features-2103205/tests/Cobra2103205PresentationEffectsTest.java','cobra-media-calls-2103206/tests/Cobra2103206MediaCallsTest.java']:
            shutil.copy2(source/relative,target/Path(relative).name)
        adapt.adapt(target,target/'supersessions.json')
        subprocess.run(['java',str(ROOT/'ParseJava.java'),str(target)],check=True)
        t=(target/'Cobra2103206MediaCallsTest.java').read_text()
        assert t.count('@Test')==28 and 'cobraCallResumeAvailable' not in t
        assert 'assertEquals("Play",row("cobra_player_play_pause")' not in t
        try:adapt.adapt(target,target/'supersessions.json')
        except RuntimeError:pass
        else:raise AssertionError('Adaptation must reject already-changed fixtures')
    print('PASS local patch, 49 protected members, syntax and fixture guards; Android tests NOT run locally')
if __name__=='__main__':main()
