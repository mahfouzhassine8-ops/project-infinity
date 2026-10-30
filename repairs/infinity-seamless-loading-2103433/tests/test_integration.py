import ast
from io import BytesIO
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
STAGED=Path(os.environ.get('INFINITY_STAGED','/workspace/cobra-evidence/consolidated434/infinity-stage-v3'))
SKIN_BASE=STAGED/'input-skin'
BASE=STAGED/'input-addons'

def sem(node):
    return node.tag,tuple(sorted(node.attrib.items())),(node.text or '').strip(),tuple(sem(c) for c in node)

def remove_loading(node):
    for child in list(node):
        text=child.text or ''
        selected=(child.tag=='include' and (child.get('content')=='InfinityActionLoadingFrame' or child.get('file')=='Includes_InfinityActionLoading.xml') or
                  child.tag=='param' and child.get('name')=='loadingcontrol' or
                  child.tag=='control' and child.findtext('description')=='INFINITY_ACTION_LOADING_V1 drawer frame' or
                  child.tag in ('onclick','onload','onunload','visible') and 'Infinity.Loading.' in text or
                  child.tag=='onclick' and 'seamless.loading' in text)
        if selected:node.remove(child)
        else:remove_loading(child)

class SourceAndSkinIntegrationTest(unittest.TestCase):
    def test_every_staged_python_source_matches_tested_overlay(self):
        overlay=ROOT/'overlay/script.infinity.commandcenter'
        for path in overlay.iterdir():
            if path.is_file():self.assertEqual(path.read_bytes(),(STAGED/'candidate-addons/script.infinity.commandcenter'/path.name).read_bytes(),path.name)

    def test_actual_xml_retains_every_original_action_geometry_and_control(self):
        plan=json.loads((STAGED/'SOURCE-PLAN.json').read_text());checked=set()
        for key,row in plan.items():
            if not key.endswith('.xml') or not key.startswith('assets/addons/skin.infinity.diggz/') or row['before'] is None or key.endswith('/addon.xml'):continue
            relative=key[len('assets/addons/'):]
            old=ET.parse(SKIN_BASE/relative).getroot();new=ET.parse(STAGED/'members'/key).getroot()
            if relative.endswith('/DialogBusy.xml'):
                panel=new.find('controls/control');hidden=panel.find('visible')
                self.assertIsNotNone(hidden);self.assertEqual('false',hidden.text)
                panel.remove(hidden)
            remove_loading(new)
            self.assertEqual(sem(old),sem(new),relative);checked.add(relative)
        for name in ('Home.xml','MyVideoNav.xml','Includes.xml','View_50_List.xml','Includes_CinemaBrowse.xml','DialogBusy.xml'):
            self.assertIn('skin.infinity.diggz/unified/'+name,checked)
        self.assertTrue(all('/unified/' in name for name in checked),'Unreviewed inactive resolution layouts stay unchanged')

    def test_action_payload_owner_ids_and_frame_capabilities_match(self):
        path=STAGED/'members/assets/addons/skin.infinity.diggz/unified/Home.xml';tree=ET.parse(path).getroot()
        actions=[n for n in tree.iter('onclick') if 'seamless.loading' in (n.text or '')]
        self.assertGreater(len(actions),20)
        for n in actions:
            command=n.text
            raw=command.split('seamless.loading,"',1)[1][:-2]
            raw=raw.replace('\\"','"').replace('\\\\','\\')
            data=json.loads(raw);self.assertIn(data['state'],('action','dispatched'));self.assertEqual(64,len(data['target']))
            self.assertIn('epoch',data['owner'])
            for field in ('section','source','addon','home_section','home_source','dbid'):self.assertIn(field,data['owner'])
            self.assertNotIn('plugin://',command)
        capabilities=next(n.text for n in tree.findall('onload') if 'FrameControls.10000' in (n.text or ''))
        for cid in ('9000','9200','9100'):self.assertIn('|'+cid+'|',capabilities)
        # Implicit native media lists get decorations, never a new onclick that
        # could swallow their built-in folder/play behavior.
        originals=ET.parse(SKIN_BASE/'skin.infinity.diggz/unified/Home.xml').getroot()
        old={n.get('id'):n for n in originals.iter('control') if n.get('id')}
        for n in tree.iter('control'):
            if n.get('id') in old and n.get('type') in ('list','wraplist','panel','fixedlist') and not old[n.get('id')].findall('onclick'):
                self.assertEqual([],n.findall('onclick'))

    def test_service_protected_definitions_and_suffix_byte_exact(self):
        old=(BASE/'script.infinity.commandcenter/service.py').read_bytes();new=(STAGED/'candidate-addons/script.infinity.commandcenter/service.py').read_bytes()
        a={n.name:ast.get_source_segment(old.decode(),n) for n in ast.parse(old).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        b={n.name:ast.get_source_segment(new.decode(),n) for n in ast.parse(new).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        for key in a:
            if key!='main':self.assertEqual(a[key],b[key],key)
        self.assertEqual(old.split(b'    if checkpoint.session is None:',1)[1],new.split(b'    if checkpoint.session is None:',1)[1])
        for key in ('common.py','checkpoint_runtime.py','persistence_participant.py','module_contract.py','default.py'):
            self.assertEqual((BASE/'script.infinity.commandcenter'/key).read_bytes(),(STAGED/'candidate-addons/script.infinity.commandcenter'/key).read_bytes())

    def test_actual_search_prepares_before_one_native_modal(self):
        source=(STAGED/'candidate-addons/script.infinity.commandcenter/infinity_search.py').read_text()
        node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_open_search')
        events=[]
        class Home:
            def getProperty(self,name):return ''
        class Keyboard:
            def __init__(self,*args):events.append('keyboard-created')
            def doModal(self):events.append('modal-open')
            def isConfirmed(self):return False
        class Monitor:
            def abortRequested(self):return False
        fake=types.ModuleType('action_loading')
        class Preparation:
            def __init__(self,target):events.append(('preparation',target))
            def __enter__(self):events.append('preparing')
            def __exit__(self,*args):events.append('ready')
        fake.preparation=Preparation
        namespace=dict(xbmc=types.SimpleNamespace(getSkinDir=lambda:'skin.infinity.diggz',getInfoLabel=lambda key:'',Keyboard=Keyboard,Monitor=Monitor),
                       xbmcgui=types.SimpleNamespace(Window=lambda id:Home()),
                       providers=lambda *a,**k:(events.append('inventory') or ([],[])),
                       shared_history=lambda:[],uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='token')),
                       json=json)
        original=sys.modules.get('action_loading');sys.modules['action_loading']=fake
        try:
            exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-_open_search>','exec'),namespace)
            namespace['_open_search']('movie')
        finally:
            if original is None:sys.modules.pop('action_loading',None)
            else:sys.modules['action_loading']=original
        self.assertEqual(['preparing','inventory','ready','keyboard-created','modal-open'],[x for x in events if not isinstance(x,tuple)])
        # Provider select/history/query/dispatch below the prepared prefix is
        # retained exactly; no synthetic selected-provider search is introduced.
        old=(BASE/'script.infinity.commandcenter/infinity_search.py').read_text()
        anchor="    current='';selected='all';view='search';restore_selection=True"
        self.assertEqual(old[old.index(anchor):],source[source.index(anchor):])

    def test_native_loading_assets_are_bounded_and_transparent(self):
        from PIL import Image
        assets=STAGED/'members/assets/addons/skin.infinity.diggz/media/infinity_ui'
        gif=Image.open(assets/'action_loading.gif');self.assertEqual((128,128),gif.size);self.assertEqual(20,gif.n_frames)
        self.assertLess((assets/'action_loading.gif').stat().st_size,40*1024)
        for i in range(gif.n_frames):
            gif.seek(i);image=gif.convert('RGBA');alpha=image.getchannel('A')
            self.assertEqual(0,alpha.getpixel((64,64)))
            self.assertLess(sum(v!=0 for v in alpha.tobytes()),256)
        gif.close()
        still=Image.open(assets/'action_loading_still.png').convert('RGBA')
        self.assertEqual(0,still.getpixel((64,64))[3])
        definitions=ET.parse(STAGED/'members/assets/addons/skin.infinity.diggz/unified/Includes_InfinityActionLoading.xml').getroot()
        raw=ET.tostring(definitions).decode();self.assertIn('Infinity.OptionalMotionAllowed',raw);self.assertIn('Infinity.RefreshBatterySaver',raw)
        self.assertNotIn('RunScript',raw);self.assertNotIn('RunPlugin',raw);self.assertNotIn('percentage',raw)

if __name__=='__main__':unittest.main()
