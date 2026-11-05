import os,json,hashlib,unittest
from pathlib import Path
import xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[2]
N='assets/addons/skin.infinity.diggz/unified/DialogVideoInfo.xml'
B=(Path('/tmp/infinity-signed456-payload-audit')/N).read_text()
A=Path(os.environ.get('INFO_SOURCE',str(R/'repairs/infinity-kodi-2103453-ui-navigation/overlay'/N))).read_text()
class Info(unittest.TestCase):
 def test_baseline_bound_to_signed458(self):
  m=json.loads((R/'repairs/infinity-browser-visual-20261105/packaging/signed458-evidence/preservation/ALL-APK-MEMBER-HASHES.json').read_text());self.assertEqual(hashlib.sha256(B.encode()).hexdigest(),m[N]['after'])
 def test_header_label_space_and_no_overlap(self):
  x=E.fromstring(A);back=x.find('.//control[@id="10"]');title=next(n for n in x.findall('.//control') if n.findtext('label')=='MEDIA DETAILS')
  def v(t,w):return float(t[:-1])*w/100 if t.endswith('%') else float(t)
  for w,h in [(1080,2520),(2520,1080),(1080,1128),(1128,1080)]:
   self.assertGreaterEqual(v(back.findtext('width'),w)-float(back.findtext('textoffsetx')),140)
   self.assertLess(v(back.findtext('left'),w)+v(back.findtext('width'),w),v(title.findtext('left'),w))
 def test_every_action_binding_and_control_preserved(self):
  # Byte reconstruction constrains changes to the exact reviewed visual fields.
  expected=B.replace('4.791614%','17.5%').replace('<left>8.2292%</left>','<left>22%</left>').replace('<aspectratio>scale</aspectratio>','<aspectratio>keep</aspectratio>').replace('<width>54.6875%</width>','<width>72%</width>').replace('<height>58</height>\n      <orientation>horizontal</orientation>','<height>72</height>\n      <orientation>horizontal</orientation>').replace('<width>14.285694%</width>','<width>22.8%</width>').replace('<width>16.190453%</width>','<width>22.8%</width>').replace('<width>18.095213%</width>','<width>22.8%</width>')
  self.assertEqual(A,expected)
 def test_action_labels_fit_narrow_window(self):
  x=E.fromstring(A);g=x.find('.//control[@id="9000"]')
  for width in (1080,1128,2520):
   gw=float(g.findtext('width')[:-1])*width/100
   widths=[float(c.findtext('width')[:-1])*gw/100 for c in g.findall('control')]
   self.assertTrue(all(w>=175 for w in widths))
   self.assertLessEqual(sum(widths)+3*float(g.findtext('itemgap')),gw)
 def test_artwork_proportional_without_metadata_substitution(self):
  x=E.fromstring(A);images=[n for n in x.findall('.//control') if n.find('aspectratio') is not None]
  self.assertEqual(len(images),3);self.assertTrue(all(n.findtext('aspectratio')=='keep' for n in images))
if __name__=='__main__':unittest.main(verbosity=2)
