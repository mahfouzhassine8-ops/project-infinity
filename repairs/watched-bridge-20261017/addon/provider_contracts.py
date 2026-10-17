"""Reviewed episode ID scopes, pinned to installed producer code, read outside GUI."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

CATALOG = json.loads((Path(__file__).parent / "PROVIDER-CONTRACTS.json").read_text())
PROOFS = "infinity_watched_identity_proofs"
ENTRY_PROOF = "infinity_provider_contract"


def provider(entry):
    route = urlsplit(str(entry.get("source") or ""))
    return route.netloc if route.scheme == "plugin" else ""


def reviewed(addon_id, proof):
    value = CATALOG.get(addon_id)
    return value if value and value["proof"] == proof else None


def verify(addon_id, root):
    """Never infer semantics from just an add-on name or advertised version."""
    contract = CATALOG.get(addon_id)
    if not contract:
        return None
    try:
        root = Path(root).resolve()
        manifest = ET.parse(root / "addon.xml").getroot()
        if manifest.get("id") != addon_id or manifest.get("version") != contract["version"]:
            return None
        for name, wanted in contract["files"].items():
            path = (root / name).resolve()
            if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > 1024 * 1024:
                return None
            if hashlib.sha256(path.read_bytes()).hexdigest() != wanted:
                return None
        return contract["proof"]
    except (OSError, ValueError, ET.ParseError):
        return None


def canonical(entry, raw, proof):
    if not raw or raw["kind"] != "episode":
        return raw
    addon_id = provider(entry)
    if addon_id:
        contract = reviewed(addon_id, proof)
        return dict(raw, scope=contract["scope"]) if contract else None
    # Generic episode IDs from a checked native-library row have item scope.
    # Local files and absolute anime numbers do not acquire identities by title.
    source = str(entry.get("source") or "")
    return raw if source.startswith("videodb://") and type(entry.get("dbid")) is int and entry["dbid"] > 0 else None


def presentation(entry, raw, saved_proof=None):
    if not raw or raw["kind"] != "episode":
        return raw
    if not provider(entry):
        return canonical(entry, raw, None)
    if not isinstance(saved_proof, dict) or saved_proof.get("identity") != raw or saved_proof.get("provider") != provider(entry):
        return None
    return canonical(entry, raw, saved_proof.get("proof"))
