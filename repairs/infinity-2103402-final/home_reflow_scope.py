"""Fail-closed owner-only patch: native-owned geometry must not invalidate content."""
from __future__ import annotations
import hashlib

PREIMAGE_SHA256 = "ca9233507680c5d013468a38d4996bb54389ebe4d3e2410df8c241dd8340f6c5"
BEFORE = (b"                elif semantic != self.widget_signature:\n"
          b"                    self.widget_signature = semantic\n"
          b"                    _bump_widget_revision()\n"
          b"                self.stable = sig\n")
AFTER = (b"                elif semantic != self.widget_signature:\n"
         b"                    # Native ownership already reflows live GUI controls.\n"
         b"                    # Geometry alone must not refetch content directory items.\n"
         b"                    self.widget_signature = semantic\n"
         b"                self.stable = sig\n")

def transform(original: bytes) -> bytes:
    if hashlib.sha256(original).hexdigest() != PREIMAGE_SHA256:
        raise ValueError("Not exact signed CC0.3.5.35 service preimage")
    if original.count(BEFORE) != 1:
        raise ValueError("Native owner region is absent or ambiguous")
    after = original.replace(BEFORE, AFTER, 1)
    if after.replace(AFTER, BEFORE, 1) != original:
        raise ValueError("Out of scope service diff")
    compile(after, '<native-owned-reflow>', 'exec')
    return after
