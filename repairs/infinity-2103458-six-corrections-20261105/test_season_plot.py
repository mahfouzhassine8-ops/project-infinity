import hashlib,json,subprocess,unittest
from pathlib import Path
import xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[2];REL='repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Variables.xml'
BEFORE=subprocess.check_output(['git','show','87efb5ec:'+REL],cwd=R).decode()
OLD='    <value condition="Container.Content(seasons)">$INFO[Container.ShowPlot]</value>'
NEW='    <value condition="Window.IsActive(videos) + Container.Content(seasons) + String.IsEmpty(Container.ShowPlot) + !String.IsEmpty(ListItem.Plot)">$INFO[ListItem.Plot]</value>\n'
class Season(unittest.TestCase):
 def test_signed_baseline(self):
  m=json.loads((R/'repairs/infinity-browser-visual-20261105/packaging/signed458-evidence/preservation/ALL-APK-MEMBER-HASHES.json').read_text());self.assertEqual(hashlib.sha256(BEFORE.encode()).hexdigest(),m['assets/addons/skin.infinity.diggz/unified/Variables.xml']['after'])
 def test_one_scoped_value_only(self):self.assertEqual((R/REL).read_text(),BEFORE.replace(OLD,NEW+OLD))
 def test_collection_and_existing_show_plot_priority(self):
  x=E.parse(R/REL).getroot();vs=x.find('variable[@name="VideoPlotVar"]').findall('value')
  self.assertIn('ListItem.IsCollection',vs[0].get('condition'))
  self.assertEqual(vs[1].text,'$INFO[ListItem.Plot]');self.assertEqual(vs[1].get('condition'),E.fromstring(NEW).get('condition'))
  self.assertEqual(vs[2].text,'$INFO[Container.ShowPlot]')
if __name__=='__main__':unittest.main(verbosity=2)
