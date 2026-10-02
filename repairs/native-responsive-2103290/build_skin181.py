#!/usr/bin/env python3
"""Build Infinity skin 1.0.5.181 Native Responsive Layout from the exact 1.0.5.178 skin.

Legacy profile folders remain byte-preserved except addon.xml metadata. A complete responsive/
presentation contract is added. Every responsive class contains every XML window, so Kodi native
geometry never depends on a missing skin profile. Existing optimized class files are reused where
available and 16x9 fills coverage gaps.

Coordinates are converted so positions follow their current parent while small controls keep a
stable short-axis size. Large structural surfaces stretch with their parent. Kodi owns the exact
logical canvas and re-parses these percentages after a settled resize.
"""
from pathlib import Path
import argparse, hashlib, json, re, shutil, zipfile
import xml.etree.ElementTree as ET

EXPECTED_PARENT="8e14c98fa50dfc5defe16732588a509e819d9e99983b91541ba1edf23ca60cd3"
VERSION="1.0.5.181"
OUT_NAME="Infinity-1.0.5.181-Native-Responsive-Layout-RC1.zip"
NUM=re.compile(r'^\s*(-?\d+(?:\.\d+)?)\s*$')
POSITIONS={'left','top','posx','posy','right','bottom','centerleft','centerright','centertop','centerbottom'}
SCALARS={'offsetx','offsety','textoffsetx','textoffsety','itemgap','movement','spinwidth','spinheight',
         'spinposx','spinposy','sliderwidth','sliderheight','radiowidth','radioheight','radioposx',
         'radioposy','colorwidth','colorheight','colorposx','colorposy'}
STRUCTURAL={'group','grouplist','panel','list','wraplist','fixedlist','epggrid','video','game',
            'visualisation','multiimage'}
