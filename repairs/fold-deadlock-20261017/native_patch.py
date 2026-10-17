"""Release retired directory GUI items after releasing the provider lock.

The captured Fold cycle is graphics -> directory (GUI) versus directory ->
graphics (OnJobComplete). Replacing shared GUI items can invoke layout/texture
destructors. Keep the old items alive until the directory guard has unlocked.
"""
from pathlib import Path
import hashlib

SOURCE = "xbmc/guilib/listproviders/DirectoryProvider.cpp"
SIGNATURE = "void CDirectoryProvider::OnJobComplete("
ASSIGN = "    m_items = static_cast<CDirectoryJob*>(job)->GetItems();"
REPLACEMENT = """    // Copy the incoming references before swapping; allocation failure leaves
    // the currently published items intact. Retired GUI layouts may acquire
    // the graphics lock, so their final release must follow directory unlock.
    retiredItems = static_cast<CDirectoryJob*>(job)->GetItems();
    m_items.swap(retiredItems);"""
LIFETIME = """  // Declared before the directory guard: C++ reverse destruction order
  // releases this guard first, including exception and early-return paths.
  std::vector<CGUIStaticItemPtr> retiredItems;
"""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def callback(text):
    start = text.index(SIGNATURE)
    end = text.index("\n}\n", start) + 3
    return start, end, text[start:end]


def apply(root, expected=None):
    path = Path(root) / SOURCE
    old = path.read_bytes()
    if expected is not None and digest(old) != expected:
        raise ValueError("DirectoryProvider differs from the exact TEST4 source map")
    text = old.decode()
    start, end, body = callback(text)
    if "retiredItems" in body or body.count(ASSIGN) != 1:
        raise ValueError("Unexpected or already corrected directory callback")
    if body.count("std::unique_lock<CCriticalSection> lock(m_section);") != 1:
        raise ValueError("Expected the original single directory guard")
    opening = body.index("\n{\n") + len("\n{\n")
    body = body[:opening] + LIFETIME + body[opening:]
    body = body.replace(ASSIGN, REPLACEMENT, 1)
    updated = text[:start] + body + text[end:]
    path.write_text(updated)
    return {"changed": [SOURCE], "before": {SOURCE: digest(old)},
            "after": {SOURCE: digest(path.read_bytes())},
            "scope": "OnJobComplete item ownership lifetime only",
            "rails_stale_request_gate_preserved": "stale job discarded" in body,
            "physical_fold_verified": False, "locked": False}
