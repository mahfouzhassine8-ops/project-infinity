#!/usr/bin/env python3
"""Independent candidate gates. Geometry and source checks are not device acceptance."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import unittest
import zipfile
from lxml import etree as E

HERE = Path(__file__).resolve().parent
PROFILES = [('cover portrait',412,915),('cover landscape',915,412),('inner portrait',673,790),('inner landscape',790,673),('16:9',1920,1080),('20:9',2400,1080),('portrait 9:16',1080,1920),('split portrait',340,790),('split landscape',790,340),('popup portrait',320,640),('popup landscape',640,320),('narrow popup',240,800),('short popup',800,240),('square',600,600),('wide stress',1200,200),('narrow stress',200,1200)]
SOURCE_GEOMETRY = (1080, 2400)

def logical(w, h):
    ratio = w / h
    original = SOURCE_GEOMETRY[0] / SOURCE_GEOMETRY[1]
    if max(ratio / original, original / ratio) <= 1.03:
        return SOURCE_GEOMETRY
    area = SOURCE_GEOMETRY[0] * SOURCE_GEOMETRY[1]
    return tuple(max(8, ((math.floor(x + 0.5) + 4) // 8) * 8) for x in (math.sqrt(area * ratio), math.sqrt(area / ratio)))

def value(text, size):
    if text is None:
        return None
    return float(text[:-1]) * size / 100 if text.endswith('%') else float(text)

def axis(node, start, end, center, length, size):
    first = value(node.findtext(start), size)
    last = value(node.findtext(end), size)
    middle = value(node.findtext(center), size)
    item = node.find(length)
    extent = value(item.get('max') if item.text == 'auto' else item.text, size) if item is not None else None
    if first is None:
        first = size-last-extent if last is not None and extent is not None else middle-extent/2 if middle is not None and extent is not None else 0
    if extent is None:
        extent = size-(last or 0)-first
    return first, extent

def bounds(node, w, h):
    x,cw = axis(node,'left','right','centerleft','width',w)
    y,ch = axis(node,'top','bottom','centertop','height',h)
    return x,y,cw,ch

def canonical(node):
    return (node.tag, tuple(sorted(node.attrib.items())), (node.text or '').strip(), tuple(canonical(child) for child in node if isinstance(child.tag,str)))

def archive(path):
    with zipfile.ZipFile(path) as z:
        assert len(z.namelist()) == len(set(z.namelist())) and z.testzip() is None
        return {n.removeprefix('skin.infinity.diggz/'): z.read(n) for n in z.namelist() if not n.endswith('/')}

def luminance(token):
    rgb = [int(token[i:i+2],16)/255 for i in (2,4,6)]
    linear = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb]
    return sum(c*k for c,k in zip(linear,(.2126,.7152,.0722)))

class CandidateTests(unittest.TestCase):
    def test_exact_package_membership(self):
        self.assertEqual(hashlib.sha256(self.parent.read_bytes()).hexdigest(), 'a6d496f6bd576676d060a31b572e3930c7ac6a3625b8eaf5dcdd04433f172408')
        modified = sorted(n for n in self.before if self.before[n] != self.after.get(n))
        self.assertEqual(modified, self.inventory['modified'])
        self.assertEqual(sorted(set(self.after)-set(self.before)), self.inventory['added'])
        self.assertFalse(set(self.before)-set(self.after))
        self.assertEqual(len(modified),59)
        self.assertEqual(len(self.inventory['added']),27)
        for n,digest in self.inventory['delta_sha256'].items():
            self.assertEqual(hashlib.sha256(self.after[n]).hexdigest(),digest,n)

    def test_retired_routes_and_dependency_boundary(self):
        legacy_count = sum(d.count(b'RunAddon(script.infinity.live)') for n,d in self.before.items() if n.endswith('.xml'))
        self.assertEqual(legacy_count,61)
        for n,d in self.after.items():
            if n.endswith('.xml'):
                self.assertNotIn(b'RunAddon(script.infinity.live)',d,n)
        # Preserve provider TV presets: a missing source is not proof of dead code.
        prefix = 'plugin://plugin.video.playlistbrowser/?action=channels_by_group&src=100&group=TV'
        for name,data in self.before.items():
            if not name.endswith('.xml'):continue
            original=E.fromstring(data);candidate=self.xml[name]
            routes=lambda root:[n.text for n in root.iter() if prefix in (n.text or '')]
            self.assertEqual(routes(original),routes(candidate),name+' provider TV preset changed')
        old = E.fromstring(self.before['addon.xml']); new = self.xml['addon.xml']
        old_imports = {n.get('addon'):dict(n.attrib) for n in old.find('requires')}
        new_imports = {n.get('addon'):dict(n.attrib) for n in new.find('requires')}
        self.assertEqual(set(old_imports)-set(new_imports),{'script.infinity.live'})
        self.assertEqual(set(new_imports)-set(old_imports),{'xbmc.python'})
        for n in set(old_imports)&set(new_imports): self.assertEqual(old_imports[n],new_imports[n])
        self.assertEqual(new_imports['xbmc.python'],{'addon':'xbmc.python','version':'3.0.0'})
        self.assertEqual(new.get('version'),'1.0.5.209')
        self.assertEqual(canonical(old.find("extension[@point='xbmc.gui.skin']")),canonical(new.find("extension[@point='xbmc.gui.skin']")))
        self.assertNotIn('resources/infinity-native-responsive-v1.json',self.after)

    def test_active_sports_routes_preserved_and_scoped(self):
        checked = 0
        variables = {v.get('name'):v for n,r in self.xml.items() if n.endswith('Includes_InfinityPreview.xml') for v in r.findall('variable')}
        for n,r in self.xml.items():
            if not n.endswith('/Home.xml'): continue
            old = E.fromstring(self.before[n])
            for before,after in zip(old.findall('.//content'),r.findall('.//content')):
                text = before.text or ''
                if 'plugin.video.playlistbrowser' in text and 'src=100' in text and 'group=Live+Events' in text:
                    match = re.fullmatch(r'\$VAR\[(Infinity209SportsPath[a-f0-9]+)\]',after.text or '')
                    self.assertIsNotNone(match,n)
                    vals = variables[match[1]].findall('value')
                    self.assertEqual(len(vals),2)
                    self.assertEqual(vals[0].get('condition'),'String.IsEqual(Container(9000).ListItem.Property(section),sports)')
                    self.assertEqual(vals[0].text,text)
                    self.assertFalse(vals[1].get('condition'))
                    self.assertFalse(vals[1].text)
                    checked += 1
        self.assertGreater(checked,0)
        self.metrics['guarded_sports_contents'] = checked

    def test_unrelated_semantics_and_services(self):
        """Compare complete trees after removing only explicit, independently checked repairs."""
        variables = {v.get('name'):v.findtext('value') for n,r in self.xml.items() if n.endswith('Includes_InfinityPreview.xml') for v in r.findall('variable') if v.get('name','').startswith('Infinity209SportsPath')}
        for name in self.inventory['modified']:
            if name == 'addon.xml': continue
            old = E.fromstring(self.before[name]); new = copy.deepcopy(self.xml[name])
            if name.endswith('/Includes.xml'):
                node = new.find("include[@file='Includes_InfinityPreview.xml']")
                self.assertIsNotNone(node,name);new.remove(node)
            # Dedicated legacy power item and its former neighbor references.
            for action in list(old.xpath("//*[text()='RunAddon(script.infinity.live)']")):
                parent = action.getparent()
                if parent.get('id') != '1700' or parent.getparent().get('id') != '17':continue
                group = parent.getparent(); scope = group.getparent()
                while scope.getparent() is not None and not (scope.tag=='include' and scope.get('name')):scope=scope.getparent()
                for link in scope.xpath('.//onup[text()="17"] | .//ondown[text()="17"] | .//onleft[text()="17"] | .//onright[text()="17"]'):
                    link.text='14' if link.tag in ('onup','onleft') else '15'
                group.getparent().remove(group)
            for action in list(old.xpath("//*[text()='RunAddon(script.infinity.live)']")):
                parent=action.getparent(); path=old.getroottree().getpath(parent)
                peers=new.getroottree().xpath(path);self.assertEqual(len(peers),1,name+' '+path)
                peer=peers[0]
                expected=['ClearProperty(Infinity.CinemaDrawerLevel,home)','ActivateWindow(TVGuide)'] if parent.get('id')=='19522' else ['ActivateWindow(TVGuide)']
                self.assertEqual([n.text for n in peer.findall('onclick')],expected,name+' '+path)
                self.assertTrue(all(not n.attrib for n in peer.findall('onclick')),name)
                for node in list(parent.findall('onclick')):parent.remove(node)
                for node in list(peer.findall('onclick')):peer.remove(node)
            for node in new.iter():
                text=node.text or ''
                match=re.fullmatch(r'\$VAR\[(Infinity209SportsPath[a-f0-9]+)\]',text)
                if match:node.text=variables[match[1]]
            if name.endswith('/FileBrowser.xml'):
                load=new.find("onload[.='SetProperty(Infinity.FilePreview.OptIn,v1)']")
                self.assertIsNotNone(load,name);new.remove(load)
                side_old=old.find(".//control[@id='90']");side_new=new.find(".//control[@id='90']")
                for node in list(side_old.findall('control')):
                    if node.get('type')!='button':side_old.remove(node)
                for node in list(side_new.findall('control')):
                    if node.get('type')!='button' or node.get('id')=='9410':side_new.remove(node)
                for root in (old,new):
                    for node in root.find('controls').findall('control'):
                        for tag in ('left','width','top','height','bottom'):
                            for item in node.findall(tag):node.remove(item)
            self.assertEqual(canonical(old),canonical(new),name+' unrelated semantics changed')
        self.metrics['modified_trees_compared'] = len(self.inventory['modified'])-1

    def test_native_controls_and_remote_graph(self):
        for name in self.inventory['modified']:
            if not name.endswith('/FileBrowser.xml'):continue
            old=E.fromstring(self.before[name]);new=self.xml[name]
            old_ids={n.get('id') for n in old.findall('.//control') if n.get('id')}
            new_ids=[n.get('id') for n in new.findall('.//control') if n.get('id')]
            self.assertEqual(len(new_ids),len(set(new_ids)),name)
            self.assertEqual(set(new_ids)-old_ids,{'9410','9413'})
            self.assertTrue(old_ids<=set(new_ids))
            self.assertEqual(new.findtext('defaultcontrol'),'450')
            for ident in old_ids:
                a=old.find(".//control[@id='%s']"%ident);b=new.find(".//control[@id='%s']"%ident)
                for field in ('onclick','altclick','onfocus','enable','selected','onleft','onright','onup','ondown','pagecontrol'):
                    self.assertEqual([canonical(n) for n in a.findall(field)],[canonical(n) for n in b.findall(field)],name+' '+ident+' '+field)
        for name,r in self.xml.items():
            if not name.endswith('/InfinityFilePreview.xml'):continue
            self.assertEqual(r.findtext('defaultcontrol'),'81')
            ids={n.get('id') for n in r.findall('.//control') if n.get('id')}
            for button in r.findall(".//control[@type='button']")+r.findall(".//control[@type='scrollbar']"):
                for field in ('onleft','onright','onup','ondown'):
                    self.assertTrue(button.findall(field),name+' '+field)
                    self.assertTrue(all(n.text in ids for n in button.findall(field)),name+' broken remote target')
            self.assertEqual(r.findtext(".//control[@id='20']/pagecontrol"),'70')

    def test_preview_references_and_themes(self):
        complete = [Path(n).parent.as_posix() for n in self.xml if n.endswith('/Includes_InfinityPreview.xml')]
        all_unified = {n:r for n,r in self.xml.items() if n.startswith('unified/')}
        contrast=[]
        for folder in complete:
            helper=self.xml[folder+'/Includes_InfinityPreview.xml']
            self.assertIsNotNone(self.xml[folder+'/Includes.xml'].find("include[@file='Includes_InfinityPreview.xml']"))
            universe=list(all_unified.values())+[r for n,r in self.xml.items() if str(Path(n).parent)==folder]
            variables={v.get('name') for r in universe for v in r.findall('variable')}
            fonts={v.findtext('name') for r in universe for v in r.findall('.//font')}
            preview=self.xml[folder+'/InfinityFilePreview.xml']
            for node in preview.iter():
                for text in [node.text or '',*node.attrib.values()]:
                    for var in re.findall(r'\$VAR\[([^\]]+)\]',text):self.assertIn(var,variables,folder+' '+var)
                if node.tag=='font':self.assertIn(node.text,fonts,folder+' font')
                if 'texture' in node.tag and node.text and '$' not in node.text and '/' in node.text:self.assertIn('media/'+node.text,self.after,folder+' texture')
            legacy=self.xml.get(folder+'/Includes_InfinityLegacy.xml',self.xml['unified/Includes_InfinityLegacy.xml'])
            for index,theme in enumerate(('cinema','True Black','Light Pearl','Dark OLED')):
                surface=helper.find("variable[@name='InfinityPreviewSurface']").findall('value')[index].text
                self.assertTrue(surface.startswith('FF'))
                for name in ('Text','Secondary'):
                    foreground=legacy.find("variable[@name='InfinityLegacy%s']"%name).findall('value')[index].text
                    low,high=sorted((luminance(foreground),luminance(surface)));ratio=(high+.05)/(low+.05)
                    self.assertGreaterEqual(ratio,4.5,folder+' '+theme+' '+name)
                    contrast.append({'folder':folder,'theme':theme,'text':name,'ratio':round(ratio,2)})
        self.metrics['contrast']=contrast

    def test_responsive_preview_and_browser_bounds(self):
        checks=0;matrix=[]
        def inside(node,w,h,label):
            nonlocal checks
            x,y,cw,ch=bounds(node,w,h)
            self.assertTrue(cw>0 and ch>0 and x>=-.1 and y>=-.1 and x+cw<=w+.1 and y+ch<=h+.1,label+' '+str((x,y,cw,ch)))
            checks+=1;return x,y,cw,ch
        for profile,pw,ph in PROFILES:
            w,h=logical(pw,ph)
            for name,r in self.xml.items():
                if name.endswith('/InfinityFilePreview.xml'):
                    _,_,cw,ch=inside(r.find(".//control[@id='1']"),w,h,name+' '+profile)
                    rects={n.get('id'):inside(n,cw,ch,name+' '+profile+' '+str(n.get('id'))) for n in r.find(".//control[@id='1']").findall('control')}
                    tx,ty,tw,th=rects['20'];self.assertGreaterEqual(th,100)
                    self.assertLessEqual(ty+th,rects['30'][1])
                    self.assertLessEqual(rects['30'][1]+rects['30'][3],rects['80'][1])
                    self.assertLessEqual(rects['80'][0]+rects['80'][2],rects['81'][0])
                    self.assertLessEqual(rects['10'][0]+rects['10'][2],rects['11'][0])
                    self.assertLessEqual(rects['11'][0]+rects['11'][2],rects['82'][0])
                # The exact manifest declares only unified; the responsive opt-in
                # marker is absent. Historical 1920-wide folders must not be
                # misrepresented as active 1080-wide windows on a cover screen.
                if name == 'unified/FileBrowser.xml':
                    for ident in ('411','412','419','450','451','61','90'):
                        inside(r.find(".//control[@id='%s']"%ident),w,h,name+' '+profile+' '+ident)
                    footer=r.find(".//control[@id='9413']")
                    for node in footer.findall('control'):inside(node,.255556*w,244,name+' footer '+profile)
                    # The native grouplist scrolls its longer contents; its viewport remains bounded.
                    self.assertEqual(r.find(".//control[@id='90']").get('type'),'grouplist')
            matrix.append({'profile':profile,'usable_window':[pw,ph],'logical_canvas':[w,h],'result':'PASS'})
        self.metrics['bounds_checks']=checks;self.metrics['profiles']=matrix
        self.metrics['active_file_browser_folder']='unified'
        self.metrics['preview_families']=14

    def test_all_xml_and_unmodified_integration_windows(self):
        self.assertEqual(len(self.xml),2075)
        protected=['Custom_1198_InfinityNav.xml','Custom_1191_InfinitySystemHub.xml','Custom_1188_InfinityHealthCenter.xml','DialogAddonInfo.xml','DialogSettings.xml','DialogAddonSettings.xml','DialogTextViewer.xml','DialogKeyboard.xml','DialogContextMenu.xml','DialogButtonMenu.xml','View_50_List.xml','Includes_CinemaBrowse.xml']
        for name in protected:self.assertEqual(self.before['unified/'+name],self.after['unified/'+name],name)
        for name,data in self.before.items():
            if name.startswith('resources/') or '/Font.xml' in name or name.startswith('media/'):
                self.assertEqual(data,self.after[name],name)
        self.metrics['protected_named_unified_windows']=protected
        self.metrics['xml_documents_parsed']=len(self.xml)

def main():
    parser=argparse.ArgumentParser()
    for n in ('parent','candidate','out'):parser.add_argument('--'+n,type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    CandidateTests.parent=args.parent;CandidateTests.before=archive(args.parent);CandidateTests.after=archive(args.candidate)
    CandidateTests.inventory=json.loads((HERE/'change-inventory.json').read_text())
    CandidateTests.xml={n:E.fromstring(data) for n,data in CandidateTests.after.items() if n.endswith('.xml')}
    CandidateTests.metrics={}
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CandidateTests))
    receipt={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'metrics':CandidateTests.metrics,'physical_device_verified':False}
    (args.out/'SKIN-209-VALIDATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)

if __name__=='__main__':main()
