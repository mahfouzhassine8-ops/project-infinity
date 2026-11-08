"""Patch only a disposable emulator QA observer, never an installed/signed APK.

Insert one controlled result-heading action that does *not* dereference a live
Container(50).ListItem immediately before or while navigating. The real
provider folder path must still match, so this is not a fake success gate.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
QA_ADDON = "script.infinity.finalreleaseqa"
ANCHOR = "    if kind=='select-row':\n"
ACTION = """    if kind=='select-row-no-list-read':
        index=request['index']
        assert type(index) is int and 0<=index<=200,'VALID_PREVIOUSLY_OBSERVED_ROW_INDEX'
        expected=request['file']
        assert expected.startswith(tuple('plugin://'+p+'/' for p in PROVIDERS))
        # Already observed and pinned by the host's complete Search All
        # result snapshot, but NEVER dereference a volatile list item here.
        assert xbmcgui.getCurrentWindowId()==10025,'REAL_VIDEO_SEARCH_WINDOW'
        assert 'action=search-all' in xbmc.getInfoLabel('Container.FolderPath')
        xbmc.executebuiltin('Container.SetViewMode(50)',True)
        xbmc.executebuiltin('SetFocus(50,%d,absolute)'%index,True)
        rpc('Input.Select')
        until(lambda:xbmc.getInfoLabel('Container.FolderPath').rstrip('/')==expected.rstrip('/'),
              'exact real provider heading route without selected-item label read',90)
        return dict(status='REAL_PROVIDER_FOLDER_MATCHED_NO_LIVE_LIST_ITEM_READ',
                    folder_path=xbmc.getInfoLabel('Container.FolderPath'),pid=os.getpid())
"""

def run(fixture: Path) -> None:
    baseline = HERE / "android_qa.py"
    qa = fixture / "home" / "addons" / QA_ADDON / "qa.py"
    assert baseline.is_file() and qa.is_file(), "MISSING_REAL_EXISTING_QA_FIXTURE"
    raw = baseline.read_bytes()
    assert qa.read_bytes() == raw, "DISPOSABLE_QA_MUST_MATCH_UNMODIFIED_SOURCE"
    text = raw.decode("utf-8")
    assert text.count(ANCHOR) == 1, "EXACT_ONE_ORIGINAL_ACTION_ANCHOR"
    assert "select-row-no-list-read" not in text, "OBSERVER_ALREADY_MODIFIED"
    patched = text.replace(ANCHOR, ACTION + ANCHOR, 1)
    import ast
    ast.parse(patched, filename=str(qa))
    qa.write_text(patched)
    assert patched.count("select-row-no-list-read") == 1
    print("PASS controlled disposable QA observer only", flush=True)
    print("source_sha256", hashlib.sha256(raw).hexdigest(), flush=True)
    print("fixture_sha256", hashlib.sha256(qa.read_bytes()).hexdigest(), flush=True)
    print("signed_APK_unchanged=true; original_QA_source_unchanged=true", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    run(parser.parse_args().fixture)
