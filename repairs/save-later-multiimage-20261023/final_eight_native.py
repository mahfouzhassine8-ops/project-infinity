"""Exact Infinity-owned video-list hold dispatch; unrelated touch paths untouched."""
import hashlib
from pathlib import Path

PATH = 'xbmc/guilib/GUIBaseContainer.cpp'
BEFORE = '4a716be3ce8024e430fe17827437b83ba8ce5a438549958d9e57395e980d0082'
OLD = '    OnClick(ACTION_CONTEXT_MENU); // original exact-item provider/native context, no Select'
NEW = '    if (local && video)\n    {\n      std::string bucket = item->GetProperty("Infinity.ResumeHub.Bucket").asString();\n      if (bucket != "continue" && bucket != "watchlist" && bucket != "later" &&\n          bucket != "history" && bucket != "watched" && bucket != "collection" &&\n          bucket != "list" && bucket != "ratings" && bucket != "progress" && bucket != "next")\n        bucket.clear();\n      CServiceBroker::GetAppMessenger()->PostMsg(TMSG_EXECUTE_BUILT_IN, -1, -1, nullptr,\n          "RunPlugin(plugin://script.infinity.commandcenter/?action=item-menu&key=" + saved + "&bucket=" + bucket + ")");\n    }\n    else\n      OnClick(ACTION_CONTEXT_MENU); // original exact-item provider/native context, no Select'

def apply(source, overlay):
    raw = (source / PATH).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BEFORE:
        raise RuntimeError('Infinity touch preimage differs from signed baseline')
    text = raw.decode()
    if text.count(OLD) != 1:
        raise RuntimeError('Infinity media hold boundary changed')
    updated = text.replace(OLD, NEW).encode()
    path = overlay / PATH
    if path.exists():
        raise RuntimeError('Overlapping native touch correction')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(updated)
    return {PATH: dict(original_sha256=BEFORE, final_sha256=hashlib.sha256(updated).hexdigest(),
                      defect='Infinity Movies/TV selected-title popup',
                      justification='Only the existing local && video media hold branch dispatches the verified CC popup; other branches byte-identical')}
