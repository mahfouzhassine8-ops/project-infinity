"""Delete exactly eight reviewed private definitions from authenticated 2103373."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = json.loads((HERE / 'removals.json').read_text())

def digest(data):
    return hashlib.sha256(data).hexdigest()

def apply(source):
    target = source / RULES['source_path']
    original = target.read_bytes()
    if digest(original) != RULES['before_sha256']:
        raise RuntimeError('Exact locked source preimage required')
    text = original.decode()
    for member in RULES['methods']:
        if text.count(member['text']) != 1 or digest(member['text'].encode()) != member['sha256']:
            raise RuntimeError('Removal definition mismatch: ' + member['name'])
        text = text.replace(member['text'], '', 1)
    if digest(text.encode()) != RULES['after_sha256']:
        raise RuntimeError('Unexpected cleanup output')
    target.write_bytes(text.encode())
