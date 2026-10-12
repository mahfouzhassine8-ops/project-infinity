"""Patch only the two version attributes in the exact parent binary Android manifest."""
import struct

PARENT_CODE = 2103375
CODE = 2103376
PARENT_NAME = '1.0.9-File-Preview-Native-RC1'
NAME = '1.0.9-File-Preview-Repair-RC1'


def length(data, position, utf8):
    if utf8:
        first = data[position]
        return (((first & 0x7f) << 8) | data[position + 1], position + 2) if first & 0x80 else (first, position + 1)
    first = struct.unpack_from('<H', data, position)[0]
    return (((first & 0x7fff) << 16) | struct.unpack_from('<H', data, position + 2)[0], position + 4) if first & 0x8000 else (first, position + 2)


def patch(original):
    assert len(PARENT_NAME) == len(NAME)
    assert struct.unpack_from('<H', original, 0)[0] == 3
    data = bytearray(original)
    position = struct.unpack_from('<H', data, 2)[0]
    strings = []
    spans = []
    changed_code = False
    changed_name = False
    edits = []
    while position < len(data):
        kind, header, size = struct.unpack_from('<HHI', data, position)
        assert header >= 8 and size >= header and position + size <= len(data)
        if kind == 1:
            count, _, flags, start, _ = struct.unpack_from('<5I', data, position + 8)
            utf8 = bool(flags & 0x100)
            for index in range(count):
                offset = struct.unpack_from('<I', data, position + header + index * 4)[0]
                cursor = position + start + offset
                characters, cursor = length(data, cursor, utf8)
                if utf8:
                    size_string, cursor = length(data, cursor, True)
                    encoding = 'utf-8'
                else:
                    size_string = characters * 2
                    encoding = 'utf-16-le'
                strings.append(bytes(data[cursor:cursor + size_string]).decode(encoding))
                spans.append((cursor, size_string, encoding))
        elif kind == 0x102:
            name = struct.unpack_from('<I', data, position + 20)[0]
            if strings[name] == 'manifest':
                attribute_start, attribute_size, count = struct.unpack_from('<3H', data, position + 24)
                for index in range(count):
                    offset = position + 16 + attribute_start + index * attribute_size
                    namespace, key, raw = struct.unpack_from('<3I', data, offset)
                    value_type = data[offset + 15]
                    value = struct.unpack_from('<I', data, offset + 16)[0]
                    if namespace == 0xffffffff or strings[namespace] != 'http://schemas.android.com/apk/res/android':
                        continue
                    if strings[key] == 'versionCode':
                        assert not changed_code and value_type == 0x10 and value == PARENT_CODE
                        struct.pack_into('<I', data, offset + 16, CODE)
                        edits.append({'field': 'versionCode', 'offset': offset + 16, 'bytes': 4})
                        if raw != 0xffffffff:
                            assert strings[raw] == str(PARENT_CODE)
                            start_string, amount, encoding = spans[raw]
                            replacement = str(CODE).encode(encoding)
                            assert len(replacement) == amount
                            data[start_string:start_string + amount] = replacement
                        changed_code = True
                    elif strings[key] == 'versionName':
                        assert not changed_name and value_type == 3 and strings[value] == PARENT_NAME
                        start_string, amount, encoding = spans[value]
                        replacement = NAME.encode(encoding)
                        assert len(replacement) == amount
                        data[start_string:start_string + amount] = replacement
                        edits.append({'field': 'versionName', 'offset': start_string, 'bytes': amount})
                        changed_name = True
        position += size
    assert changed_code and changed_name and position == len(data) and len(data) == len(original)
    return bytes(data), edits
