"""Small read-only binary AndroidManifest package reader (no resource rewriting)."""
from __future__ import annotations
import struct
import xml.etree.ElementTree as ET

def package_name(data: bytes) -> str:
    if data.lstrip().startswith(b'<'):
        return ET.fromstring(data).attrib.get('package','')
    def u16(p):return struct.unpack_from('<H',data,p)[0]
    def u32(p):return struct.unpack_from('<I',data,p)[0]
    if len(data)<8 or u16(0)!=3:raise ValueError('Not an Android XML document')
    pos=u16(2); strings=[]
    while pos+8<=len(data):
        kind,head,size=struct.unpack_from('<HHI',data,pos)
        if size<head or size<8 or pos+size>len(data):raise ValueError('Malformed XML chunk')
        if kind==1:
            count=u32(pos+8); flags=u32(pos+16); start=pos+u32(pos+20)
            strings=[]
            for i in range(count):
                p=start+u32(pos+head+4*i)
                if flags & 0x100:
                    def length(p):
                        n=data[p];p+=1
                        if n & 0x80:n=((n & 0x7f)<<8)|data[p];p+=1
                        return n,p
                    _,p=length(p);n,p=length(p)
                    strings.append(data[p:p+n].decode('utf-8'))
                else:
                    n=u16(p);p+=2
                    if n & 0x8000:n=((n & 0x7fff)<<16)|u16(p);p+=2
                    strings.append(data[p:p+2*n].decode('utf-16le'))
        elif kind==0x102:
            ext=pos+head
            name=strings[u32(ext+4)]
            if name=='manifest':
                attr_start=u16(ext+8);attr_size=u16(ext+10);count=u16(ext+12)
                for i in range(count):
                    at=ext+attr_start+i*attr_size
                    if strings[u32(at+4)]=='package':
                        raw=u32(at+8)
                        if raw != 0xffffffff:return strings[raw]
                        if data[at+15]==3:return strings[u32(at+16)]
                        raise ValueError('Unexpected typed package value')
        pos+=size
    raise ValueError('Package attribute not found')
