"""Prove narrowly reviewed D8 synthetic-name changes using normalized DEX code.

This is deliberately not a general DEX decoder. Unknown instructions, exception
handlers, annotations or source-class loss fail the preservation gate. Fields,
interfaces and callback code must match. Only the compiler-generated classes
of the two observed source owners may be mapped.
"""
import re
import struct

REVIEWED_OWNERS = (
    'Lcom/projectinfinity/kodi/InfinityExitDiagnostics$Api30$$ExternalSyntheticLambda',
    'Lcom/projectinfinity/kodi/Splash$$ExternalSyntheticLambda',
)


def require(value, message):
    if not value:
        raise ValueError(message)


def simple_code(data, offset, strings, types, fields, methods, owner):
    registers, incoming, outgoing, tries, debug, size = struct.unpack_from('<HHHHII', data, offset)
    require(tries == 0, 'Synthetic equivalence does not accept exception handlers')
    units = list(struct.unpack_from('<' + str(size) + 'H', data, offset + 16))
    single = set(range(0x0a, 0x13)) | {0x00, 0x01, 0x04, 0x07, 0x21, 0x27, 0x28}
    widths = {0x02:2, 0x03:3, 0x05:2, 0x06:3, 0x08:2, 0x09:3,
              0x13:2, 0x14:3, 0x15:2, 0x16:2, 0x17:3, 0x18:5, 0x19:2}
    references = {0x1a: (2, strings), 0x1c: (2, types), 0x1f: (2, types),
                  0x20: (2, types), 0x22: (2, types), 0x23: (2, types)}
    references.update({op:(2, fields) for op in range(0x52, 0x6e)})
    references.update({op:(3, methods) for op in list(range(0x6e,0x73)) + list(range(0x74,0x79))})
    def norm(value):
        if isinstance(value, tuple): return tuple(norm(v) for v in value)
        return '@self' if value == owner else value
    result = []; position = 0
    while position < size:
        opcode = units[position] & 255
        if opcode in references:
            width, table = references[opcode]
            require(position + width <= size, 'Truncated reference instruction')
            row = units[position:position+width]
            require(row[1] < len(table), 'Invalid DEX reference index')
            row[1] = norm(table[row[1]])
        else:
            width = 1 if opcode in single else widths.get(opcode)
            require(width is not None, 'Unreviewed synthetic instruction: ' + hex(opcode))
            require(position + width <= size, 'Truncated synthetic instruction')
            row = units[position:position+width]
        result.append(tuple(row)); position += width
    return registers, incoming, outgoing, tuple(result)


def classes(archive, selected):
    result = {}
    for name in archive.namelist():
        if not re.fullmatch(r'classes(?:\d+)?\.dex', name): continue
        data = archive.read(name)
        def u32(offset): return struct.unpack_from('<I', data, offset)[0]
        def leb(offset):
            value = shift = 0
            while True:
                b = data[offset]; offset += 1; value |= (b & 127) << shift
                if b < 128: return value, offset
                shift += 7; require(shift <= 28, 'Malformed LEB128')
        strings = []
        for i in range(u32(56)):
            _, offset = leb(u32(u32(60)+4*i))
            # Preserve exact modified-UTF8 bytes, rather than equating distinct
            # invalid Unicode literals through replacement decoding.
            strings.append(data[offset:data.index(b'\0', offset)])
        types = [strings[u32(u32(68)+4*i)].decode('ascii') for i in range(u32(64))]
        protos = []
        for i in range(u32(72)):
            offset = u32(76)+12*i; params = u32(offset+8)
            args = () if not params else tuple(types[struct.unpack_from('<H',data,params+4+2*j)[0]] for j in range(u32(params)))
            protos.append((types[u32(offset+4)], args))
        fields = []
        for i in range(u32(80)):
            owner, type_index, string = struct.unpack_from('<HHI',data,u32(84)+8*i)
            fields.append((types[owner], strings[string], types[type_index]))
        methods = []
        for i in range(u32(88)):
            owner, proto, string = struct.unpack_from('<HHI',data,u32(92)+8*i)
            methods.append((types[owner], strings[string], protos[proto]))
        for i in range(u32(96)):
            offset=u32(100)+32*i; owner=types[u32(offset)]
            if owner not in selected: continue
            parent = u32(offset+8); interfaces = u32(offset+12); annotations = u32(offset+20)
            # D8 may supply annotation metadata; compare absence/presence only
            # after rejecting annotations rather than assuming equivalence.
            require(annotations == 0, 'Annotated synthetic class requires separate review')
            interface_types = () if not interfaces else tuple(types[struct.unpack_from('<H',data,interfaces+4+2*j)[0]] for j in range(u32(interfaces)))
            def own(ref): return tuple('@self' if value == owner else value for value in ref)
            pos=u32(offset+24); counts=[]
            for _ in range(4): count,pos=leb(pos); counts.append(count)
            field_rows=[]; method_rows=[]
            for count in counts[:2]:
                index=0
                for _ in range(count):
                    delta,pos=leb(pos); flags,pos=leb(pos); index+=delta
                    field_rows.append((own(fields[index]),flags))
            for count in counts[2:]:
                index=0
                for _ in range(count):
                    delta,pos=leb(pos); flags,pos=leb(pos); code,pos=leb(pos); index+=delta
                    method_rows.append((own(methods[index]), flags,
                        None if code == 0 else simple_code(data,code,strings,types,fields,methods,owner)))
            result[owner] = (u32(offset+4), None if parent == 0xffffffff else types[parent],
                             interface_types, tuple(field_rows), tuple(method_rows))
    return result


def verified_renames(original, compiled, old_names, new_names):
    def reviewed(name): return any(name.startswith(owner) for owner in REVIEWED_OWNERS)
    missing = set(old_names) - set(new_names)
    require(all(reviewed(name) for name in missing), 'Unreviewed original class loss')
    # D8 also reassigns already-existing numeric suffixes. Verify the entire
    # callback population for each affected source owner, not merely the two
    # absent names, and require a one-to-one code/interface/field mapping.
    selected_old = {name for name in old_names if reviewed(name)}
    selected_new = {name for name in new_names if reviewed(name)}
    old_classes = classes(original, selected_old)
    new_classes = classes(compiled, selected_new)
    remaining = set(new_classes); mapped = {}
    for old in sorted(old_classes):
        prefix = next(owner for owner in REVIEWED_OWNERS if old.startswith(owner))
        candidates = sorted(new for new in remaining if new.startswith(prefix) and
                            old_classes[old] == new_classes[new])
        require(bool(candidates), 'Generated callback body/interface/field missing: ' + old)
        new = old if old in candidates else candidates[0]
        mapped[old] = new; remaining.remove(new)
    require(len(mapped) == len(selected_old), 'Original generated callback missing')
    return mapped
