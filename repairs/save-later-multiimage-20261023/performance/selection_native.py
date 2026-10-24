"""Admit exact new CC35 to the unchanged shared Infinity selection adapter."""
import hashlib
from pathlib import Path
PATH='xbmc/guilib/GUIBaseContainer.cpp'
ORIGINAL_SHA='4a716be3ce8024e430fe17827437b83ba8ce5a438549958d9e57395e980d0082'
RETAINED_SHA='204b94ef5fd58229a1101a6ecdbf439785b01770bacdebc45b297227ec24c86b'
OLD='ADDON::OnlyEnabled::CHOICE_YES) && addon->Version().asString() == "0.3.5.34";'
NEW='ADDON::OnlyEnabled::CHOICE_YES) && (addon->Version().asString() == "0.3.5.34" ||\n      addon->Version().asString() == "0.3.5.35");'
def patch(raw):
 if hashlib.sha256(raw).hexdigest()!=RETAINED_SHA:raise RuntimeError('Shared selection CC34 preimage differs')
 text=raw.decode()
 if text.count(OLD)!=1:raise RuntimeError('Shared selection owner predicate differs')
 return text.replace(OLD,NEW,1).encode()
def apply(source,overlay):
 original=(Path(source)/PATH).read_bytes()
 if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:raise RuntimeError('Original selection source differs')
 file=Path(overlay)/PATH;updated=patch(file.read_bytes());file.write_bytes(updated)
 return {PATH:dict(original_sha256=ORIGINAL_SHA,final_sha256=hashlib.sha256(updated).hexdigest(),defect='Coordinated CC35 shared selection admission',justification='Retain exact CC34 owner and add CC35; all other shared selection, native and Cobra paths byte-identical')}
