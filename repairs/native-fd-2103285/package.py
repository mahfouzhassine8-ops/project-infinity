#!/usr/bin/env python3
"""Package the passed native engine onto the exact installed 2103284 APK.
No Java, resource, skin, database or provider changes. Identity-only AXML edits
are fixed-width, schema-validated and rejected unless exactly reversible.
"""
from pathlib import Path
import argparse, copy, hashlib, json, os, re, struct, subprocess, zipfile
PARENT_SHA = '0986aedd4d5375b125d02ba5b6aec29c6f9788722eb2ee13d3e8d588eeaa3cd9'
OLD_NATIVE = 'c7976ce0adb45b9264f2092a27111be4e05bde4220be2b26b1ea0e2cc74f1e2d'
NEW_NATIVE = 'f6eb05f091bfe7a624105a0a83744a292e229b385d39c1b6a23f8bf954a2522a'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
OLD_NAME = '1.0.9-Ambient-Surface-Repair-RC1'
NEW_NAME = '1.0.9-Native-FD-Crash-Repair-RC1'
OLD_CODE, NEW_CODE = 2103284, 2103285
NATIVE = 'lib/arm64-v8a/libkodi.so'
SIGN = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$', re.I)
DIGEST = lambda b: hashlib.sha256(b).hexdigest()

def require(value, message):
    if not value: raise RuntimeError(message)

def identity_only_manifest(original):
    data = bytearray(original)
    def u16(o): return struct.unpack_from('<H', data, o)[0]
    def u32(o): return struct.unpack_from('<I', data, o)[0]
    require((u16(0),u16(2),u32(4)) == (3,8,len(data)), 'Unexpected AXML header')
    strings, string_ranges, roots, name_users = [], [], [], []
    pos = 8
    while pos < len(data):
        typ, header, size = struct.unpack_from('<HHI',data,pos)
        require(size >= header >= 8 and pos+size <= len(data), 'AXML chunk bounds')
        if typ == 1:
            require(not strings and header == 28, 'Unexpected string pool')
            count, styles, flags, start, style_start = struct.unpack_from('<IIIII',data,pos+8)
            require(styles == 0 and flags == 0 and style_start == 0, 'Expected unsorted UTF16 string pool')
            require(start >= header+4*count, 'Invalid string offsets')
            for i in range(count):
                off = pos + start + u32(pos+header+4*i)
                length = u16(off)
                require(length < 32768, 'Unsupported extended string length')
                off += 2
                end = off + 2*length
                require(end+2 <= pos+size and data[end:end+2] == b'\x00\x00', 'String bounds')
                strings.append(bytes(data[off:end]).decode('utf-16-le'))
                string_ranges.append((off,end))
        elif typ == 0x102:
            require(header == 16 and strings, 'Unexpected XML node')
            ext = pos+header
            name = u32(ext+4)
            attr_start, attr_size, count = struct.unpack_from('<HHH',data,ext+8)
            require(attr_size == 20 and ext+attr_start+count*attr_size <= pos+size, 'Attribute bounds')
            attrs = []
            for i in range(count):
                off = ext+attr_start+20*i
                ns,key,raw = struct.unpack_from('<III',data,off)
                require(u16(off+12)==8 and data[off+14]==0, 'Unexpected Res_value')
                kind, value = data[off+15],u32(off+16)
                attrs.append((ns,key,raw,kind,value,off))
                if kind == 3 and strings[value] == OLD_NAME: name_users.append(off)
            if strings[name]=='manifest': roots.append(attrs)
        pos += size
    require(pos==len(data) and len(roots)==1, 'Expected one manifest root')
    root = {strings[a[1]]:a for a in roots[0]}
    ns,key,raw,kind,value,off = root['versionCode']
    require(strings[ns]=='http://schemas.android.com/apk/res/android' and raw==0xffffffff and kind==0x10 and value==OLD_CODE, 'Unexpected original versionCode')
    code_offset=off+16
    struct.pack_into('<I',data,code_offset,NEW_CODE)
    ns,key,raw,kind,value,off = root['versionName']
    require(strings[ns]=='http://schemas.android.com/apk/res/android' and kind==3 and strings[value]==OLD_NAME, 'Unexpected original versionName')
    require(raw in (value,0xffffffff) and name_users==[off] and strings.count(OLD_NAME)==1, 'Version string is not exclusive to manifest identity')
    lo,hi = string_ranges[value]
    encoded = NEW_NAME.encode('utf-16-le')
    require(len(encoded)==hi-lo, 'Identity update cannot resize the string pool')
    data[lo:hi]=encoded
    reverse=bytearray(data)
    reverse[lo:hi]=OLD_NAME.encode('utf-16-le')
    struct.pack_into('<I',reverse,code_offset,OLD_CODE)
    require(bytes(reverse)==original, 'Manifest changed beyond two version attributes')
    return bytes(data), {'version_code_value_offset':code_offset, 'version_name_string_range':[lo,hi], 'other_manifest_bytes_identical':True}

