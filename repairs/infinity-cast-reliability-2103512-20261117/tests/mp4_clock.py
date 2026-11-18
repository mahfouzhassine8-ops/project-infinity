"""Read actual fMP4 sample clock fields, without a decoder/parser duration guess."""
import struct

def u32(b,p):return int.from_bytes(b[p:p+4],'big')
def boxes(b,start=0,end=None):
 end=len(b)if end is None else end
 while start<end:
  assert end-start>=8;n=u32(b,start);h=8
  if n==1:assert end-start>=16;n=int.from_bytes(b[start+8:start+16],'big');h=16
  assert h<=n<=end-start;yield start,n,b[start+4:start+8],h;start+=n
 assert start==end

def track_samples(media,track=2):
 result=[]
 for start,size,kind,head in boxes(media):
  if kind!=b'moof':continue
  for pos,length,kind,head in boxes(media,start+head,start+size):
   if kind!=b'traf':continue
   children=list(boxes(media,pos+head,pos+length));tfhd=next(x for x in children if x[2]==b'tfhd');p=tfhd[0];flags=u32(media,p+8)&0xffffff
   if u32(media,p+12)!=track:continue
   at=p+16
   if flags&1:at+=8
   if flags&2:at+=4
   duration=u32(media,at)if flags&8 else 0
   if flags&8:at+=4
   tfdt=next(x for x in children if x[2]==b'tfdt');p=tfdt[0];version=media[p+8];clock=int.from_bytes(media[p+12:p+12+(8 if version else 4)],'big')
   for p,n,k,h in children:
    if k!=b'trun':continue
    version=media[p+8];flags=u32(media,p+8)&0xffffff;count=u32(media,p+12);at=p+16
    if flags&1:at+=4
    if flags&4:at+=4
    for _ in range(count):
     d=duration
     if flags&256:d=u32(media,at);at+=4
     if flags&512:at+=4
     if flags&1024:at+=4
     c=0
     if flags&2048:c=int.from_bytes(media[at:at+4],'big',signed=version==1);at+=4
     assert d>0;result.append([clock+c,clock,d]);clock+=d
    assert at==p+n
 return result
