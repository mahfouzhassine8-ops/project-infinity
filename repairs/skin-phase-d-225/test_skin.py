"""Production-byte and adaptive geometry regressions against the exact .224 parent.

These are host checks, not touch/device or rendering acceptance.
"""
import argparse, collections, hashlib, json, sys, unittest, zipfile
from pathlib import Path
import xml.etree.ElementTree as E

p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True)
a,remaining=p.parse_known_args();sys.argv=[sys.argv[0],*remaining]
BEFORE=a.before;AFTER=a.after
def tree(root,name):return E.parse(root/'unified'/name).getroot()
def control(root,id):return root.find(f'.//control[@id="{id}"]')
def length(value,total):return float(value[:-1])*total/100 if value.endswith('%') else float(value)
def y(c,h):return length(c.findtext('top','0'),h)
def height(c,h):return length(c.findtext('height','0'),h)
GEOMETRY=('left','right','top','bottom','width','height','centerleft','centertop')

class Geometry(unittest.TestCase):
 def test_audio_reproduces_original_overlap_and_separates_every_row(self):
  old=tree(BEFORE,'Custom_1195_InfinityAudioSubtitles.xml');new=tree(AFTER,'Custom_1195_InfinityAudioSubtitles.xml')
  self.assertLess(y(control(old,5102),1080)-y(control(old,5101),1080),height(control(old,5101),1080))
  for h in (1080,1440,1800,2400,3400):
   rows=[control(new,id) for id in (5101,5102,5103)]
   for first,second in zip(rows,rows[1:]):self.assertGreaterEqual(y(second,h)-y(first,h)-height(first,h),24)
   group=new.find('./controls/control[@type="group"]');self.assertLessEqual(float(group.findtext('height')),h)
   self.assertLess(y(rows[-1],h)+height(rows[-1],h),float(group.findtext('height')))

 def test_settings_header_reproduces_overlap_and_clears_category(self):
  old=tree(BEFORE,'SettingsCategory.xml');new=tree(AFTER,'SettingsCategory.xml')
  ot=old.find('./controls/control[@type="label"]');nt=new.find('./controls/control[@type="label"]')
  self.assertGreater(y(ot,1080)+height(ot,1080),y(control(old,3),1080))
  for h in (1080,1440,2400):
   for id in (3,5,60):self.assertLess(y(nt,h)+height(nt,h),y(control(new,id),h))

 def test_category_viewport_matches_native_row_template_width(self):
  old=tree(BEFORE,'SettingsCategory.xml');new=tree(AFTER,'SettingsCategory.xml')
  self.assertNotAlmostEqual(length(control(old,3).findtext('width'),2400),length(control(old,10).findtext('width'),2400),places=1)
  for w in (760,1080,1800,2400):self.assertEqual(length(control(new,3).findtext('width'),w),length(control(new,10).findtext('width'),w))

 def test_command_viewport_cannot_start_outside_surface(self):
  name='Custom_1194_InfinityCommandCenter.xml';old=tree(BEFORE,name);new=tree(AFTER,name)
  self.assertLess(y(control(old,1194888),2400),2400*.035)
  for h in (1080,1440,2400,3400):
   c=control(new,1194888);self.assertGreaterEqual(y(c,h),h*.035);self.assertGreaterEqual(length(c.findtext('bottom'),h),h*.035)

 def test_browse_subtitle_is_below_title_on_short_windows(self):
  r=tree(AFTER,'Custom_1193_InfinityBrowse.xml');labels=r.findall('./controls/control[@type="label"]')
  title=next(c for c in labels if 'Infinity.BrowseTitle' in c.findtext('label',''))
  subtitle=next(c for c in labels if 'Infinity.BrowseSubtitle' in c.findtext('label',''))
  for h in (1080,1440,2400):self.assertGreaterEqual(y(subtitle,h),y(title,h)+height(title,h))

 def test_speed_labels_actions_and_close_stay_separate(self):
  r=tree(AFTER,'Custom_1196_InfinityPlaybackSpeed.xml');g=r.find('./controls/control[@type="group"]')
  labels=g.findall('control[@type="label"]')
  for first,second in zip(labels,labels[1:]):self.assertLessEqual(y(first,560)+height(first,560),y(second,560))
  for id in (5201,5202,5203):
   c=control(r,id);self.assertGreaterEqual(y(c,560),y(labels[2],560)+height(labels[2],560));self.assertLessEqual(y(c,560)+height(c,560),y(labels[3],560))

 def test_close_targets_are_reachable_without_touch(self):
  for name,close,buttons in [('Custom_1195_InfinityAudioSubtitles.xml',5199,(5101,5102,5103)),('Custom_1196_InfinityPlaybackSpeed.xml',5299,(5201,5202,5203))]:
   r=tree(AFTER,name);c=control(r,close);self.assertGreaterEqual(height(c,1080),96)
   for id in buttons:self.assertIn(str(close),[control(r,id).findtext(d) for d in ('onup','ondown','onleft','onright')])
   self.assertEqual(c.findtext('onclick'),'Action(Back)')

 def test_command_shortcuts_are_in_vertical_focus_graph(self):
  r=tree(AFTER,'Custom_1194_InfinityCommandCenter.xml')
  self.assertEqual(control(r,1194105).findtext('ondown'),'1194201')
  self.assertEqual(control(r,1194106).findtext('ondown'),'1194203')
  for id in (1194201,1194202,1194203):self.assertEqual(control(r,id).findtext('ondown'),'1194300')

