#!/usr/bin/env python3
"""Preserved 195 source/layout contracts, not physical-device acceptance.

The UI Theme ID assertion is updated to 1198310 because 195 duplicated the
legacy Performance & refresh ID 1198305. Exact routes and ID uniqueness are
now also asserted, rather than returning the first duplicated control.
"""
import unittest
from pathlib import Path
from lxml import etree as E
ROOT=Path(__file__).resolve().parents[2]
SKIN=ROOT/'addons/skin.infinity.diggz'
def xml(name):return E.parse(str(SKIN/'unified'/name))
def control(tree,id):
    matches=tree.xpath('.//control[@id="%s"]'%id)
    if len(matches)!=1:raise AssertionError('Missing or duplicated control: '+str(id))
    return matches[0]
def value(text,parent):
    if text is None:return None
    return float(text[:-1])*parent/100 if text.endswith('%') else float(text)
def axis(n,size,start,end,center,dimension):
    d=n.find(dimension);length=value(d.text,size) if d is not None else None
    if d is not None and d.get('max'):length=min(length,value(d.get('max'),size))
    a=value(n.findtext(start),size);b=value(n.findtext(end),size);c=value(n.findtext(center),size)
    if length is None:length=size-(a or 0)-(b or 0)
    if a is None:a=c-length/2 if c is not None else size-b-length if b is not None else 0
    return a,length
def rect(n,w,h):
    x,cw=axis(n,w,'left','right','centerleft','width')
    y,ch=axis(n,h,'top','bottom','centertop','height')
    return x,y,cw,ch
SIZES=[(1080,2520),(2520,1080),(1560,1560),(1080,1920),(1920,1080),
       (1080,1600),(1600,1080),(880,1280),(1280,880),(720,960),(960,720)]

