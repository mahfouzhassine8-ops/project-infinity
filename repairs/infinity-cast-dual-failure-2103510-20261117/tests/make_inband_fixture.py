"""Test-only hev1 fixtures. Preserve real container offsets/packets/timestamps.

FFmpeg supplies genuine in-band parameter NALs. Replace codec-private PS arrays
with an EBML Void of identical total length. Optional later duplicate PS become
valid HEVC filler NALs of the SAME length; no VCL bytes or timing are rewritten.
"""
from pathlib import Path
import argparse,subprocess,hashlib,json

def vint(b,p,identifier=False):
 first=b[p];width=next((k for k in range(1,9) if first&(1<<(8-k))),None)
 if width is None or p+width>len(b):raise ValueError('test_ebml_vint')
 n=int.from_bytes(b[p:p+width],'big');return (n if identifier else n&((1<<(7*width))-1)),width

def children(b,start,end):
 p=start
 while p<end:
  key,iw=vint(b,p,True);size,sw=vint(b,p+iw);payload=p+iw+sw
  finish=end if size==(1<<(7*sw))-1 else payload+size
  if finish>end or finish<payload:raise ValueError('test_ebml_bounds')
  yield key,p,payload,finish,iw,sw;p=finish
 if p!=end:raise ValueError('test_ebml_end')

def size_bytes(n,width):
 if not(0<=n<(1<<(7*width))-1):raise ValueError('test_ebml_size')
 return (n|(1<<(7*width))).to_bytes(width,'big')

def void(length):
 for width in range(1,9):
  payload=length-1-width
  if 0<=payload<(1<<(7*width))-1:return b'\xec'+size_bytes(payload,width)+bytes(payload)
 raise ValueError('test_void_length')

def convert(source,out,first_only=True):
 control=out.with_suffix('.control.mkv');subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-copyts','-i',str(source),'-map','0','-c','copy','-bsf:v','hevc_mp4toannexb','-avoid_negative_ts','disabled','-write_crc32','0',str(control)],check=True)
 before=control.read_bytes();b=bytearray(before)
 if len(b)>16*1024*1024:raise ValueError('test_fixture_size')
 segment=next(v for v in children(b,0,len(b)) if v[0]==0x18538067);roots=list(children(b,segment[2],segment[3]));tracks=next(v for v in roots if v[0]==0x1654ae6b);video=None
 for entry in children(b,tracks[2],tracks[3]):
  if entry[0]!=0xae:continue
  fields=list(children(b,entry[2],entry[3]));codec=next((bytes(b[v[2]:v[3]]) for v in fields if v[0]==0x86),b'')
  if codec==b'V_MPEGH/ISO/HEVC':
   video=int.from_bytes(next(bytes(b[v[2]:v[3]]) for v in fields if v[0]==0xd7),'big');private=next(v for v in fields if v[0]==0x63a2);break
 if video is None:raise ValueError('test_hevc_track_missing')
 _,start,payload,end,iw,sw=private;h=bytes(b[payload:end])
 if len(h)<23 or h[0]!=1:raise ValueError('test_hvcc_missing')
 short=bytearray(h[:23]);short[22]=0;replacement=size_bytes(23,sw)+short+void(len(h)-23)
 assert len(replacement)==end-(start+iw);b[start+iw:end]=replacement
 width=(h[21]&3)+1;key_count=replaced=0
 def block(v):
  nonlocal key_count,replaced
  _,_,at,end,_,_=v;track,tw=vint(b,at);flags=at+tw+2;at=flags+1
  if track!=video:return
  if b[flags]&6:raise ValueError('test_video_lacing_not_supported')
  key=bool(b[flags]&128)
  if key:key_count+=1
  while at<end:
   if end-at<width:raise ValueError('test_nal_length')
   n=int.from_bytes(b[at:at+width],'big');at+=width
   if n<2 or n>end-at:raise ValueError('test_nal_bounds')
   kind=(b[at]>>1)&63
   if first_only and key_count>1 and kind in(32,33,34):
    if n<3:raise ValueError('test_parameter_length')
    b[at:at+n]=bytes((76,1))+bytes([255])*(n-3)+bytes([128]);replaced+=1
   at+=n
 for cluster in roots:
  if cluster[0]!=0x1f43b675:continue
  for v in children(b,cluster[2],cluster[3]):
   if v[0]==0xa3:block(v)
   elif v[0]==0xa0:
    for w in children(b,v[2],v[3]):
     if w[0]==0xa1:block(w)
 assert len(before)==len(b) and key_count>=2
 out.write_bytes(b)
 r=subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(out),'-f','null','-'],capture_output=True,text=True);assert r.returncode==0 and not r.stderr.strip(),r.stderr
 result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'control_sha256':hashlib.sha256(before).hexdigest(),'fixture_sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'private_before':len(h),'private_after':23,'keys':key_count,'later_parameter_NALs_replaced_by_valid_filler':replaced,'full_decode':'PASS','container_offsets_and_sample_times':'UNCHANGED_FROM_CONTROL','production_codec_metadata':'NOT_MODIFIED; TEST_FIXTURE_ONLY'}
 out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--repeat',action='store_true');a=p.parse_args();print(json.dumps(convert(a.source,a.out,not a.repeat),indent=2))
