import os,unittest,tempfile,json,hashlib
from pathlib import Path
from zipfile import ZipFile,ZIP_STORED
import xml.etree.ElementTree as ET
import visual_scope as v
BASE=Path(os.environ['INFINITY_BASELINE_APK'])
class VisualScope(unittest.TestCase):
 def test_all_variants_exact_negative_boundary(self):
  revised=v.expected(BASE)
  self.assertEqual(len(revised),15)
  with ZipFile(BASE) as z:
   for n,b in revised.items():
    old=z.read('assets/addons/'+n)
    if n in v.MEMBERS:
     self.assertEqual(b.replace(v.INK,v.ORIGINAL_INK).replace(v.NEW[0],v.OLD[0]).replace(v.NEW[1],v.OLD[1]),old)
     root=ET.fromstring(b);control=root.find('.//control[@id="202"]');self.assertEqual(control.findtext('onclick'),'PlayerControl(Play)')
     self.assertEqual(b.count(v.INK),2 if '/unified/' in n else 0)
    else:
     self.assertEqual(b.replace(b'<showonepage>false</showonepage>',b'<showonepage>true</showonepage>'),old)
     root=ET.fromstring(b)
     for text,bar in [(126,128),(131,133)]:
      self.assertEqual(root.find('.//control[@id="%s"]/pagecontrol'%text).text,str(bar))
      self.assertEqual(root.find('.//control[@id="%s"]/showonepage'%bar).text,'false')
 def test_unexpected_source_and_unowned_paths_rejected(self):
  with ZipFile(BASE) as z:
   for n in v.PINS:
    b=z.read('assets/addons/'+n)
    with self.assertRaises(ValueError):v.transform(n,b+b' ')
    with self.assertRaises(ValueError):v.transform('cobra/'+n,b)
 def test_staging_does_not_modify_original(self):
  before=BASE.stat();revised=v.expected(BASE)
  with tempfile.TemporaryDirectory() as d:
   receipt=v.stage(BASE,d);self.assertEqual(set(receipt),set(v.PINS))
   for n,b in revised.items():self.assertEqual((Path(d)/n).read_bytes(),b)
  after=BASE.stat();self.assertEqual((before.st_size,before.st_mtime_ns),(after.st_size,after.st_mtime_ns))
 def test_package_gate_detects_reintroduced_regression_and_extra_variant(self):
  revised=v.expected(BASE)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'candidate.zip'
   def package(change=None,extra=False):
    with ZipFile(p,'w',ZIP_STORED) as z:
     for n,b in revised.items():z.writestr('assets/addons/'+n,change(b) if change else b)
     if extra:z.writestr('assets/addons/skin.infinity.diggz/unreviewed/VideoOSD.xml',b'<window/>')
   package();self.assertTrue(v.audit_package(BASE,p))
   package(lambda b:b.replace(v.NEW[0],v.OLD[0]));self.assertRaises(ValueError,v.audit_package,BASE,p)
   package(lambda b:b.replace(v.INK,v.ORIGINAL_INK));self.assertRaises(ValueError,v.audit_package,BASE,p)
   package(extra=True);self.assertRaises(ValueError,v.audit_package,BASE,p)
if __name__=='__main__':unittest.main(verbosity=2)