def command(args, report=None):
    out=subprocess.check_output([str(x) for x in args],text=True)
    if report: Path(report).write_text(out)
    return out

def native_contract(parent, candidate, out):
    a=out/'parent-libkodi.so'; a.write_bytes(parent)
    try:
        def dynamic(path):
            text=command(['readelf','-dW',path])
            return sorted(l.strip().split(')',1)[1] for l in text.splitlines() if '(NEEDED)' in l or '(SONAME)' in l)
        require(dynamic(a)==dynamic(candidate),'Native dependency or SONAME drift')
        def symbols(path):
            text=command(['readelf','--dyn-syms','--wide',path])
            rows=[l.split() for l in text.splitlines() if len(l.split())>=8 and l.split()[0].endswith(':')]
            return ({r[7].split('@')[0] for r in rows if r[6]=='UND'}, {r[7].split('@')[0] for r in rows if r[6]!='UND'})
        oldi,olde=symbols(a); newi,newe=symbols(candidate)
        require(newi-oldi=={'ppoll'} and not oldi-newi,'Unexpected import changes')
        missing=sorted(olde-newe)
        require(all(s.startswith(('_ZN3fmt','_ZN4CLog')) for s in missing),'Native exported runtime contract lost')
        require({s for s in olde if s.startswith(('Java_','JNI_','ANativeActivity'))}=={s for s in newe if s.startswith(('Java_','JNI_','ANativeActivity'))},'JNI entrypoint drift')
        return {'dependencies_identical':True,'only_added_import':'ppoll','removed_exports_logging_templates_only':missing}
    finally: a.unlink(missing_ok=True)

def prepare(parent, native, out):
    require(DIGEST(parent.read_bytes())==PARENT_SHA,'Wrong parent APK')
    require(DIGEST(native.read_bytes())==NEW_NATIVE,'Wrong successful native engine')
    require(b'INFINITY_FD_POLL_V1' in native.read_bytes(),'Missing FD repair marker')
    engine_proof=json.loads((native.parent/'engine-proof.json').read_text())
    require(engine_proof['native_engine_sha256']==NEW_NATIVE and engine_proof['native_fd_source']['verified'],'Missing passed source proof')
    unsigned=out/'unsigned.apk'
    with zipfile.ZipFile(parent) as src, zipfile.ZipFile(unsigned,'w') as dst:
        require(len(set(src.namelist()))==len(src.namelist()) and src.testzip() is None,'Invalid parent archive')
        require(DIGEST(src.read(NATIVE))==OLD_NATIVE,'Parent engine mismatch')
        manifest,proof=identity_only_manifest(src.read('AndroidManifest.xml'))
        for info in src.infolist():
            if SIGN.fullmatch(info.filename): continue
            payload=(manifest if info.filename=='AndroidManifest.xml' else native.read_bytes() if info.filename==NATIVE else src.read(info.filename))
            dst.writestr(copy.copy(info),payload)
        elf=native_contract(src.read(NATIVE),native,out)
    (out/'packaging-input-proof.json').write_text(json.dumps({'parent_sha256':PARENT_SHA,'native_sha256':NEW_NATIVE,'identity':proof,'elf_contract':elf,'native_build_run':36925544128,'native_source_commit':'cb5cd7d2da3290a8a4e01a184efe9534aaf8e548'},indent=2)+'\n')
    print('PASS: prepared version-only manifest + exact passed native engine; other payload untouched')

