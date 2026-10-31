"""Synthetic-format observer guards only; never application/runtime evidence."""
import copy
import json
from pathlib import Path
import unittest
from verify import native_structure

def format_fixture():
 def group(w,h,identity,kind='android.widget.LinearLayout'):
  return dict(identity=identity,**{'class':kind},width=w,height=h,drawing_bounds=[0,0,w,h],layout_width=w,layout_height=h,screen_bounds=[448,0,1600,h])
 structure=dict(grid=group(1600,900,1,'android.widget.GridView'),browser=group(1600,1065,3),toolbar=group(1600,129,4),preview=group(774,449,5))
 structure['grid'].update(columns=4,layout_width=-1,layout_height=0)
 nodes=[dict(id=1,parent=None,label='',**{'class':'android.widget.GridView'},drawing_bounds=[0,0,1600,900],bounds=[448,0,1600,900],selected=False,visible=True),dict(id=2,parent=1,label='Cards QA 00001',drawing_bounds=[0,0,380,200],bounds=[448,150,828,350],selected=True,visible=True)]
 return dict(structure=structure,nodes=nodes)

class ObserverTests(unittest.TestCase):
 def test_unclipped_native_sizes_are_independent_of_screen_occlusion(self):
  data=format_fixture();self.assertEqual(native_structure(data)['grid']['width'],1600)
  data['structure']['grid']['screen_bounds']=[700,0,1600,900];self.assertEqual(native_structure(data)['grid']['width'],1600)
 def test_drawn_and_native_layout_parameters_must_agree(self):
  data=format_fixture();data['structure']['browser']['layout_width']=1152
  with self.assertRaises(AssertionError):native_structure(data)
 def test_missing_native_collection_measurement_is_not_a_pass(self):
  data=format_fixture();del data['structure']['grid']['columns']
  with self.assertRaises(KeyError):native_structure(data)
  data=format_fixture();data['nodes']=[]
  with self.assertRaises(AssertionError):native_structure(data)

if __name__=='__main__':
 scope=json.loads(Path(__file__).with_name('SCOPE.json').read_text());assert scope['selected_before_execution'];methods=scope['selected_offline_observer_tests'];assert sorted(methods)==unittest.defaultTestLoader.getTestCaseNames(ObserverTests)
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(ObserverTests(n) for n in methods));raise SystemExit(0 if result.wasSuccessful() else 1)
