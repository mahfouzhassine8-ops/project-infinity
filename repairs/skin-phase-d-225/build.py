#!/usr/bin/env python3
"""Forward-only Skin 225: minimal XML edits, raw-copy untouched ZIP records."""
from pathlib import Path
import argparse, collections, hashlib, json, re, shutil, struct, zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

PARENT_SHA='e23d5d08c7737f317c2d55ae3f27e8746a019afd02dc20f6fbc73dc48c0c994e'
PARENT_COMMIT='224965e068bae594daabf4f81fbaba9dcfaae29f'
MOTION='!String.IsEqual(Window(Home).Property(Infinity.OptionalMotionAllowed),false)'
PROTECTED={'InfinityFilePreview.xml','FileBrowser.xml','DialogContextMenu.xml','Includes_InfinityPreview.xml'}
def sha(b):return hashlib.sha256(b).hexdigest()

class Edit:
    """Change individual XML tokens without serializing unrelated bytes."""
    def __init__(self,data):
        self.s=data.decode('utf-8');self.root=ET.fromstring(self.s);self.edits=[];self.reasons=set();self.spans={}
        nodes=iter(self.root.iter()); stack=[]
        for m in re.finditer(r'<!--[\s\S]*?-->|<\?[\s\S]*?\?>|</?[^>]+>',self.s):
            token=m.group()
            if token.startswith(('<!--','<?','<!')):continue
            if token.startswith('</'):
                e,start,opening=stack.pop();self.spans[e]=(start,opening,m.start(),m.end())
            else:
                e=next(nodes);assert e.tag==re.match(r'<([^\s/>]+)',token)[1]
                if token.endswith('/>'):self.spans[e]=(m.start(),m.end(),m.end(),m.end())
                else:stack.append((e,m.start(),m.end()))
        assert not stack
    def replace(self,start,end,s,why):self.edits.append((start,end,s));self.reasons.add(why)
    def text(self,e,value,why):
        if e.text==str(value):return
        a,b,c,d=self.spans[e]
        if b==d:self.replace(a,d,f'<{e.tag}>{escape(str(value))}</{e.tag}>',why)
        else:self.replace(b,c,escape(str(value)),why)
    def set(self,e,tag,value,why):
        child=e.find(tag)
        if child is not None:self.text(child,value,why)
        else:
            a,b,c,d=self.spans[e];self.replace(b,b,f'<{tag}>{escape(str(value))}</{tag}>',why)
    def delete(self,e,tag,why):
        child=e.find(tag)
        if child is not None:
            a,b,c,d=self.spans[child];self.replace(a,d,'',why)
    def attr(self,e,key,value,why):
        a,b,c,d=self.spans[e];s=self.s[a:b]
        new=escape(value,{'"':'&quot;'})
        if key in e.attrib:s=re.sub(r'\b'+key+r'=("[^"]*"|\x27[^\x27]*\x27)',key+'="'+new+'"',s,count=1)
        else:s=s[:-1]+' '+key+'="'+new+'">'
        self.replace(a,b,s,why)
    def geometry(self,e,why,**kv):
        for k,v in kv.items():self.set(e,k,v,why)
        if 'right' in kv:self.delete(e,'width' if 'left' in kv else 'left',why)
        if 'bottom' in kv:self.delete(e,'height' if 'top' in kv else 'top',why)
    def control(self,id):return self.root.find(f'.//control[@id="{id}"]')
    def done(self):
        out=self.s;last=len(out)+1
        for a,b,s in sorted(self.edits,reverse=True):
            assert b<=last,(a,b,last);out=out[:a]+s+out[b:];last=a
        ET.fromstring(out);return out.encode('utf-8')

