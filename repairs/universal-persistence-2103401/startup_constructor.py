"""Read-only ELF proof for the RC8 pre-Kodi talloc constructor startup crash.

Resolve the four changed address operands, rather than treating changed machine
addresses as a changed function or masking arbitrary instructions.
"""
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path
def signed(value,bits):return value-(1<<bits) if value&(1<<(bits-1)) else value
def inspect(apk,pin):
 with zipfile.ZipFile(apk) as z:b=z.read('lib/arm64-v8a/libkodi.so')
 assert hashlib.sha256(b).hexdigest()==pin and b[:6]==b'\x7fELF\x02\x01'
 off=struct.unpack_from('<Q',b,40)[0];size,count,namesid=struct.unpack_from('<HHH',b,58)
 sections=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*size) for i in range(count)]
 names=sections[namesid];names=b[names[4]:names[4]+names[5]]
 named={names[s[0]:names.find(b'\0',s[0])].decode():s for s in sections}
 def symbols(tab):
  s=named[tab];strings=sections[s[6]];strings=b[strings[4]:strings[4]+strings[5]];result=[]
  for at in range(s[4],s[4]+s[5],s[9]):
   ni,info,other,ndx,value,length=struct.unpack_from('<IBBHQQ',b,at)
   name=strings[ni:strings.find(b'\0',ni)].decode();result.append(dict(name=name,section=ndx,value=value,size=length))
  return result
 syms={s['name']:s for s in symbols('.symtab') if s['name'] in ('talloc_lib_init','talloc_magic')};dynamic=symbols('.dynsym')
 reloc=named['.rela.plt'];plt=named['.plt'];calls={}
 for i,at in enumerate(range(reloc[4],reloc[4]+reloc[5],reloc[9])):
  offset,info,addend=struct.unpack_from('<QQq',b,at);assert info&0xffffffff==1026
  calls[plt[3]+32+i*16]=dynamic[info>>32]['name']
 fn=syms['talloc_lib_init'];assert fn['size']==100;s=sections[fn['section']];at=s[4]+fn['value']-s[3];raw=b[at:at+100];words=list(struct.unpack('<25I',raw));normal=[hex(w) for w in words]
 for i,name in [(4,'getauxval'),(7,'rand')]:
  w=words[i];assert w&0xfc000000==0x94000000
  target=fn['value']+4*i+signed(w&0x3ffffff,26)*4;assert calls[target]==name
  normal[i]='BL '+name
 def adrp(i):
  w=words[i];assert w&0x9f000000==0x90000000
  displacement=signed(((w>>5)&0x7ffff)*4+((w>>29)&3),21)*4096
  return ((fn['value']+4*i)&~4095)+displacement
 assert words[17]==0x90000008 and words[18]&0xffc003ff==0x91000108
 assert adrp(17)+((words[18]>>10)&0xfff)==fn['value']
 normal[17]='ADRP talloc_lib_init page';normal[18]='ADD talloc_lib_init page offset'
 assert words[21]&31==9 and words[22]&0xffc003ff==0xb9000128
 assert adrp(21)+((words[22]>>10)&0xfff)*4==syms['talloc_magic']['value']
 normal[21]='ADRP talloc_magic page';normal[22]='STR w8 talloc_magic'
 assert words[3]==0x52800320 and words[6]==0xaa0003f3 and words[15]==0xb8686a68
 return dict(engine_sha256=pin,function=fn,words=[hex(w) for w in words],normalized=normal,
  raw_function_sha256=hashlib.sha256(raw).hexdigest(),fault_instruction='LDR w8, [x19, x8]; offset 60; four-byte read from getauxval(AT_RANDOM) plus rand()%12')
def main():
 p=argparse.ArgumentParser()
 for n in ['input','candidate','tombstone','out']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();old=inspect(a.input,'1c34d5a24ab4d39785282849e280153c71f0ddef29bbcf91ad894de9de2f5254');new=inspect(a.candidate,'a538ef1cca66a8841ba116e3af028fc76dcebecfcb94ac5db9a0405d023e3fc8');assert old['normalized']==new['normalized']
 text=a.tombstone.read_text();fault=int(re.search(r'fault addr 0x([0-9a-f]+)',text)[1],16);pointer=int(re.search(r'\bx19\s+([0-9a-f]{16})',text)[1],16);offset=int(re.search(r'\bx8\s+([0-9a-f]{16})',text)[1],16)
 assert fault==pointer+offset and offset==7 and new['function']['value']+60==int(re.search(r'#00 pc ([0-9a-f]+).*libkodi.so \(talloc_lib_init\+60\)',text)[1],16)
 report=dict(passed=True,scope='Constructor equivalence and crash-register attribution, not a startup acceptance waiver',input=old,candidate=new,
  same_constructor_instructions_with_exact_resolved_address_operands=True,fault_address=hex(fault),auxiliary_random_pointer=hex(pointer),offset=offset,
  observed='SEGV_MAPERR while reading the AT_RANDOM pointer returned by getauxval during ELF constructors, before Kodi startup and Close',
  unresolved='Why the auxiliary pointer was unmapped is not established. Native translation is present but platform-only attribution is not proven.',
  startup_failure_retained=True,apk_modified=False,physical_fold_verified=False)
 a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('input','candidate')},indent=2))
if __name__=='__main__':main()
