"""Actual ZIP preservation plus XML contracts; not a Kodi renderer emulator."""
import copy,hashlib,importlib.util,json,re,sys,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile
WORK=Path(__file__).resolve().parents[1];ROOT=WORK.parent
sys.path.insert(0,str(WORK/'tools'))
import build_rc3 as build
BASE=ROOT/'inputs/skin.infinity.diggz-1.0.5.215-CommandCenter-Settings-Readability-RC1-TEST.zip'
CAND=ROOT/'delivery/skin.infinity.diggz-1.0.5.217-Custom-Rails-RC3-TEST.zip'
HELP=ROOT/'delivery/script.infinity.rails-0.2.0-Custom-Rails-RC3-TEST.zip'
DYNAMIC='<content target="videos" sortby="none" limit="0" browse="never">$VAR[InfinityRailsContent]</content>'
def semantic(node):return node.tag,dict(node.attrib),node.text.strip() if node.text and node.text.strip() else None,tuple(semantic(c) for c in node)

class SkinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(BASE) as z:cls.before={n[len(build.ROOT):]:z.read(n) for n in z.namelist() if n.startswith(build.ROOT) and not n.endswith('/')}
        with ZipFile(CAND) as z:cls.after={n[len(build.ROOT):]:z.read(n) for n in z.namelist()}
        with ZipFile(HELP) as z:cls.helper={n:z.read(n) for n in z.namelist()}
    def test_exact_baseline_hash(self):self.assertEqual(hashlib.sha256(BASE.read_bytes()).hexdigest(),build.BASE_SHA)
    def test_version_upgrade_and_real_dependency(self):
        addon=ET.fromstring(self.after['addon.xml']);self.assertEqual(addon.get('version'),'1.0.5.217');self.assertEqual(addon.find('./requires/import[@addon="script.infinity.rails"]').get('version'),'0.2.0')
    def test_all_skin_xml_parse(self):
        count=0
        for n,b in self.after.items():
            if n.endswith('.xml'):ET.fromstring(b);count+=1
        self.assertGreaterEqual(count,2107)
    def test_no_existing_file_removed(self):self.assertTrue(set(self.before)<=set(self.after))
    def test_only_approved_integration_paths_changed(self):
        allowed={'addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json'}
        for p in build.PROFILES:allowed.update(p+'/'+n for n in ['Home.xml','Includes.xml','Includes_InfinityRails.xml','DialogContextMenu.xml','script-infinity-rails-select.xml'])
        changed={n for n,b in self.after.items() if n not in self.before or self.before[n]!=b};self.assertEqual(changed,allowed)
    def test_2937_existing_files_byte_preserved(self):self.assertEqual(sum(self.after[n]==b for n,b in self.before.items()),2937)
    def test_unchanged_commandcenter_and_settings(self):
        paths=[n for n in self.before if 'DialogAddonSettings' in n or 'Custom_1194_InfinityCommandCenter' in n]
        self.assertGreaterEqual(len(paths),14)
        for n in paths:self.assertEqual(self.before[n],self.after[n],n)
    def test_all_baseline_python_and_shutdown_preserved(self):
        for n in self.before:
            if n.endswith('.py') or any(x in n.lower() for x in ['shutdown','resumehub','healthcenter']):self.assertEqual(self.before[n],self.after[n],n)
    def test_all_artwork_fonts_provider_resources_identical(self):
        for n in self.before:
            if n.startswith(('media/','fonts/','resources/')):self.assertEqual(self.before[n],self.after[n],n)
    def test_approved_shortcuts_preserved(self):
        for n in self.before:
            if n.endswith('script-skinshortcuts-includes.xml'):self.assertEqual(self.before[n],self.after[n],n)
    def test_metadata_hashes_correct(self):
        b=json.loads(self.before['Infinity-Protected-Manifest.json'])['protected_files'];a=json.loads(self.after['Infinity-Protected-Manifest.json'])['protected_files'];self.assertEqual(set(a),set(b))
        for n in a:
            if self.before.get(n)!=self.after.get(n):self.assertEqual(a[n],hashlib.sha256(self.after[n]).hexdigest())
            else:self.assertEqual(a[n],b[n])
    def test_helper_no_patcher_or_service(self):
        names=list(self.helper);self.assertFalse(any('skin216' in n or 'installer.py' in n or 'settings.xml' in n or 'rails.json' in n or '.pyc' in n for n in names))
        a=ET.fromstring(self.helper['script.infinity.rails/addon.xml']);self.assertEqual(a.get('version'),'0.2.0');self.assertNotIn('xbmc.service',[e.get('point') for e in a.findall('extension')])
    def test_helper_store_and_catalog_exact_rc2_bytes(self):
        for n in ['store.py','catalog.py']:
            self.assertEqual(self.helper['script.infinity.rails/resources/lib/'+n],(ROOT/'rc2/script.infinity.rails/resources/lib'/n).read_bytes())
    def test_zip_integrity(self):
        for p in [CAND,HELP,BASE]:
            with ZipFile(p) as z:self.assertIsNone(z.testzip());self.assertEqual(len(z.namelist()),len(set(z.namelist())))
    def test_no_user_profile_native_or_external_addon_inside_skin(self):
        for n in self.after:self.assertFalse(n.startswith(('userdata/','addons/')));self.assertFalse(n.endswith(('.apk','.so','.db','.pyc')))
    def test_helper_source_matches_package(self):
        for name,data in self.helper.items():self.assertEqual((WORK/'addons'/name).read_bytes(),data)
    def test_no_menu_startup_hooks_added(self):
        for p in build.PROFILES:
            self.assertEqual(ET.fromstring(self.before[p+'/Home.xml']).findall('onload').__len__(),ET.fromstring(self.after[p+'/Home.xml']).findall('onload').__len__())
        rt=self.helper['script.infinity.rails/resources/lib/runtime.py'].decode();self.assertNotIn('ReloadSkin',rt);self.assertNotIn('Container.Refresh',rt);self.assertNotIn('Thread(',rt)
    def test_animation_gates_reduced_motion(self):
        root=ET.fromstring(self.after['unified/script-infinity-rails-select.xml'])
        for a in root.findall('animation'):self.assertIn('Infinity.OptionalMotionAllowed',a.get('condition',''));self.assertIn(a.get('time'),('180','130'))
    def test_chooser_uses_current_skin_and_closes(self):
        code=self.helper['script.infinity.rails/resources/lib/dialog.py'].decode();self.assertIn('script-infinity-rails-select.xml',code);self.assertIn('finally:',code);self.assertIn('window.close()',code)

