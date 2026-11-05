#!/usr/bin/env python3
"""Restore the exact user-approved 2026-11-04 Infinity browser PNG from Git-tracked base64 parts."""
from pathlib import Path
import base64
import hashlib

here = Path(__file__).resolve().parent
parts = sorted((here / "approved-png-parts").glob("APPROVED-INFINITY-MEDIA-BROWSER.png.b64.part*"))
if len(parts) != 12:
    raise SystemExit(f"Expected 12 source parts, found {len(parts)}")
source = b"".join(part.read_bytes() for part in parts)
if len(source) != 2063120:
    raise SystemExit("Approved source base64 length mismatch")
image = base64.b64decode(source, validate=True)
expected = "6786b5cadb7153bb0036a651dcfba889a58f2a5acd79a759a798302e2d70c0ad"
digest = hashlib.sha256(image).hexdigest()
if len(image) != 1547339 or digest != expected:
    raise SystemExit(f"Locked approved PNG checksum mismatch: {digest}")
output = here / "a_polished_ui_mockup_of_the_same_screen_redesigne.png"
if output.is_file() and output.read_bytes() != image:
    raise SystemExit("Refusing to overwrite a different existing approved PNG")
if not output.is_file():
    output.write_bytes(image)
print(f"VERIFIED: {output} ({len(image)} bytes, SHA-256 {digest})")
