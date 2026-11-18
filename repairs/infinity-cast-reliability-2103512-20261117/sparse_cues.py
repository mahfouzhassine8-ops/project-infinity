"""Keep alternating real Matroska cues, retaining every media byte/offset."""
def vint(b,at,identifier=False):
 first=b[at];n=1
 while n<=8 and not first&(1<<(8-n)):n+=1
 if n>8 or at+n>len(b):raise ValueError('EBML bounds')
 value=int.from_bytes(b[at:at+n],'big');return (value if identifier else value&((1<<(7*n))-1)),n

def elements(b,begin,end):
 while begin<end:
  ident,ni=vint(b,begin,True);size,ns=vint(b,begin+ni);payload=begin+ni+ns
  if size==(1<<(7*ns))-1:size=end-payload
  assert size<=end-payload
  yield ident,begin,payload,payload+size;begin=payload+size
 assert begin==end

def sparse(data):
 b=bytearray(data);count=0
 for ident,at,start,end in elements(b,0,len(b)):
  if ident!=0x18538067:continue
  for ident,at,start,end in elements(b,start,end):
   if ident!=0x1c53bb6b:continue
   for ident,at,start,end in elements(b,start,end):
    if ident==0xbb:
     if count%2:b[at]=0xec # EBML Void; exact same width, size, payload and offsets.
     count+=1
 assert count==6,count
 return b