def mode_test(profile,control):
    def test(self):
        tree=ET.fromstring(self.after[profile+'/Home.xml']);c=tree.find('.//control[@id="'+str(control)+'"]')
        contents=[x for x in c.findall('content') if x.text=='$VAR[InfinityRailsContent]'];self.assertEqual(len(contents),1);self.assertEqual(contents[0].get('target'),'videos');self.assertEqual(contents[0].get('browse'),'never')
        self.assertEqual(c.findtext('content/include'),'skinshortcuts-submenu' if control==19600 else 'InfinityRailsFallback')
        inc=ET.fromstring(self.after[profile+'/Includes_InfinityRails.xml']);var=inc.find('./variable[@name="InfinityRailsContent"]');self.assertEqual(len(var),3)
        for sec,value in zip(['movies','tvshows'],list(var)[:2]):self.assertIn('section='+sec,value.text);self.assertIn('Infinity.Rails.'+sec+'.Revision',value.text)
    return test

def preservation_test(profile):
    def test(self):
        before=self.before[profile+'/Home.xml'].decode();after=self.after[profile+'/Home.xml'].decode()
        recovered=re.sub(r'\n\s*'+re.escape(DYNAMIC),'',after).replace('<include>InfinityRailsFallback</include>','<include>skinshortcuts-submenu-2</include>');self.assertEqual(recovered,before)
        include=ET.fromstring(self.after[profile+'/Includes_InfinityRails.xml'])
        original=ET.fromstring(self.before[profile+'/DialogContextMenu.xml'])
        retained=include.find('./include[@name="InfinityRailsOriginalContextControls"]');self.assertEqual([semantic(c) for c in original.find('controls')],[semantic(c) for c in retained])
        tree=ET.fromstring(self.after[profile+'/DialogContextMenu.xml']);branches=tree.find('controls').findall('include');self.assertEqual(len(branches),2);self.assertEqual(branches[1].get('condition'),'!['+branches[0].get('condition')+']')
        fresh=include.find('./include[@name="InfinityRailsContextControls"]')
        for cid in ('999','996','1000'):self.assertIsNotNone(fresh.find('./control[@id="'+cid+'"]'));self.assertEqual(len(fresh.findall('.//control[@id="'+cid+'"]')),1)
        lifecycle=include.find('./include[@name="InfinityRailsContextLifecycle"]');self.assertIn('SetProperty',lifecycle.findtext('onload'));self.assertIn('ClearProperty',lifecycle.findtext('onunload'))
    return test