class Preservation(unittest.TestCase):
 def test_every_existing_action_and_control_id_is_preserved(self):
  tags=('onclick','onload','onunload','onfocus','onunfocus','onback')
  for path in BEFORE.rglob('*.xml'):
   rel=path.relative_to(BEFORE)
   if path.name=='addon.xml':continue
   old=E.parse(path).getroot();new=E.parse(AFTER/rel).getroot()
   for tag in tags:
    self.assertEqual(collections.Counter(E.tostring(n) for n in old.iter(tag)),collections.Counter(E.tostring(n) for n in new.iter(tag)),f'{rel}: {tag}')
   self.assertEqual(collections.Counter(c.get('id') for c in old.iter('control')),collections.Counter(c.get('id') for c in new.iter('control') if c.get('id') is not None)+collections.Counter({None:sum(c.get('id') is None for c in old.iter('control'))}),str(rel))

 def test_conditional_geometry_and_focus_animations_unchanged(self):
  def essential(root):
   return [E.tostring(n) for n in root.iter('animation') if (n.get('type') or n.text or '').strip().lower() in ('conditional','focus','unfocus')]
  for p in BEFORE.rglob('*.xml'):
   self.assertEqual(essential(E.parse(p)),essential(E.parse(AFTER/p.relative_to(BEFORE))),str(p.relative_to(BEFORE)))

 def test_no_new_duplicate_geometry_fields(self):
  for p in BEFORE.rglob('*.xml'):
   old=E.parse(p);new=E.parse(AFTER/p.relative_to(BEFORE))
   def duplicates(t):return collections.Counter((c.get('id'),c.get('type'),tag) for c in t.iter('control') for tag in GEOMETRY if len(c.findall(tag))>1)
   self.assertFalse(duplicates(new)-duplicates(old),str(p.relative_to(BEFORE)))

 def test_preview_context_browser_are_byte_identical(self):
  protected={'InfinityFilePreview.xml','FileBrowser.xml','DialogContextMenu.xml','Includes_InfinityPreview.xml'}
  for p in BEFORE.rglob('*.xml'):
   if p.name in protected:self.assertEqual(p.read_bytes(),(AFTER/p.relative_to(BEFORE)).read_bytes(),str(p))

 def test_all_graphics_fonts_themes_and_unrelated_scripts_unchanged(self):
  for p in BEFORE.rglob('*'):
   if not p.is_file() or '__pycache__' in p.parts:continue
   rel=p.relative_to(BEFORE)
   if str(rel)=='resources/lib/infinity_native_ambient.py':continue
   if rel.parts[0] in ('media','fonts','colors','language','resources'):
    self.assertEqual(p.read_bytes(),(AFTER/rel).read_bytes(),str(rel))

 def test_ambient_is_exact_existing_native_approved_repair(self):
  b=(AFTER/'resources/lib/infinity_native_ambient.py').read_bytes()
  self.assertEqual(hashlib.sha256(b).hexdigest(),'de30a5114302a303638c589342024b348d3070c5aa76ba4a360d2506dd4402f7')
  cpp=Path(__file__).resolve().parents[1]/'android-checkpoint-shutdown/runtime/native/overlay/xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'
  self.assertIn(hashlib.sha256(b).hexdigest(),cpp.read_text())

if __name__=='__main__':unittest.main(verbosity=2)