def patch(data,name):
    e=Edit(data);root=e.root;file=Path(name).name;active=name.startswith('unified/')
    if file in PROTECTED:return data,[]
    # A transition may be optional, but a Conditional transform may encode layout or state.
    # Only event animations are gated here; geometry/status conditionals are untouched.
    for a in root.iter('animation'):
        event=(a.get('type') or a.text or '').strip().lower()
        cond=a.get('condition','')
        duration=max([int(float(x.get('time','0'))) for x in [a,*a.findall('effect')] if re.fullmatch(r'\d+(\.\d+)?',x.get('time','0'))] or [0])
        if event in ('windowopen','windowclose','visible','hidden','visiblechange') and duration>0 and 'Infinity.OptionalMotionAllowed' not in cond:
            e.attr(a,'condition',(f'[{cond}] + ' if cond else '')+MOTION,'D01: event transitions obey existing reduced/off motion policy; conditional layout transforms retained')
    # Decode provider/Home artwork on Kodi's existing texture-loader path, not GUI evaluation.
    if file.startswith(('Home','View_','Includes')):
        for t in root.iter('texture'):
            value=t.text or ''
            if '$INFO[' in value and re.search(r'(?:ListItem(?:Absolute\([^)]*\))?\.)?(?:Art\(|Thumb\])',value) and t.get('background')!='true':
                e.attr(t,'background','true','D02: asynchronous selected/provider artwork loading avoids synchronous texture decode on navigation')
    if not active:return e.done(),sorted(e.reasons)
    if file=='Custom_1194_InfinityCommandCenter.xml':
        why='D03: keep Command Center scroll viewport within the glass panel at every window aspect'
        c=e.control('1194888');e.geometry(c,why,top='5%',bottom='5%')
        # Natural ordering of header/footer buttons was reversed by a prior scroll conversion.
        why='D04: restore reachable vertical focus through Command Center playback shortcuts'
        links={1194105:{'onup':'1194103','ondown':'1194201'},1194106:{'onup':'1194104','ondown':'1194203'},1194201:{'onup':'1194105','ondown':'1194300','onleft':'1194201','onright':'1194202'},1194202:{'onup':'1194105','ondown':'1194300','onleft':'1194201','onright':'1194203'},1194203:{'onup':'1194106','ondown':'1194300','onleft':'1194202','onright':'1194203'},1194300:{'onup':'1194202'}}
        for id,kv in links.items():
            for k,v in kv.items():e.set(e.control(str(id)),k,v,why)
    if file=='SettingsCategory.xml':
        why='D05: reserve a fixed Settings header and footer; align category viewport to row width on adaptive windows'
        title=root.find('./controls/control[@type="label"]');e.geometry(title,why,top='24',height='64')
        for c in root.findall('./controls/control[@type="image"]'):
            if c.findtext('top') in ('10.5417%',):e.geometry(c,why,top='112',bottom='16')
            elif c.findtext('top')=='9.625%':e.set(c,'top','100',why)
        e.geometry(e.control('3'),why,top='128',bottom='104',width=e.control('10').findtext('width'))
        e.geometry(e.control('5'),why,top='128',bottom='24')
        e.geometry(e.control('60'),why,top='128',bottom='24')
        for k,v in {'onleft':'5','onright':'5','onup':'60','ondown':'60'}.items():e.set(e.control('60'),k,v,why)
    if file=='Custom_1193_InfinityBrowse.xml':
        why='D06: keep browser title/subtitle and touch controls separate on short windows; preserve native grid and recovery actions'
        for c in root.findall('./controls/control[@type="label"]'):
            if 'Infinity.BrowseTitle' in (c.findtext('label') or ''):e.set(c,'top','24',why)
            elif 'Infinity.BrowseSubtitle' in (c.findtext('label') or ''):e.set(c,'top','86',why)
            elif c.findtext('top')=='98.25%':e.geometry(c,why,bottom='20')
        e.geometry(e.control('10'),why,top='24',width='80',height='96')
        e.geometry(e.control('12'),why,top='24',height='96')
    if file=='Custom_1198_InfinityNav.xml':
        why='D07: remove extreme 11-to-100-percent drawer zoom; retain approved surface and calm opacity transition'
        for a in root.iter('animation'):
            if a.get('effect')=='zoom' and a.get('start','').startswith(('11.47','100')):
                # One token replacement so attributes are never patched over each other.
                start,end=('0','100') if (a.text or '').strip()=='WindowOpen' else ('100','0')
                a0,b,c,d=e.spans[a]
                e.replace(a0,b,f'<animation effect="fade" start="{start}" end="{end}" time="{160 if start=="0" else 110}" condition="{MOTION}">',why)
    if file=='Custom_1195_InfinityAudioSubtitles.xml':
        why='D08: audio/subtitle buttons overlap when percent Y spacing shrinks; use one centered fixed-height compact content group'
        controls=root.find('controls');children=list(controls);start=e.spans[children[1]][0];end=e.spans[children[-1]][3]
        e.replace(start,start,'<control type="group"><centerleft>50%</centerleft><centertop>50%</centertop><width>76%</width><height>800</height>\n',why);e.replace(end,end,'\n</control>',why)
        for c in children[1:3]:e.geometry(c,why,left='0',top='0',width='100%',height='100%')
        e.geometry(children[3],why,left='32',top='34',width='60',height='60')
        e.geometry(children[4],why,left='112',top='24',right='128',height='64')
        e.geometry(children[5],why,left='112',top='100',right='32',height='40')
        close=e.control('5199');e.geometry(close,why,right='24',top='24',width='96',height='96')
        for k in ('onup','ondown','onleft','onright'):e.set(close,k,'5101',why)
        for i,id in enumerate(['5101','5102','5103']):
            c=e.control(id);top=230+i*168
            # The global button default supplies width=450 if width is omitted.
            # Give each row an inset group and an explicit full-width button.
            idx=children.index(c);row_end=e.spans[children[idx+2]][3]
            row_start=e.spans[c][0]
            e.replace(row_start,row_start,'<control type="group"><left>32</left><right>32</right><top>0</top><height>100%</height>\n',why)
            e.replace(row_end,row_end,'\n</control>',why)
            e.geometry(c,why,left='0',width='100%',top=str(top),height='144');e.set(c,'textoffsety','-20',why)
            e.set(c,'onleft','5199',why);e.set(c,'onright','5199',why)
            e.geometry(children[idx+1],why,left='24',top=str(top+46),width='34',height='34')
            e.geometry(children[idx+2],why,left='86',right='8',top=str(top+92),height='32')
    if file=='Custom_1196_InfinityPlaybackSpeed.xml':
        why='D09: prevent speed dialog heading/value/action overlap on landscape; enlarge and connect the close target'
        controls=root.find('controls');children=list(controls);start=e.spans[children[1]][0];end=e.spans[children[-1]][3]
        e.replace(start,start,'<control type="group"><centerleft>50%</centerleft><centertop>50%</centertop><width>70%</width><height>560</height>\n',why);e.replace(end,end,'\n</control>',why)
        for c in children[1:3]:e.geometry(c,why,left='0',top='0',width='100%',height='100%')
        labels=[c for c in children if c.get('type')=='label']
        for i,(c,top,height) in enumerate(zip(labels,['24','108','180','470'],['64','44','90','44'])):e.geometry(c,why,left='40',right='136' if i==0 else '40',top=top,height=height)
        close=e.control('5299');e.geometry(close,why,right='24',top='24',width='96',height='96')
        for k in ('onup','ondown','onleft','onright'):e.set(close,k,'5202',why)
        for i,id in enumerate(['5201','5202','5203']):
            c=e.control(id);e.geometry(c,why,left=str(8+i*29)+'%',top='316',width='26%',height='112');e.set(c,'onup','5299',why)
    if file=='Custom_1190_InfinityPalette.xml':
        why='D10: reserve command palette header/query/footer instead of overlapping fixed text with percentage rows'
        for c in root.findall('./controls/control[@type="label"]'):
            if c.findtext('label')=='INFINITY COMMAND PALETTE':e.set(c,'top','17%',why)
            elif 'Infinity.Palette.Query' in (c.findtext('label') or ''):e.set(c,'top','23%',why)
        # Keep original 16%-84% panel; uniform bounded content independent of row count.
        e.geometry(e.control('119000'),why,top='29%',bottom='24%')
        for id in ('119001','119002','119003'):e.geometry(e.control(id),why,top='77%',height='80')
    return e.done(),sorted(e.reasons)

