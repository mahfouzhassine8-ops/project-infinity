#!/usr/bin/env python3
"""Exact launcher-only resource transformation; no aapt rebuild of other owners.

The two existing manifest resource IDs remain unchanged. Existing dark artwork
is never rewritten. Day icons are new paths; night configs reference the original
paths. Existing API33 monochrome remains under launcher/Material You control.

This is deliberately limited to one SHA-pinned original table. It is not a
general resource editor and rejects an unrecognized resource layout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from collections.abc import Mapping
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
TABLE = "resources.arsc"
TABLE_SHA256 = "1b8c1788a5a86242635277f063ebdce6b82ed12eafe3cfdf331b902c8eb7e616"
ICON_IDS = frozenset((0x7F080000, 0x7F080001))
MONO_ID = 0x7F040006
MONO_PATH = "res/za.png"
FOREGROUND_PATH = "res/n4.png"
DENSITIES = {160: ("mdpi", 48), 240: ("hdpi", 72), 320: ("xhdpi", 96),
             480: ("xxhdpi", 144), 640: ("xxxhdpi", 192)}
LEGACY_PATHS = {160: ("res/9w.png", "res/zR.png"), 240: ("res/yn.png", "res/8c.png"),
                320: ("res/FS.png", "res/wb.png"), 480: ("res/RJ.png", "res/fO.png"),
                640: ("res/o-.png", "res/Gc.png")}
ADAPTIVE_PATHS = {26: ("res/BW.xml", "res/0K.xml"), 33: ("res/IG.xml", "res/6H.xml")}
NEW_PATHS = frozenset(
    ["res/infinity_launcher_light_" + d[0] + ".png" for d in DENSITIES.values()] +
    ["res/infinity_launcher_light_v26.xml", "res/infinity_launcher_light_v33.xml"])
BASELINE_SHA256 = {
    TABLE: TABLE_SHA256,
    "res/HA.png": "b974f18e6449a830e26e68f783464721cec3c02983b66dc9ed894de4fe93319f",
    FOREGROUND_PATH: "9348747bebff15426671ac156ff2824a4de2b7736d07e68c36f014ab3a73c788",
    MONO_PATH: "7a2c6f9de711c859244eee484d627f7d92c0ee7f3dee8bc1dba55d9b92fe89e2",
    "res/zp.png": "c692b219dbbe4bd711f7922757d5d294574775c964b94b9595b291ebc3e429f8",
}
for _density, _paths in LEGACY_PATHS.items():
    _h = {160: "e6029cd5772e320359c86499ba2033598e6cc79bdb94cf2c3a063f72a6a3bb16",
          240: "de9a26f502d1eed776837c02ddaa988484f00c6970f9070a7838bba159df92c3",
          320: "84c03ad5d79da937dcef2f93ccea5a6012d6f26e04bc9c7a5274827a878ded22",
          480: "72e7286d8931746d817424f429c626a265184add24d829f62cec70eabbd0a7e5",
          640: "296c75e912271576af5014d5a14120bff1295bebf4c87791f676888aef226506"}[_density]
    BASELINE_SHA256.update({p: _h for p in _paths})
for _sdk, _paths in ADAPTIVE_PATHS.items():
    _h = {26: "72178fe886f9ccd3eaa4fa161ab7222b4a7afaa2112ed249375821f463966ec9",
          33: "f0af3fdd93c92162f7ead31dd5747bf4fb2220e1bb2a6f6fd4f1a5f3813359e4"}[_sdk]
    BASELINE_SHA256.update({p: _h for p in _paths})


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def chunks(data, start, end):
    while start < end:
        require(start + 8 <= end, "Truncated chunk")
        kind, head, size = struct.unpack_from("<HHI", data, start)
        require(8 <= head <= size and start + size <= end, "Invalid chunk extent")
        yield start, kind, head, size
        start += size
    require(start == end, "Unaligned chunk end")


def _length(data, pos, utf8):
    if utf8:
        n = data[pos]; pos += 1
        if n & 0x80:
            n = ((n & 0x7F) << 8) | data[pos]; pos += 1
    else:
        n = struct.unpack_from("<H", data, pos)[0]; pos += 2
        if n & 0x8000:
            n = ((n & 0x7FFF) << 16) | struct.unpack_from("<H", data, pos)[0]; pos += 2
    return n, pos


def string_pool(data, pos):
    kind, head, size = struct.unpack_from("<HHI", data, pos)
    require(kind == 1 and head == 28, "Unexpected string pool header")
    count, style_count, flags, start, style_start = struct.unpack_from("<5I", data, pos + 8)
    result = []
    for i in range(count):
        p = pos + start + struct.unpack_from("<I", data, pos + head + 4*i)[0]
        if flags & 0x100:
            _, p = _length(data, p, True); n, p = _length(data, p, True)
            result.append(data[p:p+n].decode("utf-8"))
        else:
            n, p = _length(data, p, False)
            result.append(data[p:p+2*n].decode("utf-16le"))
    return result


def _utf8_length(n):
    require(n < 0x8000, "Oversized string")
    return bytes([n]) if n < 0x80 else bytes([(n >> 8) | 0x80, n & 0xFF])


def make_pool(strings):
    body = bytearray(); offsets = []
    for text in strings:
        b = text.encode("utf-8"); offsets.append(len(body))
        body += _utf8_length(len(text.encode("utf-16le"))//2) + _utf8_length(len(b)) + b + b"\0"
    body += b"\0" * (-len(body) % 4)
    start = 28 + len(offsets)*4
    return struct.pack("<HHI5I", 1, 28, start+len(body), len(offsets), 0, 0x100, start, 0) + struct.pack("<"+"I"*len(offsets), *offsets) + body


def append_pool(data, additions):
    kind, head, size = struct.unpack_from("<HHI", data)
    count, styles, flags, start, style_start = struct.unpack_from("<5I", data, 8)
    require(kind == 1 and head == 28 and styles == 0 and style_start == 0 and not flags & 1,
            "Unsupported global pool; refuse regeneration")
    old = string_pool(data, 0)
    require(not set(additions) & set(old), "Icon path already present")
    body = bytearray(data[start:size]); offsets = list(struct.unpack_from("<"+"I"*count, data, head))
    for value in additions:
        b = value.encode(); offsets.append(len(body))
        body += _utf8_length(len(value)) + _utf8_length(len(b)) + b + b"\0"
    body += b"\0" * (-len(body) % 4)
    new_start = head + len(offsets)*4
    out = struct.pack("<HHI5I", 1, head, new_start+len(body), len(offsets), 0, flags, new_start, 0)
    out += struct.pack("<"+"I"*len(offsets), *offsets) + body
    require(string_pool(out, 0) == old + list(additions), "Pool append changed existing strings")
    return out


def png_rgba(data):
    require(data.startswith(b"\x89PNG\r\n\x1a\n"), "Not PNG")
    pos = 8; packed = bytearray(); width = height = None
    while pos < len(data):
        size = struct.unpack_from(">I", data, pos)[0]
        kind = data[pos+4:pos+8]; body = data[pos+8:pos+8+size]
        require(zlib.crc32(kind+body) & 0xFFFFFFFF == struct.unpack_from(">I", data, pos+8+size)[0], "PNG CRC")
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", body)
            require((depth, color, compression, filtering, interlace) == (8, 6, 0, 0, 0), "Only pinned RGBA8 originals supported")
        elif kind == b"IDAT": packed += body
        elif kind == b"IEND": break
        pos += 12 + size
    require(width and height, "PNG dimensions")
    raw = zlib.decompress(packed); stride = width*4
    require(len(raw) == height*(stride+1), "PNG scanline length")
    pixels = bytearray(); prior = bytearray(stride)
    for y in range(height):
        f = raw[y*(stride+1)]; line = bytearray(raw[y*(stride+1)+1:(y+1)*(stride+1)])
        require(f <= 4, "PNG filter")
        for x in range(stride):
            a = line[x-4] if x >= 4 else 0; b = prior[x]; c = prior[x-4] if x >= 4 else 0
            if f == 1: p = a
            elif f == 2: p = b
            elif f == 3: p = (a+b)//2
            elif f == 4:
                q = a+b-c; pa, pb, pc = abs(q-a), abs(q-b), abs(q-c)
                p = a if pa <= pb and pa <= pc else b if pb <= pc else c
            else: p = 0
            line[x] = (line[x]+p) & 255
        pixels += line; prior = line
    return width, height, bytes(pixels)


def _png_chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind+data) & 0xFFFFFFFF)


def png_encode(width, height, rgba):
    """Version-independent PNG: uncompressed DEFLATE blocks, no metadata/time."""
    require(len(rgba) == width*height*4, "Invalid pixels")
    scan = b"".join(b"\0" + rgba[y*width*4:(y+1)*width*4] for y in range(height))
    packed = bytearray(b"\x78\x01")
    for start in range(0, len(scan), 65535):
        block = scan[start:start+65535]; final = start+len(block) == len(scan)
        packed += bytes([int(final)]) + struct.pack("<HH", len(block), len(block) ^ 0xFFFF) + block
    packed += struct.pack(">I", zlib.adler32(scan) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + _png_chunk(b"IDAT", packed) + _png_chunk(b"IEND", b"")


def light_legacy(original, monochrome):
    width, height, original_rgba = png_rgba(original)
    mw, mh, mask = png_rgba(monochrome)
    require(mw == mh == 432 and width == height, "Unexpected icon geometry")
    # Adaptive layers are 108 units; launcher visible viewport is centered72.
    # Reuse this exact existing mask, without detecting/retracing cyan pixels.
    inset = 72; crop = 288; out = bytearray()
    den = 2*width
    for y in range(height):
        yy = (2*y+1)*crop-width; y0 = max(0, yy//den); fy = max(0, yy-y0*den); y1 = min(crop-1, y0+1)
        for x in range(width):
            xx = (2*x+1)*crop-width; x0 = max(0, xx//den); fx = max(0, xx-x0*den); x1 = min(crop-1, x0+1)
            a00 = mask[((inset+y0)*mw+inset+x0)*4+3]; a10 = mask[((inset+y0)*mw+inset+x1)*4+3]
            a01 = mask[((inset+y1)*mw+inset+x0)*4+3]; a11 = mask[((inset+y1)*mw+inset+x1)*4+3]
            alpha = (a00*(den-fx)*(den-fy)+a10*fx*(den-fy)+a01*(den-fx)*fy+a11*fx*fy+den*den//2)//(den*den)
            gray = 255-alpha
            out += bytes((gray, gray, gray, original_rgba[(y*width+x)*4+3]))
    return png_encode(width, height, out)


def adaptive_xml(sdk):
    # Framework attribute IDs are from the pinned android34 SDK android.R$attr.
    # Inline ColorDrawable/BitmapDrawable require no new app resource IDs.
    strings = ["drawable", "src", "tint", "android", "http://schemas.android.com/apk/res/android",
               "adaptive-icon", "background", "foreground", "bitmap", "monochrome"]
    ix = {s: i for i, s in enumerate(strings)}; no = 0xFFFFFFFF; uri = ix[strings[4]]
    def node(kind, extension):
        return struct.pack("<HHIII", kind, 16, 16+len(extension), 1, no) + extension
    def start(name, attributes=()):
        ext = struct.pack("<IIHHHHHH", no, ix[name], 20, 20, len(attributes), 0, 0, 0)
        for name, typ, value in attributes:
            ext += struct.pack("<IIIHBBI", uri, ix[name], no, 8, 0, typ, value)
        return node(0x102, ext)
    def end(name): return node(0x103, struct.pack("<II", no, ix[name]))
    content = make_pool(strings)
    content += struct.pack("<HHI3I", 0x180, 8, 20, 0x01010199, 0x01010119, 0x01010121)
    content += node(0x100, struct.pack("<II", ix["android"], uri))
    content += start("adaptive-icon")
    content += start("background", (("drawable", 0x1C, 0xFFFFFFFF),)) + end("background")
    content += start("foreground")
    content += start("bitmap", (("src", 1, MONO_ID), ("tint", 0x1C, 0xFF000000))) + end("bitmap")
    content += end("foreground")
    if sdk == 33:
        content += start("monochrome", (("drawable", 1, MONO_ID),)) + end("monochrome")
    content += end("adaptive-icon")
    content += node(0x101, struct.pack("<II", ix["android"], uri))
    return struct.pack("<HHI", 3, 8, len(content)+8) + content


def table_entries(data):
    require(struct.unpack_from("<HHI", data) == (2, 12, len(data)), "Invalid table")
    global_strings = string_pool(data, 12); entries = {}; specs = {}
    for p, kind, head, size in chunks(data, 12, len(data)):
        if kind != 0x200: continue
        package_id = struct.unpack_from("<I", data, p+8)[0]
        require(head == 288 and package_id == 0x7F, "Unexpected package header")
        key_pool = string_pool(data, p+struct.unpack_from("<I", data, p+276)[0])
        for q, typ, h, s in chunks(data, p+head, p+size):
            if typ == 0x202:
                tid = data[q+8]; count = struct.unpack_from("<I", data, q+12)[0]
                specs[tid] = tuple(struct.unpack_from("<"+"I"*count, data, q+h))
            if typ != 0x201: continue
            tid, flags = data[q+8:q+10]; count, values_start = struct.unpack_from("<II", data, q+12)
            require(flags == 0, "Sparse/offset16 table unsupported")
            config = bytes(data[q+20:q+h]); config_size = struct.unpack_from("<I", config)[0]
            require(len(config) == config_size, "Unexpected config extent")
            for i in range(count):
                offset = struct.unpack_from("<I", data, q+h+4*i)[0]
                if offset == 0xFFFFFFFF: continue
                e = q+values_start+offset; eh, ef, key = struct.unpack_from("<HHI", data, e)
                if ef & 1:
                    bag_count = struct.unpack_from("<I", data, e+12)[0]; length = eh+bag_count*12
                    value = bytes(data[e:e+length])
                else:
                    require(eh == 8, "Unexpected simple resource entry")
                    typ = data[e+eh+3]; raw = struct.unpack_from("<I", data, e+eh+4)[0]
                    value = (typ, global_strings[raw] if typ == 3 else raw)
                rid = (package_id << 24) | (tid << 16) | i
                require((rid, config) not in entries, "Duplicate resource configuration")
                entries[rid, config] = (key_pool[key], value)
    return entries, specs


def patch_table(original):
    require(digest(original) == TABLE_SHA256, "Wrong original resource table")
    old_strings = string_pool(original, 12); paths = sorted(NEW_PATHS)
    indices = {p: len(old_strings)+i for i, p in enumerate(paths)}
    output = bytearray(original[:12]); observed = []
    for p, kind, head, size in chunks(original, 12, len(original)):
        raw = original[p:p+size]
        if kind == 1:
            output += append_pool(raw, paths); continue
        require(kind == 0x200 and head == 288, "Unexpected top-level chunk")
        package = bytearray(raw[:head])
        for q, typ, h, s in chunks(raw, head, len(raw)):
            chunk = bytearray(raw[q:q+s])
            if typ == 0x202 and chunk[8] == 8:
                count = struct.unpack_from("<I", chunk, 12)[0]; require(count == 2, "Launcher type capacity changed")
                for i in range(count):
                    flags = struct.unpack_from("<I", chunk, h+i*4)[0]
                    struct.pack_into("<I", chunk, h+i*4, flags | 0x1000)
            if typ != 0x201 or chunk[8] != 8:
                package += chunk; continue
            require(chunk[9] == 0, "Sparse launcher table unsupported")
            count, estart = struct.unpack_from("<II", chunk, 12)
            require(count == 2 and chunk[20+29] & 0x30 == 0, "Unexpected launcher config")
            density = struct.unpack_from("<H", chunk, 20+14)[0]
            sdk = struct.unpack_from("<H", chunk, 20+24)[0]
            if sdk == 0:
                require(density in DENSITIES, "Unexpected legacy density")
                path = "res/infinity_launcher_light_" + DENSITIES[density][0] + ".png"
                expected = LEGACY_PATHS[density]
            else:
                require(density == 65534 and sdk in ADAPTIVE_PATHS, "Unexpected adaptive configuration")
                path = "res/infinity_launcher_light_v" + str(sdk) + ".xml"; expected = ADAPTIVE_PATHS[sdk]
            night = bytearray(chunk); night[20+29] = (night[20+29] & ~0x30) | 0x20
            for i in range(count):
                offset = struct.unpack_from("<I", chunk, h+i*4)[0]
                require(offset != 0xFFFFFFFF, "Missing launcher resource")
                e = estart+offset
                require(struct.unpack_from("<HH", chunk, e) == (8, 0) and chunk[e+11] == 3, "Unexpected launcher entry")
                old_index = struct.unpack_from("<I", chunk, e+12)[0]
                require(old_strings[old_index] == expected[i], "Launcher path preimage mismatch")
                struct.pack_into("<I", chunk, e+12, indices[path])
            observed.append((density, sdk)); package += chunk + night
        require(len(observed) == 7, "Missing or duplicated launcher configuration")
        struct.pack_into("<I", package, 4, len(package)); output += package
    struct.pack_into("<I", output, 4, len(output))
    before, before_specs = table_entries(original); after, after_specs = table_entries(output)
    require({k: v for k, v in before.items() if k[0] not in ICON_IDS} ==
            {k: v for k, v in after.items() if k[0] not in ICON_IDS}, "Non-icon semantic delta")
    require({k: v for k, v in before_specs.items() if k != 8} ==
            {k: v for k, v in after_specs.items() if k != 8}, "Non-icon config flag delta")
    require(after_specs[8] == tuple(f | 0x1000 for f in before_specs[8]), "Launcher uiMode flags")
    require(len(after)-len(before) == 14, "Unexpected resource config additions")
    return bytes(output)


def expected_resources(baseline_members: Mapping[str, bytes]):
    for path, expected in BASELINE_SHA256.items():
        require(path in baseline_members and digest(baseline_members[path]) == expected,
                "Original launcher input mismatch: " + path)
    require(not set(baseline_members) & NEW_PATHS, "Light resources already present in baseline")
    fw, fh, foreground = png_rgba(baseline_members[FOREGROUND_PATH])
    mw, mh, mono = png_rgba(baseline_members[MONO_PATH])
    require((fw, fh) == (mw, mh) and foreground[3::4] == mono[3::4], "Original color/mono alpha differs")
    result = {TABLE: patch_table(baseline_members[TABLE])}
    for density, (qualifier, size) in DENSITIES.items():
        path = LEGACY_PATHS[density][0]
        require(png_rgba(baseline_members[path])[:2] == (size, size), "Wrong legacy dimensions")
        result["res/infinity_launcher_light_"+qualifier+".png"] = light_legacy(baseline_members[path], baseline_members[MONO_PATH])
    for sdk in ADAPTIVE_PATHS:
        result["res/infinity_launcher_light_v"+str(sdk)+".xml"] = adaptive_xml(sdk)
    require(set(result) == NEW_PATHS | {TABLE}, "Unexpected resource output budget")
    return result


def verify_resources(candidate_members: Mapping[str, bytes], baseline_members: Mapping[str, bytes]):
    expected = expected_resources(baseline_members)
    for path, original_hash in BASELINE_SHA256.items():
        if path != TABLE:
            require(path in candidate_members and digest(candidate_members[path]) == original_hash,
                    "Original dark/source asset changed: " + path)
    for path, data in expected.items():
        require(path in candidate_members and candidate_members[path] == data,
                "Unexpected light/table resource output: " + path)
    before, _ = table_entries(baseline_members[TABLE]); after, _ = table_entries(candidate_members[TABLE])
    return {"status": "PASS_EXACT_ICON_ONLY_TABLE_TRANSFORM", "original_table_sha256": TABLE_SHA256,
            "table_sha256": digest(expected[TABLE]), "original_dark_assets": "ALL_BYTE_IDENTICAL",
            "resource_ids": [hex(v) for v in sorted(ICON_IDS)], "new_resource_ids": 0,
            "original_entries": len(before), "new_entries": len(after),
            "night_config_additions": 14, "non_icon_resource_entries": "EXACT_SEMANTIC_AND_ORIGINAL_CHUNK_IDENTITY",
            "adaptive_symbol_alpha": "EXACT_ORIGINAL_MONO_AND_COLOR_ALPHA; RESOURCE_BLACK_TINT_ONLY",
            "legacy_symbol": "SAME_ORIGINAL_MONO_ALPHA; STANDARD_CENTERED_72_OF_108_ADAPTIVE_VIEWPORT_RESAMPLED_TO_ORIGINAL_DENSITY",
            "legacy_tile_alpha": "EXACT_ORIGINAL_DENSITY_TILE_ALPHA",
            "new_path_sha256": {p: digest(expected[p]) for p in sorted(NEW_PATHS)},
            "manifest": "NOT_MODIFIED_BY_ICON_IMPLEMENTATION",
            "launcher_limits": "Launcher caches may retain an old drawable; user-enabled themed-icon palettes control monochrome colors. Resource resolution does not guarantee every Samsung surface refreshes immediately.",
            "physical_Samsung": "NOT_VERIFIED", "shutdown": "NOT_RUN"}


def read_members(path):
    with ZipFile(path) as z:
        prefix = "payload/" if "payload/resources.arsc" in z.namelist() else ""
        names = [(n, n[len(prefix):]) for n in z.namelist() if n.startswith(prefix) and not n.endswith("/")]
        return {logical: z.read(n) for n, logical in names if logical == TABLE or logical.startswith("res/")}


def main():
    p = argparse.ArgumentParser(); p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--out", type=Path); p.add_argument("--verify", type=Path); a = p.parse_args()
    original = read_members(a.baseline)
    if a.out:
        a.out.mkdir(parents=True, exist_ok=False); changed = expected_resources(original)
        for path, data in changed.items():
            target = a.out/path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        proof = verify_resources(original | changed, original)
        (a.out/"proof.json").write_text(json.dumps(proof, indent=2)+"\n")
        print(json.dumps(proof, indent=2))
    if a.verify:
        print(json.dumps(verify_resources(read_members(a.verify), original), indent=2))
    require(a.out or a.verify, "Select --out or --verify")


if __name__ == "__main__": main()
