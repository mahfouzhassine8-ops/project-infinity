"""Group 1/task03 locked rail orientation in ACTUAL 2103390 skin (read only)."""
import os
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

SOURCE = Path(os.environ.get('INFINITY_2103390_SKIN_ZIP', '/mnt/data/skin.infinity.diggz-1.0.5.228-from-Infinity-2103390.zip'))


class HorizontalContinueWatchingContract(unittest.TestCase):
    @unittest.skipUnless(SOURCE.is_file(), 'exact 2103390 skin input required')
    def test_both_movie_and_tv_continue_panels_horizontal_across_layouts(self):
        with ZipFile(SOURCE) as z:
            all_home=[n for n in z.namelist() if n.startswith('skin.infinity.diggz/') and n.endswith('/Home.xml')]
            self.assertEqual(len(all_home), 14)
            for name in all_home:
                with self.subTest(layout=name):
                    root=ET.fromstring(z.read(name))
                    ids={x.attrib['id']:x for x in root.findall('.//control[@type="panel"]') if 'id' in x.attrib}
                    for ident,category,source in [('8830','movies','InfinityCompactContinueMoviesPath'),('8831','tvshows','InfinityCompactContinueTVPath')]:
                        p=ids.get(ident)
                        self.assertIsNotNone(p, 'Original rail missing: '+ident)
                        self.assertEqual(p.findtext('orientation'), 'horizontal')
                        self.assertEqual(p.findtext('scrolltime'), '150')
                        self.assertGreater(int(p.findtext('width').strip('%')) if p.findtext('width').endswith('%') else int(p.findtext('width')),0)
                        visible=p.findtext('visible') or ''
                        self.assertIn('Property(section),'+category+')', visible)
                        self.assertIn(source,p.findtext('content') or '')
                        self.assertEqual(p.find('content').attrib.get('target'),'videos')


if __name__=='__main__':
    unittest.main()
