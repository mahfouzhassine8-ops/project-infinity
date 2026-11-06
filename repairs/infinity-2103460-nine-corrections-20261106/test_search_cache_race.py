"""Selected actual Search functions; existing synthetic Kodi boundaries only."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'repairs/infinity-master-corrective-20261105'))
import test_search_correction as original
class CacheRace(original.unittest.TestCase):
 def setUp(self):
  self.base=original.SearchCorrection();self.base.setUp();self.addCleanup(self.base.doCleanups);self.b=self.base.b
 def seed_and_race(self,change):
  self.assertEqual(self.b.query()[1],'completed');read=self.b.home.getProperty;done=False
  def get(key):
   nonlocal done
   if not done and key.startswith('Infinity.Search.Cache.'):
    done=True;change()
   return read(key)
  self.b.home.getProperty=get
 def test_widget_race_uses_one_fresh_request_not_stale_rows(self):
  self.seed_and_race(lambda:self.b.props.__setitem__('widgetreload','new'))
  self.assertEqual(self.b.query()[1],'completed');self.assertEqual(self.b.calls,2)
 def test_progress_race_uses_one_fresh_request(self):
  self.seed_and_race(lambda:self.b.touch(self.b.progress/'continue-watching.json'))
  self.assertEqual(self.b.query()[1],'completed');self.assertEqual(self.b.calls,2)
 def test_ui_plus_meaningful_config_change_is_still_rejected(self):
  def mutate():self.b.props['widgetreload']='new';self.b.settings.write_text('<settings><setting id="filter">new</setting></settings>')
  self.seed_and_race(mutate);self.assertEqual(self.b.query()[1],'state_changed');self.assertEqual(self.b.calls,1)
 def test_profile_switch_does_not_start_request_in_new_profile(self):
  other=self.b.profile/'other';other.mkdir()
  self.seed_and_race(lambda:setattr(self.b,'profile',other));self.assertEqual(self.b.query()[1],'state_changed');self.assertEqual(self.b.calls,1)
 def test_cancellation_does_not_start_fresh_request(self):
  def mutate():self.b.props['widgetreload']='new';self.b.canceled=True
  self.seed_and_race(mutate);self.assertEqual(self.b.query()[1],'cancelled');self.assertEqual(self.b.calls,1)
 def test_fresh_native_refusal_is_preserved(self):
  self.seed_and_race(lambda:self.b.props.__setitem__('widgetreload','new'));self.b.native_status='timeout'
  self.assertEqual(self.b.query()[1],'timeout');self.assertEqual(self.b.calls,2)
if __name__=='__main__':unittest.main(verbosity=2)