def verify(parent, final, out):
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    for path,label in [(parent,'parent'),(final,'candidate')]:
        cert=command([bt/'apksigner','verify','--verbose','--print-certs',path],out/(label+'-signer.txt'))
        require('Signer #1 certificate SHA-256 digest: '+CERT in cert,'Wrong permanent signer')
    command([bt/'zipalign','-c','-p','4',final],out/'alignment.txt')
    badge=command([bt/'aapt','dump','badging',final],out/'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{NEW_CODE}' versionName='{NEW_NAME}'" in badge,'Wrong candidate identity')
    require("sdkVersion:'21'" in badge and "targetSdkVersion:'35'" in badge and 'application-debuggable' not in badge,'SDK or debuggability drift')
    require(len(re.findall('^launchable-activity:',badge,re.M))==1,'Wrong launcher count')
    old=command([bt/'aapt','dump','xmltree',parent,'AndroidManifest.xml'],out/'parent-manifest.txt')
    new=command([bt/'aapt','dump','xmltree',final,'AndroidManifest.xml'],out/'candidate-manifest.txt')
    def normalize(t): return '\n'.join(l for l in t.splitlines() if not re.match(r'\s*A: android:version(?:Code|Name)\(',l))
    require(normalize(old)==normalize(new),'Compiled manifest drift beyond version identity')
    with zipfile.ZipFile(parent) as a,zipfile.ZipFile(final) as b:
        require(b.testzip() is None and len(set(b.namelist()))==len(b.namelist()),'Invalid final ZIP')
        an={n for n in a.namelist() if not SIGN.fullmatch(n)}
        bn={n for n in b.namelist() if not SIGN.fullmatch(n)}
        require(an==bn,'APK member inventory drift')
        protected=an-{'AndroidManifest.xml',NATIVE}
        for n in protected: require(a.read(n)==b.read(n),'Preservation failure: '+n)
        require(DIGEST(b.read(NATIVE))==NEW_NATIVE,'Final native engine mismatch')
        require(b.read('AndroidManifest.xml')==identity_only_manifest(a.read('AndroidManifest.xml'))[0],'Unexpected final manifest')
        inventory={n:DIGEST(b.read(n)) for n in sorted(protected)}
    report={'schema':1,'apk':final.name,'apk_sha256':DIGEST(final.read_bytes()),'version_code':NEW_CODE,'version_name':NEW_NAME,'parent_apk_sha256':PARENT_SHA,'parent_version_code':OLD_CODE,'native_engine_sha256':NEW_NATIVE,'signer_sha256':CERT,'changed_payload_entries':['AndroidManifest.xml',NATIVE],'protected_payload_count':len(protected),'dex_byte_identical':True,'android_resources_byte_identical':True,'assets_byte_identical':True,'all_other_native_libraries_byte_identical':True,'no_skin_installation_or_cleanup':True,'no_user_data_migration_or_wipe':True,'native_build_run':36925544128,'physical_device_verified':False,'locked':False,'runtime_acceptance':'PENDING; signing/integrity is not Fold acceptance','remaining_limitations':['Exported crash trace does not prove descriptor leak owner or unique crashing caller.','External native dependencies, including shairplay, remain unchanged; this is a core-Kodi/Neptune targeted candidate.','Installed skin layout and broader audit/ambient behavior are not repaired by this APK.']}
    (out/'preserved-entry-sha256.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (out/'RELEASE-REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'SHA256SUMS.txt').write_text(report['apk_sha256']+'  '+final.name+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['prepare','verify']);ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--native',type=Path);ap.add_argument('--candidate',type=Path);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    if args.mode=='prepare': prepare(args.parent,args.native,args.out)
    else: verify(args.parent,args.candidate,args.out)