def raw_zip(parent,output,changes):
    """Preserve each untouched local record and compressed payload exactly; no duplicate names."""
    raw=parent.read_bytes();central=[]
    with zipfile.ZipFile(parent) as z,output.open('wb') as f:
        for info in z.infolist():
            off=f.tell()
            if info.filename not in changes:
                a=info.header_offset; n,x=struct.unpack_from('<HH',raw,a+26);end=a+30+n+x+info.compress_size
                assert not info.flag_bits&8,'data descriptors require explicit preservation support'
                f.write(raw[a:end]); clone=info
            else:
                import io
                b=io.BytesIO()
                with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as one:
                    clone=zipfile.ZipInfo(info.filename,info.date_time);clone.compress_type=info.compress_type;clone.external_attr=info.external_attr;one.writestr(clone,changes[info.filename])
                with zipfile.ZipFile(b) as one:clone=one.infolist()[0];f.write(b.getvalue()[:one.start_dir])
            clone.header_offset=off;central.append(clone)
        start=f.tell()
        # stdlib writes the central directory only: records above have already been emitted.
        z2=zipfile.ZipFile(f,'a');z2.filelist=central;z2.NameToInfo={i.filename:i for i in central};z2.start_dir=start;z2._didModify=True;z2.close()

def build(parent,work,output):
    assert sha(parent.read_bytes())==PARENT_SHA
    work.mkdir(parents=True,exist_ok=False);changes={};inventory=[]
    with zipfile.ZipFile(parent) as z:
        original={i.filename:z.read(i) for i in z.infolist() if not i.is_dir()}
        for name,data in original.items():
            rel=name.removeprefix('skin.infinity.diggz/');new=data;reasons=[]
            if rel.endswith('.xml') and '/' in rel and not rel.startswith(('resources/','shortcuts/','language/')):new,reasons=patch(data,rel)
            if rel=='addon.xml':
                new=data.replace(b'version="1.0.5.224"',b'version="1.0.5.225"',1)
                new=re.sub(rb'<description lang="en_GB">.*?</description>',b'<description lang="en_GB">Infinity .225 experimental Phase D: forward from exact .224. Coordinated motion policy, asynchronous artwork, adaptive dialog and Settings geometry, and focus/touch corrections. Existing watched/recovery, ZIP preview, Rails, playback, Cobra and shutdown retained. Physical Galaxy Fold acceptance pending.</description>',new,flags=re.S);reasons=['D00: forward experimental version and accurate candidate description']
            if rel=='resources/lib/infinity_native_ambient.py':
                # Reuse the complete existing repair, not a new unrecognized script digest.
                # Both .224 and this exact repaired source are accepted by the current APK.
                import sys
                sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'e2e-mobile-2103303'))
                from ambient_lifecycle import repair
                assert sha(data)=='3e33144282d81aa727466f530fd3d37deaee8357c5973c0c7b932bbcc3db1f5f'
                new=repair(data.decode('utf-8')).encode('utf-8')
                assert sha(new)=='de30a5114302a303638c589342024b348d3070c5aa76ba4a360d2506dd4402f7'
                reasons=['D11: restore existing APK-approved Ambient lifecycle repair: release hidden textures, idempotent close, resize rebinding, bounded optional sampling']
            p=work/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(new)
            if new!=data:changes[name]=new;inventory.append(dict(file=rel,before_sha256=sha(data),after_sha256=sha(new),reasons=reasons))
        # Update the candidate integrity manifest, never the historical lock receipt.
        rel='Infinity-Protected-Manifest.json';manifest=json.loads((work/rel).read_text())
        for name in manifest.get('protected_files',{}):
            if name!=rel and (work/name).is_file():manifest['protected_files'][name]=sha((work/name).read_bytes())
        manifest.update(candidate=225,candidate_version='1.0.5.225',skin_version='1.0.5.225',candidate_locked=False,phase_d_225={'parent_sha256':PARENT_SHA,'source_checkpoint':PARENT_COMMIT,'physical_fold_verified':False,'native_or_userdata_changes':False})
        new=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode();(work/rel).write_bytes(new);name='skin.infinity.diggz/'+rel;changes[name]=new
        inventory.append(dict(file=rel,before_sha256=sha(original[name]),after_sha256=sha(new),reasons=['D00: candidate integrity hashes and provenance; historical lock receipt untouched']))
    output.parent.mkdir(parents=True,exist_ok=True);raw_zip(parent,output,changes)
    with zipfile.ZipFile(parent) as a,zipfile.ZipFile(output) as b:
        assert b.testzip() is None;assert len(b.namelist())==len(set(b.namelist()));assert a.namelist()==b.namelist()
        untouched=[n for n in original if n not in changes]
        raw_a=parent.read_bytes();raw_b=output.read_bytes()
        for n in untouched:
            assert a.read(n)==b.read(n)
            def compressed(z,raw):
                i=z.getinfo(n);k,x=struct.unpack_from('<HH',raw,i.header_offset+26);p=i.header_offset+30+k+x;return raw[p:p+i.compress_size]
            assert compressed(a,raw_a)==compressed(b,raw_b),n
    report=dict(version='1.0.5.225',parent_version='1.0.5.224',parent_sha256=PARENT_SHA,source_checkpoint=PARENT_COMMIT,file=output.name,bytes=output.stat().st_size,sha256=sha(output.read_bytes()),changed_files=inventory,unchanged_payload_and_compressed_files=len(untouched),added=[],removed=[],xml_parsed=sum(1 for p in work.rglob('*.xml') if ET.parse(p) is not None),native_changed=False,physical_fold_verified=False)
    (output.parent/'SKIN225-PRESERVATION.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=build(a.parent,a.work,a.output);print(json.dumps({k:len(v) if k=='changed_files' else v for k,v in r.items()},indent=2))
