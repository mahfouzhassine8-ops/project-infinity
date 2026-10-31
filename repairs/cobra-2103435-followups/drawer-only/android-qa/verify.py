"""Offline validation of actual native View accessibility rendering data.

ViewGroup supplies LayoutParams through EXTRA_DATA_RENDERING_INFO_KEY and View
supplies untransformed drawing bounds; screen-clipped bounds are never used as
proof of raw content width. Activity dumps are retained as diagnostics only."""
import hashlib
import json
from pathlib import Path
import re
from PIL import Image

def native_structure(info):
 structure=info['structure']
 assert structure['grid']['class']=='android.widget.GridView'
 for name in ['grid','browser','toolbar','preview']:
  group=structure[name];rect=group['drawing_bounds']
  assert group['width']==rect[2]-rect[0]>0 and group['height']==rect[3]-rect[1]>0
  if name!='grid':assert group['layout_width']==group['width'] and group['layout_height']==group['height'],'Drawn size and actual native LayoutParams must agree'
 columns=structure['grid']['columns'];assert 1<=columns<=4
 assert structure['grid']['width']==structure['browser']['width']==structure['toolbar']['width']
 assert 0<structure['toolbar']['height']<400
 nodes=info['nodes'];grid_id=structure['grid']['identity']
 by_parent={}
 for n in nodes:by_parent.setdefault(n['parent'],[]).append(n)
 def channel(node):
  match=re.search(r'Cards QA [0-9]{5}',node['label'])
  if match:return match[0]
  for child in by_parent.get(node['id'],[]):
   result=channel(child)
   if result:return result
  return None
 cards=[]
 for n in by_parent.get(grid_id,[]):
  key=channel(n)
  if key:cards.append(dict(identity=n['id'],channel=key,drawing_bounds=n['drawing_bounds'],screen_bounds=n['bounds'],selected=n['selected'],visible=n['visible']))
 assert cards,'Actual native collection children with channel identity required'
 return dict(**structure,columns=columns,cards=cards,observed_views=len(nodes))

def same_geometry(a,b):
 for name in ['grid','browser','preview','toolbar']:
  assert (a[name]['width'],a[name]['height'])==(b[name]['width'],b[name]['height']),(name,a[name],b[name])
 assert a['columns']==b['columns']

def check(root,baseline):
 outcome=json.loads((root/'OUTCOME.json').read_text());assert outcome['status'].startswith('NATIVE_EVENTS_CAPTURED') and outcome['phase']=='verify'
 phases={p.name.removesuffix('-nodes.json'):native_structure(json.loads(p.read_text())) for p in root.glob('*-nodes.json')}
 baseline_phases={p.name.removesuffix('-nodes.json'):native_structure(json.loads(p.read_text())) for p in baseline.glob('*-nodes.json')}
 for before,after in [('435-cover-closed','01-cover-closed'),('435-inner-closed','04-inner-closed'),('435-rotated-inner-closed','10-rotated-inner-closed'),('435-cover-return-closed','12-cover-return-closed')]:same_geometry(baseline_phases[before],phases[after])
 for name in ['01-cover-closed','12-cover-return-closed']:assert phases[name]['columns']==2 and phases[name]['grid']['width']==1080,(name,phases[name])
 same_geometry(phases['01-cover-closed'],phases['12-cover-return-closed'])
 for name in ['03-inner-open-from-cover','04-inner-closed','05-inner-scroll-anchor']:
  assert phases[name]['columns']==4 and phases[name]['grid']['width']==1600,(name,phases[name])
 same_geometry(phases['03-inner-open-from-cover'],phases['04-inner-closed'])
 anchor=phases['05-inner-scroll-anchor']
 assert phases['04-inner-closed']['cards']!=anchor['cards'],'Actual touch swipe must change the visible grid anchor'
 for i in range(3):
  opened=phases['06-inner-open-'+str(i)];closed=phases['07-inner-closed-'+str(i)]
  for observed in [opened,closed]:
   same_geometry(anchor,observed);assert observed['grid']['identity']==anchor['grid']['identity']
  assert closed['cards']==anchor['cards'],'Closed drawer must retain actual native card identities, selected items and screen pixel scroll positions'
  same_geometry(anchor,phases['08-interrupted-'+str(i)])
 same_geometry(phases['09-rotated-inner-open'],phases['10-rotated-inner-closed']);assert phases['10-rotated-inner-closed']['columns']==4
 same_geometry(phases['11-cover-open-from-inner'],phases['12-cover-return-closed'])
 visible_anchor=[c for c in anchor['cards'] if c['visible'] and c['screen_bounds'][3]>c['screen_bounds'][1]]
 assert visible_anchor,'A real visible scroll anchor is required'
 anchor_key=visible_anchor[0]['channel']
 for name in ['10-rotated-inner-closed','12-cover-return-closed']:
  first=[c['channel'] for c in phases[name]['cards'] if c['visible'] and c['screen_bounds'][3]>c['screen_bounds'][1]][:phases[name]['columns']]
  assert anchor_key in first,('Native first-row channel anchor must survive the genuine window transition',name,anchor_key,first)
 interruptions=[s for s in outcome['steps'] if 'interruption' in s];intervals=[s['open_to_Back_start_ms'] for s in interruptions]
 assert len(intervals)==3 and any(s['open_to_Back_start_ms']<210 and 0<s['observed_before_Back_nav_left']-s['closed_nav_left']<(s['fully_open_nav_left']-s['closed_nav_left'])*.9 for s in interruptions),'No actual partially shifted original drawer was observed at Back injection; no inferred interruption PASS'
 # Use actual observed public preview bounds for moving synthetic-frame proof.
 preview_hashes=[]
 for name in ['05-inner-scroll-anchor','07-inner-closed-0','07-inner-closed-1','07-inner-closed-2']:
  info=json.loads((root/(name+'-nodes.json')).read_text());l,t,r,b=info['preview_frame'];w,h=r-l,b-t
  with Image.open(root/(name+'.png')) as image:
   region=image.convert('RGB').crop((l+int(w*.04),t+int(h*.04),l+int(w*.55),t+int(h*.32)))
   preview_hashes.append(hashlib.sha256(region.tobytes()).hexdigest())
  assert any('Cards QA 00001' in n['label'] and n['visible'] for n in info['nodes']),'Original selected/playing channel must remain visible in native Cards details'
 assert len(set(preview_hashes))>1,'Decoded synthetic preview motion was not demonstrated; static artwork is not playback proof'
 for path in root.glob('*-nodes.json'):
  info=json.loads(path.read_text())
  if not info['expected_drawer']:assert any('Cards QA 00001' in n['label'] and n['visible'] for n in info['nodes']),('Playing channel identity changed across actual window/drawer steps',path.name)
 result=dict(status='PASS_TARGETED_ANDROID17_CARDS_DRAWER_NATIVE_EVENTS_AND_MEASURED_VIEW_DATA',platform='API37 emulator with genuine WindowManager configuration changes; NOT physical Fold',phases=phases,original435_closed_geometry=baseline_phases,interruption_intervals_ms=intervals,preview_crop_sha256=preview_hashes,retained_grid_and_cards=True,unchanged_scroll_anchor=True,physical_Fold='USER_ACCEPTANCE_PENDING',decoder_object_identity='NOT_ACCESSIBLE_THROUGH_PUBLIC_UI; unchanged production playback and host reference-identity evidence retained',media_contact_sheets='NOT_ACCESSED',shutdown='NOT_CHANGED_NOT_RUN')
 (root/'VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n');return result
