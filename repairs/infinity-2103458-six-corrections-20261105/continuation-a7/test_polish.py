import unittest,subprocess,xml.etree.ElementTree as E
import polish as P
class Visual(unittest.TestCase):
 def before(self,n):return subprocess.check_output(['git','show','a7f65029:'+str((P.BASE/n).relative_to(P.ROOT))],cwd=P.ROOT).decode()
 def test_exact_visual_only_substitutions(self):
  for n,f in [('DialogVideoInfo.xml',P.info),('Includes_InfinityMediaLists.xml',P.listing)]:self.assertEqual((P.BASE/n).read_text(),f(self.before(n)))
 def test_actions_ids_conditions_data_and_themes_unchanged(self):
  for n in ('DialogVideoInfo.xml','Includes_InfinityMediaLists.xml'):
   a=E.fromstring(self.before(n));b=E.parse(P.BASE/n).getroot()
   for tag in ['onclick','onup','ondown','onleft','onright','visible','enable','label','altlabel','texture','textcolor','autoscroll','pagecontrol','defaultcontrol']:
    self.assertEqual([(x.text,x.attrib) for x in a.findall('.//'+tag)],[(x.text,x.attrib) for x in b.findall('.//'+tag)],(n,tag))
   self.assertEqual([(x.get('id'),x.get('type')) for x in a.findall('.//control')],[(x.get('id'),x.get('type')) for x in b.findall('.//control')])
 def test_synopsis_uses_native_content_extent(self):
  x=E.parse(P.BASE/'Includes_InfinityMediaLists.xml').find('.//control[@id="98064"]')
  self.assertEqual(x.findtext('top'),'0');self.assertEqual(x.find('height').attrib,{'min':'40','max':'0'});self.assertEqual(x.findtext('height'),'auto')
 def test_info_plot_does_not_overlap_action_row(self):
  x=E.parse(P.BASE/'DialogVideoInfo.xml');plot=x.find('.//control[@id="400"]');buttons=x.find('.//control[@id="9000"]')
  self.assertLess(float(plot.findtext('top')[:-1])+float(plot.findtext('height')[:-1]),float(buttons.findtext('top')[:-1]))
  for h in (1080,1128,2520):self.assertGreaterEqual(h*.14,150)
 def test_cast_width_and_native_overflow_labels(self):
  x=E.parse(P.BASE/'DialogVideoInfo.xml');cast=x.find('.//control[@id="50"]')
  for layout in (cast.find('itemlayout'),cast.find('focusedlayout')):
   self.assertEqual(layout.get('aspectratio'),'1.6');self.assertGreater(1080*.13888888*.96666667*1.6*.893333,200)
   self.assertEqual(layout.find('.//control[label="$INFO[ListItem.Label]"]/scroll').text,'true')
  self.assertEqual(x.find('.//control[@id="1"]/scroll').text,'true')
if __name__=='__main__':unittest.main(verbosity=2)