class SkinContracts(unittest.TestCase):
    def test_xml(self):
        files=list((SKIN/'unified').glob('*.xml'))
        self.assertGreater(len(files),100)
        for path in files:E.parse(str(path))
    def test_identity_is_preserved(self):
        self.assertEqual(E.parse(str(SKIN/'addon.xml')).getroot().get('id'),'skin.infinity.diggz')
    def test_drawer_routes_and_scroll(self):
        r=xml('Custom_1198_InfinityNav.xml');rows=control(r,1198899)
        self.assertEqual(rows.findtext('bottom'),'18')
        self.assertNotIn('Infinity.Drawer.More',E.tostring(r).decode())
        self.assertFalse(r.xpath('.//label[text()="More options"]'))
        buttons=rows.xpath('./control/control[@type="button"]')
        ids=[b.get('id') for b in buttons]
        self.assertEqual(ids.index('1198310')+1,ids.index('1198304'))
        self.assertIn('ActivateWindow(InterfaceSettings)',[e.text for e in control(r,1198310).findall('onclick')])
        self.assertIn('ActivateWindow(1192)',[e.text for e in control(r,1198305).findall('onclick')])
        for id,route in [(1198102,'movies'),(1198103,'tv')]:
            actions=[e.text for e in control(r,id).findall('onclick')]
            self.assertTrue(any('script.infinity.commandcenter/' in a for a in actions))
            self.assertIn('ActivateWindow(Videos,plugin://script.infinity.commandcenter/?action='+route+',return)',actions)
            self.assertFalse(any(a=='ActivateWindow(Videos)' for a in actions))
    def test_capsule_header_separation(self):
        n=control(xml('Home.xml'),19080)
        for w,h in SIZES:
            x,y,cw,ch=rect(n,w,h)
            self.assertLessEqual(x+cw,0.106029*w+16) # existing header text reserved region
            self.assertLess(y+ch,h)
        self.assertLess(float(n.findtext('width')),float(n.findtext('height')))
    def test_power_does_not_default_to_force(self):
        r=xml('DialogButtonMenu.xml');self.assertEqual(r.findtext('defaultcontrol'),'200')
        for id,suffix in [(200,'CLOSE_KODI'),(300,'FORCE_CLOSE_KODI')]:
            actions=control(r,id).findall('onclick')
            android=[a for a in actions if a.get('condition')=='System.Platform.Android']
            self.assertEqual(len(android),1);self.assertIn('.action.'+suffix+',',android[0].text)
            self.assertTrue(any(a.get('condition')=='!System.Platform.Android' for a in actions))
    def test_player_control_order_and_modal_ownership(self):
        r=xml('VideoOSD.xml');rail=control(r,290)
        self.assertEqual([b.get('id') for b in rail.xpath('./control/control[@type="button"]')],
                         ['257','264','201','200','202','205','204','253','250','255','265','262'])
        for id,action in [(201,'Seek(-30)'),(200,'PlayerControl(Previous)'),(202,'PlayerControl(Play)'),
                          (205,'PlayerControl(Next)'),(204,'Seek(30)'),(253,'PlayerControl(Stop)'),
                          (265,'PlayerControl(Repeat)')]:
            self.assertIn(action,[e.text for e in control(r,id).findall('onclick')])
        self.assertEqual(rail.findtext('orientation'),'horizontal')
        self.assertEqual(r.findtext('defaultcontrol'),'257')
        self.assertFalse(r.xpath('.//control[@id="252"]|.//control[@id="263"]'))
        self.assertIn('PlayerVolumeMode',rail.getparent().findtext('visible'))
        volume=control(r,260).getparent()
        self.assertIsNotNone(volume.find('left'));self.assertIsNotNone(volume.find('bottom'))
        self.assertEqual(control(r,260).findtext('orientation'),'vertical')
        self.assertEqual(control(r,260).findtext('action'),'volume')
        for w,h in SIZES:
            for panel in [rail.getparent(),volume]:
                x,y,cw,ch=rect(panel,w,h)
                self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
                self.assertLessEqual(x+cw,w);self.assertLessEqual(y+ch,h)
    def test_light_textures_are_real_light_assets(self):
        r=xml('IncludesVariables.xml')
        for part in ['Header','Footer','Volume','Button','ButtonFocus']:
            vals=r.find('variable[@name="InfinityPlayer'+part+'Texture"]').findall('value')
            v=next(v for v in vals if ',light)' in v.get('condition',''))
            self.assertTrue(v.text.endswith('_light.png'));self.assertTrue((SKIN/'media'/v.text).exists())
        for name in ['InfinityGlassTextPrimary','InfinityGlassSurfaceElevated','InfinityGlassBorder']:
            vals=r.find('variable[@name="'+name+'"]').findall('value')
            self.assertTrue(any(',light)' in v.get('condition','') for v in vals))
            self.assertTrue(any(',OLED)' in v.get('condition','') for v in vals))
    def test_file_source_actions_stay_inside_panel(self):
        r=xml('DialogMediaSource.xml');panel=control(r,9002).getparent()
        self.assertIsNone(panel.find('include')) # no fixed desktop background
        for w,h in SIZES:
            x,y,pw,ph=rect(panel,w,h)
            self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
            self.assertLessEqual(x+pw,w);self.assertLessEqual(y+ph,h)
            for id in [9002,9001,1999]:
                bx,by,bw,bh=rect(control(r,id),pw,ph)
                self.assertGreaterEqual(bx,0);self.assertGreaterEqual(by,0)
                self.assertLessEqual(bx+bw,pw);self.assertLessEqual(by+bh,ph)
            actions=control(r,9001);_,_,aw,ah=rect(actions,pw,ph)
            for id in [18,19]:
                bx,by,bw,bh=rect(control(r,id),aw,ah)
                self.assertLessEqual(bx+bw,aw);self.assertLessEqual(by+bh,ah)
        for id in [10,11,12,13,14,18,19,60,2]:self.assertEqual(len(r.xpath('.//control[@id="%s"]'%id)),1)

if __name__=='__main__':unittest.main(verbosity=2)
