"""Read-only DEX definitions and references for component preservation checks."""
import struct
def class_contract(data):
 """Read classfile declarations, including inherited Android/Java APIs."""
 assert data[:4]==b'\xca\xfe\xba\xbe'
 def h(p):return struct.unpack_from('>H',data,p)[0]
 def u(p):return struct.unpack_from('>I',data,p)[0]
 cp=[None]*h(8);p=10;i=1
 while i<len(cp):
  tag=data[p];p+=1
  if tag==1:n=h(p);p+=2;cp[i]=data[p:p+n].decode('utf-8','replace');p+=n
  elif tag in (7,8,16,19,20):cp[i]=h(p);p+=2
  elif tag in (3,4):p+=4
  elif tag in (5,6):p+=8;i+=1
  elif tag in (9,10,11,12,17,18):p+=4
  elif tag==15:p+=3
  else:raise ValueError(('Unknown classfile constant',tag))
  i+=1
 def cname(index):return 'L'+cp[cp[index]]+';' if index else None
 name=cname(h(p+2));parent=cname(h(p+4));p+=6
 count=h(p);p+=2;interfaces=[cname(h(p+j*2)) for j in range(count)];p+=count*2
 result=dict(parent=parent,interfaces=interfaces,fields=[],methods=[])
 for kind in ('fields','methods'):
  count=h(p);p+=2
  for j in range(count):
   result[kind].append((cp[h(p+2)],cp[h(p+4)]));attributes=h(p+6);p+=8
   for k in range(attributes):p+=6+u(p+2)
 return name,result
class Dex:
 def __init__(self,data):
  self.data=data
  self.strings=[self.string(self.u(self.u(60)+i*4)) for i in range(self.u(56))]
  self.types=[self.strings[self.u(self.u(68)+i*4)] for i in range(self.u(64))]
  self.protos=[]
  for i in range(self.u(72)):
   p=self.u(76)+12*i;offset=self.u(p+8)
   arguments=''.join(self.types[self.h(offset+4+j*2)] for j in range(self.u(offset))) if offset else ''
   self.protos.append('('+arguments+')'+self.types[self.u(p+4)])
  self.fields=[]
  for i in range(self.u(80)):
   p=self.u(84)+8*i;self.fields.append((self.types[self.h(p)],self.strings[self.u(p+4)],self.types[self.h(p+2)]))
  self.methods=[]
  for i in range(self.u(88)):
   p=self.u(92)+8*i;self.methods.append((self.types[self.h(p)],self.strings[self.u(p+4)],self.protos[self.h(p+2)]))
  self.classes={}
  for i in range(self.u(96)):
   p=self.u(100)+32*i;name=self.types[self.u(p)];parent=self.u(p+8);offset=self.u(p+24)
   interfaces=self.u(p+12)
   value=dict(parent=self.types[parent] if parent!=0xffffffff else None,
    interfaces=[self.types[self.h(interfaces+4+j*2)] for j in range(self.u(interfaces))] if interfaces else [],methods=[],fields=[])
   if offset:
    sizes=[]
    for j in range(4):n,offset=self.leb(offset);sizes.append(n)
    for kind,count in enumerate(sizes):
     index=0
     for j in range(count):
      diff,offset=self.leb(offset);flags,offset=self.leb(offset);index+=diff
      if kind>=2:code,offset=self.leb(offset)
      value['methods' if kind>=2 else 'fields'].append((self.methods if kind>=2 else self.fields)[index][1:])
   self.classes[name]=value
 def u(self,p):return struct.unpack_from('<I',self.data,p)[0]
 def h(self,p):return struct.unpack_from('<H',self.data,p)[0]
 def leb(self,p):
  result=shift=0
  while True:
   v=self.data[p];p+=1;result|=(v&127)<<shift;shift+=7
   if not v&128:return result,p
 def string(self,p):
  _,p=self.leb(p);end=self.data.index(b'\0',p);return self.data[p:end].decode('utf-8','replace')
