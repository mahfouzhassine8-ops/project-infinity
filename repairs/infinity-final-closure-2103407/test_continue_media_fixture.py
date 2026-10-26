from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from unittest import TestCase,main
from unittest.mock import patch
import continue_media_fixture as fixture
from android17_reference_observation import OLD


class ContinueMediaFixtureTests(TestCase):
    def test_actual_generated_clip_is_seekable_180_seconds_24fps(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp);(out/'final-profile').mkdir();report={}
            selected=SimpleNamespace(__file__=str(OLD/'tracking/final-eight/android_selected.py'),subprocess=subprocess)
            args=SimpleNamespace(case='final-continue',out=out)
            device=SimpleNamespace(PACKAGE='com.projectinfinity.kodi',shell=lambda *a:'1' if a[-1]=='ro.kernel.qemu' else '37')
            fixture.prepare(selected,args,report,device)
            target=out/'final-profile/infinity-final-qa.mp4'
            command=['ffmpeg','-v','error','-f','lavfi','-i','color=c=gray:s=64x64:r=1','-t','180',
                     '-an','-c:v','libx264','-pix_fmt','yuv420p',str(target)]
            selected.subprocess.run(command,check=True)
            raw=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries',
                'stream=avg_frame_rate,duration','-of','default=noprint_wrappers=1',str(target)],text=True)
            self.assertIn('avg_frame_rate=24/1',raw);self.assertIn('duration=180.000000',raw)
            keyframes=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-skip_frame','nokey',
                '-show_entries','frame=best_effort_timestamp_time','-of','csv=p=0',str(target)],text=True)
            times=[float(v.strip().strip(',')) for v in keyframes.splitlines() if v.strip().strip(',')]
            self.assertIn(3.0,times);self.assertIn(70.0,times);self.assertEqual(len(times),180)
            self.assertEqual(report['generated_clip_format']['fps'],24)
            with self.assertRaises(ValueError):selected.subprocess.run(command+['-y'],check=True)

    def test_wrong_device_and_unselected_case_cannot_change_generator(self):
        source=SimpleNamespace(__file__=str(OLD/'tracking/final-eight/android_selected.py'),subprocess=subprocess)
        args=SimpleNamespace(case='final-actions',out=Path('/unselected'))
        device=SimpleNamespace(PACKAGE='com.projectinfinity.kodi',shell=lambda *a:'0')
        with self.assertRaises(ValueError):fixture.prepare(source,args,{},device)
        self.assertIs(source.subprocess,subprocess)
        args.case='final-participant';fixture.prepare(source,args,{},None)
        self.assertIs(source.subprocess,subprocess)


if __name__=='__main__':main(verbosity=2)
