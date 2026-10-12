"""Negative preservation checks using exact retained source hashes and token boundaries."""
import json,tempfile,unittest
from pathlib import Path
from source_scope import verify_pro,tokens,mask
HERE=Path(__file__).resolve().parent
class ScopeGuardTest(unittest.TestCase):
 def test_pro_unapproved_change_is_rejected(self):
  # The inverse edits define a closed set; unrelated team/logo/layout edits cannot pass.
  after=Path('evidence3370/android-source/tools/android/packaging/xbmc/src/CobraProUi.java.in').read_text()
  before=after.replace('final Action[] player=new Action[10]','final Action[] player=new Action[8]').replace('final long[] lastControlClick=new long[10]','final long[] lastControlClick=new long[8]').replace('"fullscreen","more","stats","groups","pip","stats"},names={"Pause","Favorite","Subtitles","Audio","Fullscreen","More","Stats","Multi-View","PiP","Status"}','"fullscreen","more","stats","groups"},names={"Pause","Favorite","Subtitles","Audio","Fullscreen","More","Stats","Multi-View"}').replace('for(int index:new int[]{0,1,2,3,4,6,7,8,9,5})','for(int index:new int[]{0,1,2,3,4,6,7,5})').replace('show&&(i<6||i>=8||sportsMode)','show&&(i<6||sportsMode)').replace('    else if("pip".equals(name)){c.drawRoundRect(2,4,22,20,2,2,p);p.setStyle(Paint.Style.FILL);c.drawRoundRect(12,11,20,18,1,1,p);}\n','')
  verify_pro(before,after)
  with self.assertRaises(AssertionError):verify_pro(before,after.replace('final Ink number,name,program,time','final Ink number,name,program,time,unauthorized'))
 def test_protected_playback_method_cannot_be_masked(self):
  text='private void toggleCobraPreviewMute(){userMute();} private void startSinglePlayer(String url){tune();}'
  self.assertNotEqual(tokens(mask(text)),tokens(mask(text.replace('userMute();','autoUnmute();'))))
  self.assertEqual(tokens(mask(text)),tokens(mask(text.replace('tune();','preserveAudioAndTune();'))))
 def test_exact_baseline_and_all_cobra_owners_pinned(self):
  identity=json.loads((HERE/'baseline-identity.json').read_text());files=json.loads((HERE/'baseline-source-sha256.json').read_text())
  self.assertEqual(len(files),264);self.assertEqual(len(identity['cobra_source_hashes']),24)
  self.assertEqual(identity['retained_transport_source_commit'],'9abf7c84fbd8224958bc8465c983429bc5976074')
  for name,sha in identity['cobra_source_hashes'].items():self.assertEqual(files[name],sha)
 def test_source_tokens_respect_string_and_comment_braces(self):
  self.assertEqual(tokens(mask('private void startSinglePlayer(String url){String x="}";/* { */ tune();} protected void untouched(){keep();}')),tokens(mask('private void startSinglePlayer(String url){String x="{"; fix();} protected void untouched(){keep();}')))
if __name__=='__main__':unittest.main()
