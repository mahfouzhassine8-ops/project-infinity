"""Focused one-shot admission and independence; no Android result asserted."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
import resume_durability as scene
import android17_shutdown_probe as shutdown


class ResumeDurabilityTests(unittest.TestCase):
    def test_scene_has_no_service_or_firstparty_writer_and_requires_current_owner(self):
        ast.parse(scene.SCRIPT)
        for value in ("request.get('pid')!=os.getpid()", "request.get('owner')!=owner.get('owner')",
                      "owner.get('status')!='ACTIVE'", "if output.exists()", "run(SimpleNamespace"):
            self.assertIn(value,scene.SCRIPT)
        for forbidden in ('controller_access','import resume_hub','CLOSE_KODI','Player().play','setResolvedUrl','force-stop'):
            self.assertNotIn(forbidden,scene.SCRIPT)
        source=Path(scene.__file__).read_text()
        self.assertNotIn('xbmc.service',source)
        self.assertIn('allow_participant=True',source)
        self.assertIn("device.shell('test','!','-e',target)",source)
        self.assertIn('readonly_resume_observer.stage(args.apk',source)

    def test_reopened_requires_native_exact_source_and_no_autoplay(self):
        directory=[dict(season=2,episode=1,file='plugin://script.infinity.commandcenter/?action=play-local-next&key=x')]
        episode=dict(tvshowid=1,season=2,episode=1,file=scene.native_tv_fixture.FOLDER+'QA.S02E01.mp4')
        responses={'Player.GetActivePlayers':[],'Files.GetDirectory':dict(files=directory),
                   'VideoLibrary.GetEpisodeDetails':dict(episodedetails=episode)}
        device=SimpleNamespace(rpc=lambda method,params=None:responses[method])
        before=dict(watched={'d'*64:dict(watched=True,percentage=100)})
        self.assertTrue(scene.reopened(device,before)['passed'])
        responses['Player.GetActivePlayers']=[dict(playerid=1)]
        with self.assertRaises(AssertionError):scene.reopened(device,before)
        responses['Player.GetActivePlayers']=[]
        directory[0]['file']='plugin://script.infinity.commandcenter/?action=unavailable'
        with self.assertRaises(AssertionError):scene.reopened(device,before)
        directory[0]['file']='plugin://script.infinity.commandcenter/?action=play-local-next&key=x'
        episode['file']='/unrelated.mp4'
        with self.assertRaises(AssertionError):scene.reopened(device,before)

    def test_scene_before_snapshot_and_actual_visible_close_with_full_existing_proofs(self):
        source=Path(shutdown.__file__).read_text()
        self.assertLess(source.index('resume_durability.run('),source.index("report['before_protected_records']=before"))
        self.assertIn("('integrated-real-power-ui','integrated-resume-power-ui')",source)
        self.assertIn('power_ui_contract.close(transport,args.apk,folder)',source)
        self.assertIn('verify_receipt(receipt,owner)',source)
        self.assertIn('verify_records(before,transport.read_json',source)
        self.assertIn('resume_durability.reopened(transport,before)',source)


if __name__=='__main__':unittest.main(verbosity=2)