for profile in build.PROFILES:
    for mode,control in [('normal',9200),('cinema',19600),('compact',8820),('twopane',8720)]:setattr(SkinTests,'test_'+profile.replace('/','_')+'_'+mode,mode_test(profile,control))
    setattr(SkinTests,'test_'+profile.replace('/','_')+'_preservation',preservation_test(profile))

class GeometryTests(unittest.TestCase):
    # Native-contract geometry only. Does not model the Android renderer or DPI.
    def check(self,w,h,count):
        bgw=.88*w;maxh=.75*h;listmax=.60*h;rowh=.05*h
        natural=count*rowh+max(0,count-1)*6;listh=min(listmax,natural);bgh=maxh-listmax+listh
        self.assertLessEqual(bgw,w);self.assertLessEqual(bgh,h);self.assertGreater(bgw,.75*w)
        self.assertGreaterEqual(bgh,.12*h+listh);self.assertLessEqual(.04*w+.80*w,bgw)
        self.assertLessEqual(.78*w+.07*w,bgw);self.assertLessEqual(.02*h+.05*h,bgh)
        for ax,ay in [(0,0),(.5*w,.5*h),(w,h)]:
            x=max(0,min(ax-bgw/2,w-bgw));y=max(0,min(ay-bgh/2,h-bgh));self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0);self.assertLessEqual(x+bgw,w+1e-6);self.assertLessEqual(y+bgh,h+1e-6)
        self.assertLessEqual(.06*w+.88*w,w);self.assertLessEqual(.32*h+.36*h,h)

for w,h in [(360,800),(800,360),(768,896),(896,768),(320,600),(600,320),(280,500),(1080,2400),(2400,1080),(1080,1920),(1920,1080),(1000,1000)]:
    for n in [3,4,5,8,20,256]:
        def check(self,w=w,h=h,n=n):self.check(w,h,n)
        setattr(GeometryTests,'test_%dx%d_%d_actions'%(w,h,n),check)

class ContrastTests(unittest.TestCase):
    def test_readable_regular_and_focused_text_all_themes(self):
        with ZipFile(CAND) as z:
            root=ET.fromstring(z.read('skin.infinity.diggz/unified/Includes_InfinityRails.xml'))
        def colors(name):return [v.text[-6:] for v in root.find('./variable[@name="InfinityRails'+name+'"]')]
        def lum(hexcolor):
            rgb=[int(hexcolor[i:i+2],16)/255 for i in (0,2,4)]
            values=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
            return sum(c*w for c,w in zip(values,(.2126,.7152,.0722)))
        for fg,bg in [(colors('Text'),colors('Field')),(colors('FocusedText'),colors('Accent'))]:
            for f,b in zip(fg,bg):
                a,c=sorted([lum(f),lum(b)])
                self.assertGreaterEqual((c+.05)/(a+.05),4.5,(f,b))