CLASSES={
 'base':('16x9',(1920,1080)),
 'wide':('16x9',(1920,1080)),
 'ultrawide':('20x9',(2400,1080)),
 'landscape':('6x5',(1440,1200)),
 'square':('fallback',(1100,1000)),
 'portrait':('5x6',(1200,1440)),
 'tall':('portrait',(1080,2400)),
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def number(text):
    if text is None:return None
    m=NUM.match(text);return float(m.group(1)) if m else None
def fmt(v):
    if abs(v-round(v))<1e-6:return str(int(round(v)))
    return f"{v:.3f}".rstrip('0').rstrip('.')
def pct(v,parent):
    if not parent:return fmt(v)
    return f"{v/parent*100:.4f}".rstrip('0').rstrip('.')+"%"

def dim(el,tag,parent):
    n=el.find(tag)
    if n is None or not n.text:return None
    raw=n.text.strip();v=number(raw)
    if v is not None:return v
    if raw.endswith('%'):
      try:return float(raw[:-1])*parent/100
      except ValueError:return None
    return None

def pos(el,a,b,parent):
    for tag in (a,b):
      n=el.find(tag)
      if n is not None and n.text:
        raw=n.text.strip();v=number(raw)
        if v is not None:return v
        if raw.endswith('%'):
          try:return float(raw[:-1])*parent/100
          except ValueError:return None
    return 0.0

def ref_size(el,pw,ph):
    w=dim(el,'width',pw);h=dim(el,'height',ph)
    left=pos(el,'left','posx',pw);top=pos(el,'top','posy',ph)
    right=dim(el,'right',pw);bottom=dim(el,'bottom',ph)
    if w is None and right is not None:w=max(1.0,pw-left-right)
    if h is None and bottom is not None:h=max(1.0,ph-top-bottom)
    if w is None:w=max(1.0,pw-left)
    if h is None:h=max(1.0,ph-top)
    return w,h

def convert_property_block(el,pw,ph,scale):
    # Include/default/definition fragments become control properties after Kodi resolves them.
    # Treat their edge positions as parent-relative and only stretch large structural dimensions.
    for tag in POSITIONS:
      node=el.find(tag)
      if node is None or not node.text:continue
      v=number(node.text)
      if v is None:continue
      axis=pw if tag in {'left','posx','right','centerleft','centerright'} else ph
      node.text=fmt(v*scale) if v<0 else pct(v,axis)
    for tag,axis in (('width',pw),('height',ph)):
      node=el.find(tag)
      if node is None or not node.text:continue
      v=number(node.text)
      if v is None:continue
      node.text=pct(v,axis) if axis and v/axis>=0.30 else fmt(v*scale)
    for tag in SCALARS:
      node=el.find(tag)
      if node is not None and node.text:
        v=number(node.text)
        if v is not None:node.text=fmt(v*scale)

def convert_control(el,pw,ph,scale):
    ctype=(el.get('type') or '').lower()
    ow,oh=ref_size(el,pw,ph)
    for tag in POSITIONS:
      node=el.find(tag)
      if node is None or not node.text:continue
      v=number(node.text)
      if v is None:continue
      axis=pw if tag in {'left','posx','right','centerleft','centerright'} else ph
      node.text=fmt(v*scale) if v<0 else pct(v,axis)
    for tag,axis in (('width',pw),('height',ph)):
      node=el.find(tag)
      if node is None or not node.text:continue
      v=number(node.text)
      if v is None:continue
      ratio=v/axis if axis else 0
      stretch=ratio>=0.48 or (ctype in STRUCTURAL and ratio>=0.30)
      node.text=pct(v,axis) if stretch else fmt(v*scale)
    for tag in SCALARS:
      node=el.find(tag)
      if node is not None and node.text:
        v=number(node.text)
        if v is not None:node.text=fmt(v*scale)
    camera=el.find('camera')
    if camera is not None:
      for attr,axis in (('x',ow),('y',oh)):
        v=number(camera.get(attr))
        if v is not None and v>=0:camera.set(attr,pct(v,axis))
    for child in list(el):
      if child.tag in ('itemlayout','focusedlayout'):
        iw=number(child.get('width')) or ow;ih=number(child.get('height')) or oh
        if number(child.get('width')) is not None:child.set('width',fmt(iw*scale))
        if number(child.get('height')) is not None:child.set('height',fmt(ih*scale))
        for gc in child.findall('control'):convert_control(gc,iw,ih,scale)
      elif child.tag=='control':
        convert_control(child,ow,oh,scale)

def convert_xml(src,dst,ref):
    tree=ET.parse(src);root=tree.getroot();rw,rh=ref;scale=1080.0/min(rw,rh)
    if root.tag=='fonts':
      for n in root.iter('size'):
        v=number(n.text)
        if v is not None:n.text=fmt(v*scale)
    if root.tag=='window':
      # Window/dialog origin is presentation too. Keep it proportional to the dynamic Kodi canvas
      # so dialogs do not remain pinned to old 1920x1080 coordinates after a Fold resize.
      coords=root.find('coordinates')
      if coords is not None:
        for tag,axis in (('left',rw),('posx',rw),('top',rh),('posy',rh)):
          node=coords.find(tag)
          if node is not None and node.text:
            v=number(node.text)
            if v is not None: node.text=fmt(v*scale) if v<0 else pct(v,axis)
        for origin in coords.findall('origin'):
          for attr,axis in (('x',rw),('y',rh)):
            v=number(origin.get(attr))
            if v is not None: origin.set(attr,fmt(v*scale) if v<0 else pct(v,axis))
      controls=root.find('controls')
      if controls is not None:
        for c in controls.findall('control'):convert_control(c,rw,rh,scale)
    # Includes/defaults/definitions are fragments that Kodi merges into controls before factory
    # creation. Convert their property blocks too, and process each top-level control exactly once.
    parent={child:par for par in root.iter() for child in par}
    for block in root.iter():
      if block.tag in ('include','default','definition'):
        convert_property_block(block,rw,rh,scale)
    for ctl in root.iter('control'):
      par=parent.get(ctl)
      # Direct window controls were already converted above; nested controls are recursively owned
      # by their nearest top-level control. This catches controls rooted in include/definition blocks.
      if par is not None and par.tag in ('controls','control','itemlayout','focusedlayout'):
        continue
      convert_control(ctl,rw,rh,scale)
    dst.parent.mkdir(parents=True,exist_ok=True)
    tree.write(dst,encoding='utf-8',xml_declaration=True)

def build(parent_zip,out_dir):
    if sha(parent_zip)!=EXPECTED_PARENT:
      raise RuntimeError("Not exact Infinity 1.0.5.178 parent")
    work=out_dir/'work';root=out_dir/'root'
    if out_dir.exists():shutil.rmtree(out_dir)
    root.mkdir(parents=True)
    with zipfile.ZipFile(parent_zip) as z:
      if z.testzip() is not None:raise RuntimeError("Parent ZIP CRC failure")
      z.extractall(root)
    skin=root/'skin.infinity.diggz'
    full=skin/'16x9';names=sorted(p.name for p in full.glob('*.xml'))
    if len(names)!=183:raise RuntimeError(f"Expected 183 full 16x9 XML files, got {len(names)}")
    resp=skin/'responsive'
    if resp.exists():shutil.rmtree(resp)
    manifest={'schema':1,'engine':'Infinity Native Responsive Layout v1','short_axis_units':1080,
              'classes':{},'base_skin':'1.0.5.178','legacy_profiles_preserved':True,
              'native_owner':'Kodi current usable window','fallback_required':False}
    for cls,(overlay,ref) in CLASSES.items():
      dest=resp/cls;dest.mkdir(parents=True)
      optimized=0
      for name in names:
        src=full/name;src_ref=(1920,1080)
        alternate=skin/overlay/name
        if cls!='base' and alternate.exists():
          src=alternate;src_ref=ref;optimized+=1
        convert_xml(src,dest/name,src_ref)
      # Kodi loads the fontset when the skin starts, not on every responsive class transition.
      # Keep one normalized font contract across every class.
      if cls!='base':
        shutil.copy2(resp/'base'/'Font.xml',dest/'Font.xml')
      manifest['classes'][cls]={'files':len(names),'overlay_source':overlay,
                                'optimized_files':optimized,'reference':list(ref)}
    marker=skin/'resources/infinity-native-responsive-v1.json'
    marker.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    addon=skin/'addon.xml';text=addon.read_text()
    if 'version="1.0.5.178"' not in text:raise RuntimeError("Parent skin version mismatch")
    addon.write_text(text.replace('version="1.0.5.178"',f'version="{VERSION}"',1))
    for cls in CLASSES:
      files=list((resp/cls).glob('*.xml'))
      if len(files)!=183:raise RuntimeError(f"Incomplete responsive class {cls}")
      for p in files:ET.parse(p)
    output=out_dir/OUT_NAME
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
      for p in sorted(root.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(root).as_posix())
    with zipfile.ZipFile(output) as z:
      if z.testzip() is not None:raise RuntimeError("Output ZIP CRC failure")
    proof={'schema':1,'parent_sha256':EXPECTED_PARENT,'skin_version':VERSION,
           'zip_sha256':sha(output),'responsive_contract':manifest,
           'all_responsive_classes_complete':True,'legacy_profiles_preserved':True}
    (out_dir/'SKIN-PROOF.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
    return output,proof

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',type=Path,required=True)
    ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args()
    output,proof=build(a.parent.resolve(),a.out_dir.resolve())
    print(output);print(proof['zip_sha256'])
if __name__=='__main__':main()
