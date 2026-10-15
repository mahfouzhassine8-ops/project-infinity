"""Existing Infinity APK verification utilities, retained from the 2103302 lineage."""
from pathlib import Path
import hashlib,re,struct,subprocess,zipfile
DEX = re.compile(r'classes\d*\.dex$')
SIGNATURE = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$', re.I)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)

def run(*args, cwd=None, env=None, output=None):
    if output is not None:
        result = subprocess.run([str(x) for x in args], cwd=cwd, env=env,
                                check=True, stdout=subprocess.PIPE, text=True)
        Path(output).write_text(result.stdout)
        return result.stdout
    subprocess.run([str(x) for x in args], cwd=cwd, env=env, check=True)

def configured(path: Path, values: dict[str, str]) -> str:
    text = path.read_text()
    for key, value in values.items():
        text = text.replace('@' + key + '@', value)
    require(not re.search(r'@[A-Z][A-Z_0-9]*@', text), 'Unresolved CMake placeholder: ' + str(path))
    return text

def resource_ids(aapt2: Path, apk: Path, output: Path) -> dict[str, str]:
    text = run(aapt2, 'dump', 'resources', apk, output=output)
    ids = {}
    for rid, name in re.findall(r'^\s*resource\s+(0x7f[0-9a-fA-F]{6})\s+([^\s]+/[^\s]+)', text, re.M):
        name = name.split(':', 1)[-1]
        require(name not in ids or ids[name] == rid, 'Ambiguous resource: ' + name)
        ids[name] = rid.lower()
    require(len(ids) > 20, 'Resource map empty or unrecognized; refusing a mixed resource/DEX APK')
    return ids

def dex_contract(archive: zipfile.ZipFile):
    """Read native declarations directly from DEX class_data, including descriptors."""
    native, classes = set(), set()
    for name in archive.namelist():
        if not DEX.fullmatch(name):
            continue
        data = archive.read(name)
        require(data[:4] == b'dex\n', 'Not a standard DEX file: ' + name)
        def u32(off):
            return struct.unpack_from('<I', data, off)[0]
        def leb(off):
            val, shift = 0, 0
            while True:
                b = data[off]; off += 1
                val |= (b & 127) << shift
                if b < 128: return val, off
                shift += 7
                require(shift <= 28, 'Invalid DEX LEB128')
        count, off = u32(56), u32(60)
        strings = []
        for i in range(count):
            _, s = leb(u32(off + 4*i))
            strings.append(data[s:data.index(b'\0', s)].decode('utf-8', errors='replace'))
        count, off = u32(64), u32(68)
        types = [strings[u32(off + 4*i)] for i in range(count)]
        count, off = u32(72), u32(76)
        protos = []
        for i in range(count):
            ret, poff = u32(off+12*i+4), u32(off+12*i+8)
            params = [] if not poff else [types[struct.unpack_from('<H',data,poff+4+2*j)[0]] for j in range(u32(poff))]
            protos.append('(' + ''.join(params) + ')' + types[ret])
        count, off = u32(88), u32(92)
        methods = []
        for i in range(count):
            owner, proto, text = struct.unpack_from('<HHI', data, off+8*i)
            methods.append((types[owner], strings[text], protos[proto]))
        count, off = u32(96), u32(100)
        for i in range(count):
            owner = types[u32(off+32*i)]
            classes.add(owner)
            pos = u32(off+32*i+24)
            if not pos: continue
            sf,pos=leb(pos); inf,pos=leb(pos); direct,pos=leb(pos); virtual,pos=leb(pos)
            for _ in range(sf+inf):
                _,pos=leb(pos); _,pos=leb(pos)
            for size in (direct,virtual):
                index=0
                for _ in range(size):
                    delta,pos=leb(pos); flags,pos=leb(pos); _,pos=leb(pos)
                    index += delta
                    if flags & 0x100:
                        native.add(methods[index])
    require(native, 'No JNI native declarations found')
    return native, classes

def manifest_tree(text: str):
    root, stack = None, []
    for line in text.splitlines():
        stripped=line.lstrip(); indent=len(line)-len(stripped)
        if stripped.startswith('E: '):
            node={'tag':stripped.split()[1], 'attrs':{}, 'children':[]}
            while stack and stack[-1][0]>=indent: stack.pop()
            if stack: stack[-1][1]['children'].append(node)
            else:
                require(root is None,'Multiple manifest roots'); root=node
            stack.append((indent,node))
        elif stripped.startswith('A: '):
            key,value=stripped[3:].split('=',1)
            require(bool(stack),'Manifest attribute outside element')
            stack[-1][1]['attrs'][key.split('(')[0]]=value
    require(root is not None,'Empty compiled manifest'); return root

def verify_manifest_pair(original: str, compiled: str):
    old,new=manifest_tree(original),manifest_tree(compiled)
    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'):
            tree['attrs'].pop(key,None)
    require(old==new,'Compiled manifest drift from exact 2103302 base outside version identity')
