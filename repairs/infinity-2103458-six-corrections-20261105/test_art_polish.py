import unittest,subprocess,hashlib,json,xml.etree.ElementTree as E
from pathlib import Path
import art_polish as A
R=A.R
class Art(unittest.TestCase):
 def test_episode_fallback_and_poster_order(self):
  x=E.parse(A.PREFIX/'Includes_InfinityMediaLists.xml').getroot()
  vals=x.find('variable[@name="InfinityMedia_SelectedPoster"]').findall('value')
  self.assertEqual([v.text for v in vals[:3]],['$INFO[Container(50).ListItem.Art('+a+')] ' .strip() for a in ('poster','season.poster','tvshow.poster')])
  self.assertEqual(vals[3].get('condition'),A.EP);self.assertEqual(vals[3].text,'$INFO[Container(50).ListItem.Art(thumb)]')
  self.assertIsNone(vals[-1].text)
 def test_no_icon_or_generic_thumbnail_selected(self):
  x=E.parse(A.PREFIX/'Includes_InfinityMediaLists.xml').getroot()
  for name in ('InfinityMedia_SelectedPoster','InfinityMedia_InfoArtwork'):
   n=x.find('variable[@name="'+name+'"]');self.assertIsNotNone(n)
   self.assertNotIn('.Icon',E.tostring(n).decode());self.assertNotIn('.Thumb]',E.tostring(n).decode())
   for v in n.findall('value'):
    if v.text and 'Art(thumb)' in v.text:self.assertIn('DBType,episode',v.get('condition'))
 def test_episode_frame_compact_and_mutually_exclusive(self):
  x=E.parse(A.PREFIX/'Includes_InfinityMediaLists.xml').getroot()
  images=[n for n in x.findall('.//control') if n.findtext('texture')=='$VAR[InfinityMedia_SelectedPoster]']
  self.assertEqual(len(images),2)
  self.assertEqual(images[0].findtext('height'),'55%')
  self.assertEqual(images[1].findtext('height'),'216')
  cond=images[1].findtext('visible');self.assertIn(A.EP,cond)
  for a in ('poster','season.poster','tvshow.poster'):self.assertIn('String.IsEmpty(Container(50).ListItem.Art('+a+'))',cond)
 def test_existing_info_fallback_retained(self):
  x=E.parse(A.PREFIX/'Includes_InfinityMediaLists.xml').getroot();v=x.find('variable[@name="InfinityMedia_InfoArtwork"]')
  self.assertIsNotNone(v);self.assertEqual(v.findall('value')[-1].text,'$VAR[PosterThumb]')
 def test_frame_tracks_rendered_image_not_viewport(self):
  x=E.parse(A.PREFIX/'DialogVideoInfo.xml').getroot()
  n=next(c for c in x.findall('.//control') if c.findtext('texture')=='$VAR[InfinityMedia_InfoArtwork]')
  self.assertEqual(n.find('aspectratio').attrib,{'align':'left','aligny':'top'})
  self.assertEqual(n.findtext('aspectratio'),'keep');self.assertEqual(n.findtext('bordersize'),'2')
  self.assertEqual(n.findtext('bordertexture'),'infinity_glass/rim.png')
  self.assertNotIn(A.FRAME,(A.PREFIX/'DialogVideoInfo.xml').read_text())
 def test_all_nonvisual_fields_exact_and_ids_unmodified(self):
  for name,fn in [('Includes_InfinityMediaLists.xml',A.list_polish),('DialogVideoInfo.xml',A.info_polish)]:
   p=A.PREFIX/name;relative=str(p.relative_to(R));before=subprocess.check_output(['git','show','87efb5ec:'+relative],cwd=R).decode()
   self.assertEqual(p.read_text(),fn(before))
   x=E.fromstring(before);y=E.parse(p).getroot()
   self.assertEqual([E.tostring(n) for n in x.findall('.//onclick')],[E.tostring(n) for n in y.findall('.//onclick')])
   self.assertEqual([n.get('id') for n in x.findall('.//control') if n.get('id')],[n.get('id') for n in y.findall('.//control') if n.get('id')])
 def test_list_baseline_matches_signed458(self):
  rel=str((A.PREFIX/'Includes_InfinityMediaLists.xml').relative_to(R));raw=subprocess.check_output(['git','show','87efb5ec:'+rel],cwd=R)
  m=json.loads((R/'repairs/infinity-browser-visual-20261105/packaging/signed458-evidence/preservation/ALL-APK-MEMBER-HASHES.json').read_text())
  self.assertEqual(hashlib.sha256(raw).hexdigest(),m['assets/addons/skin.infinity.diggz/unified/Includes_InfinityMediaLists.xml']['after'])
if __name__=='__main__':unittest.main(verbosity=2)
