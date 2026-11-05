"""Unresolved required behavior: failures block release; no Android claims."""
import json
import math
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as E

import test_search_correction as search
from test_navigation_drawer import SKIN

sys.path.insert(0,'/tmp/infinity-kodi-ui-navigation/repairs/infinity-kodi-2103453-ui-navigation/tests')
import test_navigation as old_navigation_fixture
import test_navigation_drawer as navigation


class RequiredBehavior(unittest.TestCase):
    def fixture(self):
        b=search.effects.SideEffectDiagnosis();b.setUp();self.addCleanup(b.doCleanups)
        exec(search.CODE,b.b.env)
        return b

    def test_nixtoons_history_must_not_discard_completed_result(self):
        fixture=self.fixture();run,_=fixture.nixtoons()
        fixture.b.during=lambda:run(dict(searchType='series',query='synthetic query',path='/search'))
        self.assertEqual(fixture.b.query()[1],'completed')

    def test_identical_settings_rewrite_must_not_discard_completed_result(self):
        fixture=self.fixture()
        fixture.b.during=lambda:fixture.b.touch(fixture.b.settings)
        self.assertEqual(fixture.b.query()[1],'completed')

    def test_movies_and_tv_must_not_open_intermediate_cc_menu(self):
        root=E.parse(SKIN/'unified/Custom_1198_InfinityNav.xml').getroot()
        for cid in ('1198102','1198103'):
            with self.subTest(control=cid):
                button=root.find(".//control[@id='%s']"%cid)
                self.assertFalse(any('plugin://script.infinity.commandcenter/?action=' in (e.text or '') for e in button.findall('onclick')))

    def test_sports_must_not_substitute_playlistbrowser(self):
        a=old_navigation_fixture.API()
        navigation.nav.run('sports',a,a)
        self.assertFalse(any('plugin.video.playlistbrowser' in json.dumps(c) for c in a.requests))

    def test_power_initial_fit_in_synthetic_cover_inner_orientations(self):
        root=E.parse(SKIN/'unified/Custom_1198_InfinityNav.xml').getroot()
        group=root.find(".//control[@id='1198899']")
        offset=0;power_end=None
        for child in group.findall('control'):
            height=float(child.findtext('height'))
            if child.find(".//control[@id='1198304']") is not None:power_end=offset+height;break
            offset+=height+float(group.findtext('itemgap'))
        self.assertEqual(power_end,1416)
        results=[]
        for label,w,h in [('cover_portrait',1080,2520),('cover_landscape',2520,1080),('inner_portrait',1800,2160),('inner_landscape',2160,1800)]:
            ratio=w/h
            source_ratio=1080/2400
            logical_height=2400 if max(ratio/source_ratio,source_ratio/ratio)<=1.03 else max(8,int((int(math.sqrt(1080*2400/ratio)+0.5)+4)//8)*8)
            panel=min(1572,logical_height*0.96)
            usable=panel-float(group.findtext('top'))-float(group.findtext('bottom'))
            results.append(dict(case='SYNTHETIC_'+label,viewport=[w,h],logical_height=logical_height,panel_height=panel,usable_list_height=usable,power_end=power_end,power_fits=power_end<=usable))
        target=Path(__file__).parent/'results/DRAWER-SYNTHETIC-GEOMETRY.json'
        target.write_text(json.dumps({'physical_measurements':False,'cases':results},indent=2)+'\n')
        for r in results:
            with self.subTest(case=r['case']):self.assertTrue(r['power_fits'],r)


if __name__=='__main__':unittest.main(verbosity=2)
