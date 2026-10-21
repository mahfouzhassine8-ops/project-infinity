"""Presentation scope, real font fit, assets, metadata and action preservation."""
import ast
import io
import os
from pathlib import Path
import sys
import types
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile
import components99 as f

class Final99(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(os.environ.get('INFINITY_FINAL_PARENT',str(f.ROOT.parent/'baseline97/Infinity-2103397-Fold-Corrective-EXPERIMENTAL.apk')))
  with ZipFile(p) as z:
   cls.assets={n[14:]:z.read(n) for n in z.namelist() if n.startswith('assets/addons/') and not n.endswith('/') and n.split('/')[2] in f.VERSIONS}
  version=ET.fromstring(cls.assets[f.c.UI+'/addon.xml']).get('version')
  cls.before=f.c.components(cls.assets) if version=='0.1.8' else cls.assets
  cls.after,cls.delta=f.components(cls.before)
  sys.path.insert(0,str(f.HERE.parent/'consolidated-2103398'/f.c.LATEST))
  import identity
  sys.modules['latest_identity']=identity
  import home_option_b
  cls.ui=home_option_b

 def test_final_delta_is_only_seventeen_declared_presentation_files(self):
  self.assertEqual(len(self.delta),17)
  for n in self.delta:self.assertTrue(n.startswith((f.c.UI+'/',f.c.SKIN+'/')))
  for n in self.before:
   if n not in self.delta:self.assertEqual(self.before[n],self.after[n])

 def test_chip_values_are_actual_and_missing_values_are_hidden(self):
  root=ET.fromstring(self.after[f.c.SKIN+'/unified/InfinityHomeOptionB.xml'])
  for ident,prop in f.META.items():
   for decoration in (ident+80,ident+90):
    node=root.find('.//control[@id="%d"]'%decoration)
    self.assertEqual(node.findtext('visible'),'!String.IsEmpty(Window.Property(Infinity.HomeOptionB.'+prop+'))')
   self.assertIn('Window.Property(Infinity.HomeOptionB.'+prop+')',root.findtext('.//control[@id="%d"]/label'%ident))

 def test_complete_actions_and_existing_images(self):
  root=ET.fromstring(self.after[f.c.SKIN+'/unified/InfinityHomeOptionB.xml'])
  for ident,caption in zip((101,102,103,104),('Play','Trailer','Favorite','More Info')):
   self.assertEqual(root.findtext('.//control[@id="%d"]/label'%ident).strip(),caption)
   texture=root.findtext('.//control[@id="%d"]/texture'%(ident+50))
   self.assertIn(f.c.SKIN+'/media/'+texture,self.after)
  self.assertEqual(root.findtext('.//control[@id="101"]/textcolor'),f.PRIMARY_INK)
  for tag in ('texturefocus','texturenofocus'):
   self.assertEqual(root.findtext('.//control[@id="101"]/'+tag),'infinity_glass/field.png')
  self.assertIn(f.c.SKIN+'/media/infinity_ui/icons/close.png',self.after)

 def test_font_metrics_leave_room_for_all_four_actions_on_both_fold_displays(self):
  from PIL import ImageFont
  font=ImageFont.truetype(io.BytesIO(self.after[f.c.SKIN+'/fonts/Roboto-Regular.ttf']),22)
  for physical in ((2160,1800),(2520,1080),(1080,2520),(1800,2160),(1920,1080)):
   for expanded in (False,True):
    g=self.ui.geometry(1920,1080,*physical,expanded)
    self.assertGreaterEqual(g['x'],0);self.assertGreaterEqual(g['y'],0)
    self.assertLessEqual(g['x']+g['width'],1920)
    self.assertLessEqual(g['y']+g['height'],1080)
    for coords,caption in zip(g['buttons'],('Play','Trailer','Favorite','More Info')):
     self.assertGreater(coords[2],font.getlength('    '+caption)+20)

 def test_identity_capture_and_actions_are_unchanged(self):
  before=ast.parse(self.before[f.c.UI+'/home_option_b.py'])
  after=ast.parse(self.after[f.c.UI+'/home_option_b.py'].replace(f.MODAL_DETAILS_NEW,f.MODAL_DETAILS_OLD,1))
  for name in ('capture','_perform','read_native_hold','clear_native_hold','geometry'):
   a=next(n for n in before.body if getattr(n,'name','')==name)
   b=next(n for n in after.body if getattr(n,'name','')==name)
   self.assertEqual(ast.dump(a),ast.dump(b))
  for tree in (before,after):
   fn=next(n for n in tree.body if getattr(n,'name','')=='_show_verified_hold')
   cls=next(n for n in fn.body if isinstance(n,ast.ClassDef))
   methods={n.name:ast.dump(n) for n in cls.body if isinstance(n,ast.FunctionDef) and n.name!='onInit'}
   if tree is before:original=methods
   else:self.assertEqual(original,methods)

 def test_shared_theme_layout_and_more_info_back_are_preserved(self):
  a=self.after[f.c.UI+'/resources/skins/Default/1080i/InfinityHomeOptionB.xml']
  self.assertEqual(a,self.after[f.c.SKIN+'/unified/InfinityHomeOptionB.xml'])
  root=ET.fromstring(a)
  self.assertEqual(root.findtext('.//control[@id="126"]/pagecontrol'),'128')
  code=self.after[f.c.UI+'/home_option_b.py']
  self.assertIn(f.INFO_NEW,code)
  for name in (b'snapshot.release_date',b'snapshot.certification',b'snapshot.genres',b'snapshot.credits'):
   self.assertIn(name,f.INFO_NEW)
  ids=[n.get('id') for n in root.iter('control') if n.get('id')]
  self.assertEqual(len(ids),len(set(ids)))
  for n,b in self.before.items():
   if 'Includes_' in n and b'name="InfinityLegacyAccent"' in b:
    before=ET.fromstring(b);after=ET.fromstring(self.after[n])
    added=after.find('variable[@name="InfinityOptionBPrimaryInk"]');self.assertIsNotNone(added)
    after.remove(added)
    self.assertEqual(ET.tostring(before),ET.tostring(after))
   elif n.endswith('CONTROLLER-PREIMAGES.json') or n.startswith(f.c.LATEST+'/') or 'Includes_' in n or n.endswith('/Home.xml'):
    self.assertEqual(b,self.after[n])

 def test_primary_action_is_opaque_with_readable_theme_specific_foreground(self):
  from PIL import Image
  im=Image.open(io.BytesIO(self.after[f.c.SKIN+'/media/infinity_glass/field.png'])).convert('RGBA')
  self.assertEqual(im.getpixel((im.width//2,im.height//2)),(255,255,255,255))
  checked=0
  def luminance(rgb):
   values=[int(rgb[i:i+2],16)/255 for i in (2,4,6)]
   values=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
   return sum(v*w for v,w in zip(values,(.2126,.7152,.0722)))
  for n,body in self.after.items():
   if not n.endswith('.xml') or b'<variable name="InfinityLegacyAccent"' not in body:continue
   root=ET.fromstring(body);accent=root.find('variable[@name="InfinityLegacyAccent"]');ink=root.find('variable[@name="InfinityOptionBPrimaryInk"]')
   if accent is None:continue
   light=next(v for v in accent.findall('value') if 'Infinity.NativeSystemTheme),light)' in v.get('condition',''))
   self.assertEqual(ink.find('value').get('condition'),light.get('condition'))
   for bg,fg in ((light.text,ink.find('value').text),(accent.findall('value')[-1].text,ink.findall('value')[-1].text)):
    a,b=sorted((luminance(bg),luminance(fg)))
    self.assertGreaterEqual((b+.05)/(a+.05),4.5)
   checked+=1
  self.assertEqual(checked,10)

 def test_real_closing_modal_is_waited_for_and_foreign_dialogs_stay_rejected(self):
  tree=ast.parse(self.after[f.c.UI+'/home_option_b.py'])
  fn=next(n for n in tree.body if getattr(n,'name','')=='_wait_for_option_b_close')
  clock=[0.0];waits=[];state={'modal':13000,'window':10000,'abort':False}
  def wait(delay):
   waits.append(delay);clock[0]+=delay
   if clock[0]>=.14:state['modal']=-1
   return state['abort']
  monitor=types.SimpleNamespace(waitForAbort=wait,abortRequested=lambda:state['abort'])
  xbmc=types.SimpleNamespace(Monitor=lambda:monitor)
  gui=types.SimpleNamespace(getCurrentWindowDialogId=lambda:state['modal'],getCurrentWindowId=lambda:state['window'])
  ns={'time':types.SimpleNamespace(monotonic=lambda:clock[0])}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual-close-barrier>','exec'),ns)
  close=ns['_wait_for_option_b_close']
  self.assertTrue(close(xbmc,gui,13000));self.assertGreaterEqual(len(waits),7)
  state['modal']=13000
  self.assertTrue(close(xbmc,gui,13001,13000))
  self.assertFalse(close(xbmc,gui,13001,13002))
  for modal,window,abort in [(10100,10000,False),(-1,10025,False),(-1,10000,True)]:
   state.update(modal=modal,window=window,abort=abort)
   self.assertFalse(close(xbmc,gui,13000))
  state.update(modal=13000,window=10000,abort=False);clock[0]=0
  monitor.waitForAbort=lambda delay:clock.__setitem__(0,clock[0]+delay) or False
  self.assertFalse(close(xbmc,gui,13000));self.assertGreaterEqual(clock[0],1.0)

if __name__=='__main__':unittest.main(verbosity=2)
