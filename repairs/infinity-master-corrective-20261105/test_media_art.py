"""Existing movie List texture binding; no claimed visual/device acceptance."""
from pathlib import Path
import re
import subprocess
import unittest
import xml.etree.ElementTree as E

HERE=Path(__file__).resolve().parent
NAME='repairs/infinity-kodi-2103453-ui-navigation/overlay/assets/addons/skin.infinity.diggz/unified/Includes_InfinityMediaLists.xml'
BEFORE=subprocess.check_output(['git','show','1b655a9e:'+NAME],cwd=HERE).decode()
AFTER=(HERE.parents[1]/NAME).read_text()


class MediaArt(unittest.TestCase):
    def test_baseline_binds_movie_rows_to_studio_art(self):
        root=E.fromstring(BEFORE)
        rows=[e for e in root.iter() if e.tag in ('itemlayout','focusedlayout') and e.get('condition')=='Container.Content(movies)']
        self.assertEqual(len(rows),2)
        for row in rows:self.assertIn('$VAR[StudioIconVar]',[n.text for n in row.iter('texture')])

    def test_normal_and_focused_movie_rows_use_item_poster(self):
        root=E.fromstring(AFTER)
        rows=[e for e in root.iter() if e.tag in ('itemlayout','focusedlayout') and e.get('condition')=='Container.Content(movies)']
        for row in rows:
            images=[c for c in row.iter('control') if c.findtext('texture')=='$INFO[ListItem.Art(poster)]']
            self.assertEqual(len(images),1)
            self.assertEqual(images[0].findtext('aspectratio'),'keep')
            self.assertLess(float(images[0].findtext('width').rstrip('%')),10)
            self.assertIsNone(images[0].find('texture').get('fallback'))

    def test_only_two_bindings_change_no_metadata_actions_or_theme_rewrite(self):
        pattern=r'(<(itemlayout|focusedlayout)\b[^>]*condition="Container.Content\(movies\)"[^>]*>)(.*?)(</\2>)'
        expected=re.sub(pattern,lambda m:m[1]+m[3].replace('$VAR[StudioIconVar]','$INFO[ListItem.Art(poster)]')+m[4],BEFORE,flags=re.S)
        self.assertEqual(AFTER,expected)
        old,new=E.fromstring(BEFORE),E.fromstring(AFTER)
        for tag in ('label','onclick','visible','textcolor','font','include','onright'):
            self.assertEqual([(e.attrib,e.text) for e in old.iter(tag)],[(e.attrib,e.text) for e in new.iter(tag)])


if __name__=='__main__':unittest.main(verbosity=2)
