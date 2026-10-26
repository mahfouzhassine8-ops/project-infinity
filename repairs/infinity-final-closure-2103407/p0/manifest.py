"""Append one private NoDisplay preference activity; preserve all old AXML nodes."""
import struct

NONE=0xffffffff
CLASS='com.projectinfinity.kodi.InfinityAskEveryTimeActivity'
ANDROID='http://schemas.android.com/apk/res/android'

def chunks(raw):
    if struct.unpack_from('<HHI',raw)!= (3,8,len(raw)):raise ValueError('Binary manifest header differs')
    at=8
    while at<len(raw):
        kind,header,size=struct.unpack_from('<HHI',raw,at)
        if header<8 or size<header or at+size>len(raw):raise ValueError('Invalid AXML chunk')
        yield at,kind,raw[at:at+size]
        at+=size
    if at!=len(raw):raise ValueError('AXML tail differs')

def length(raw,at,utf8):
    first=raw[at] if utf8 else struct.unpack_from('<H',raw,at)[0]
    flag=128 if utf8 else 32768;step=1 if utf8 else 2
    if first&flag:
        second=raw[at+step] if utf8 else struct.unpack_from('<H',raw,at+step)[0]
        return ((first&(flag-1))<<(7 if utf8 else 15))|second,at+2*step
    return first,at+step

def string_pool(raw):
    kind,header,size=struct.unpack_from('<HHI',raw)
    if kind!=1 or header!=28 or size!=len(raw):raise ValueError('Standard string pool required')
    count,style_count,flags,start,style_start=struct.unpack_from('<5I',raw,8)
    utf8=bool(flags&256);strings=[]
    for i in range(count):
        at=start+struct.unpack_from('<I',raw,header+i*4)[0]
        size,at=length(raw,at,utf8)
        if utf8:size,at=length(raw,at,True)
        else:size*=2
        strings.append(raw[at:at+size].decode('utf-8' if utf8 else 'utf-16-le'))
    return strings

def append_strings(raw,additions):
    count,styles,flags,start,style_start=struct.unpack_from('<5I',raw,8)
    old=string_pool(raw)
    if any(s in old for s in additions):raise ValueError('New manifest identity already exists')
    body=bytearray(raw[start:style_start or len(raw)])
    offsets=[];utf8=bool(flags&256)
    for value in additions:
        encoded=value.encode('utf-8' if utf8 else 'utf-16-le')
        characters=len(value.encode('utf-16-le'))//2
        if characters>=128 or utf8 and len(encoded)>=128:raise ValueError('Short literal required')
        offsets.append(len(body))
        body.extend(bytes((characters,len(encoded)))+encoded+b'\0' if utf8 else struct.pack('<H',characters)+encoded+b'\0\0')
    body.extend(b'\0'*((-len(body))%4))
    new_start=start+4*len(additions)
    new_style_start=new_start+len(body) if style_start else 0
    rest=raw[style_start:] if style_start else b''
    header=struct.pack('<HHI5I',1,28,new_start+len(body)+len(rest),count+len(additions),styles,
                       flags&~1,new_start,new_style_start)
    old_offsets=raw[28:28+4*count]
    style_offsets=raw[28+4*count:start]
    result=header+old_offsets+b''.join(struct.pack('<I',n) for n in offsets)+style_offsets+body+rest
    if string_pool(result)!=old+additions:raise ValueError('Original string/index changed')
    return result

def start(name,attributes,strings):
    attrs=[]
    for key,kind,value in attributes:
        attrs.append(struct.pack('<IIIHBBI',strings.index(ANDROID),strings.index(key),
            strings.index(value) if kind==3 else NONE,8,0,kind,strings.index(value) if kind==3 else value))
    return struct.pack('<HHIII',0x102,16,36+20*len(attrs),NONE,NONE)+\
        struct.pack('<II6H',NONE,strings.index(name),20,20,len(attrs),0,0,0)+b''.join(attrs)

def end(name,strings):
    return struct.pack('<HHIIIII',0x103,16,24,NONE,NONE,NONE,strings.index(name))

def patch(raw):
    parts=list(chunks(raw));pool=next(p for _,kind,p in parts if kind==1)
    old_strings=string_pool(pool)
    required=('activity','application','name','theme','exported','noHistory','excludeFromRecents',ANDROID)
    if any(s not in old_strings for s in required):raise ValueError('Original AXML attribute identities missing')
    revised_pool=append_strings(pool,[CLASS]);strings=old_strings+[CLASS]
    # android.R.style.Theme_NoDisplay, read from the pinned Android34 signature jar.
    attrs=[('theme',1,0x01030055),('name',3,CLASS),('exported',0x12,0),
           ('excludeFromRecents',0x12,1),('noHistory',0x12,1)]
    activity=start('activity',attrs,strings)+end('activity',strings)
    output=[];version_changed=False;inserted=False
    for _,kind,part in parts:
        if kind==1:output.append(revised_pool);continue
        if kind==0x102:
            name=struct.unpack_from('<I',part,20)[0]
            if strings[name]=='manifest':
                mutable=bytearray(part);first,step,count=struct.unpack_from('<3H',part,24)
                for i in range(count):
                    at=16+first+i*step;key=struct.unpack_from('<I',part,at+4)[0]
                    if strings[key]=='versionCode':
                        if part[at+15]!=0x10 or struct.unpack_from('<I',part,at+16)[0]!=2103419:
                            raise ValueError('Exact419 typed version required')
                        struct.pack_into('<I',mutable,at+16,2103420);version_changed=True
                part=bytes(mutable)
        if kind==0x103 and strings[struct.unpack_from('<I',part,20)[0]]=='application':
            if inserted:raise ValueError('Duplicate application')
            output.append(activity);inserted=True
        output.append(part)
    if not version_changed or not inserted:raise ValueError('Manifest scope incomplete')
    payload=b''.join(output);result=struct.pack('<HHI',3,8,8+len(payload))+payload
    list(chunks(result))
    return result

def verify_preference_activity(raw):
    parts=list(chunks(raw));strings=string_pool(next(p for _,k,p in parts if k==1));matches=[]
    for _,kind,part in parts:
        if kind!=0x102 or strings[struct.unpack_from('<I',part,20)[0]]!='activity':continue
        first,step,count=struct.unpack_from('<3H',part,24);attributes={}
        for i in range(count):
            at=16+first+i*step;ns,key,unused=struct.unpack_from('<3I',part,at)
            typ=part[at+15];value=struct.unpack_from('<I',part,at+16)[0]
            if ns==NONE or strings[ns]!=ANDROID:raise ValueError('Activity attribute namespace differs')
            attributes[strings[key]]=(typ,strings[value] if typ==3 else value)
        if attributes.get('name')==(3,CLASS):matches.append(attributes)
    expected={'theme':(1,0x01030055),'name':(3,CLASS),'exported':(0x12,0),
              'excludeFromRecents':(0x12,1),'noHistory':(0x12,1)}
    if matches!=[expected]:raise ValueError('Exactly one private NoDisplay preference activity required')
    return expected
