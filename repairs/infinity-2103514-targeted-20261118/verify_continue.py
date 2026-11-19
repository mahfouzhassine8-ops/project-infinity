"""Focused comparison against the actual signed snapshot, using no user data."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
from urllib.parse import urlencode

addons = Path(sys.argv[1]).absolute()
mode = sys.argv[2]
candidate = mode == "candidate"
assert mode in ("baseline", "candidate")
sys.path.insert(0, str(addons / "script.infinity.commandcenter"))
logs, cases = [], []


def deny_write(*args, **kwargs):
    raise AssertionError("read-only fixture attempted persistence or an unexpected execution")


roots = {"script.infinity.watchedbridge": addons / "script.infinity.watchedbridge"}
sys.modules.update(
    xbmc=SimpleNamespace(Monitor=lambda: SimpleNamespace(abortRequested=lambda: False),
                         getCondVisibility=lambda condition: True, LOGINFO=1,
                         log=lambda text, level: logs.append(text)),
    xbmcaddon=SimpleNamespace(Addon=lambda name: SimpleNamespace(getAddonInfo=lambda field: str(roots[name]))),
    xbmcgui=SimpleNamespace(),
    xbmcplugin=SimpleNamespace(),
    xbmcvfs=SimpleNamespace(translatePath=lambda source: source),
    infinity_search=SimpleNamespace(),
    common=SimpleNamespace(atomic_json=deny_write, read_json=deny_write, persistence_scope=deny_write),
)

import experience
import resume_hub as hub
import saved_navigation as nav


def fixture(ident, route, proof=None, **fields):
    identity = hub.media_identity("movie", {"tmdb": str(ident)})
    key = hub.identity_key(identity)
    entry = dict(key=key, media="movie", source=route, stable_source=route, identity=identity,
                 position=258.0, duration=3600.0, updated=1)
    record = dict(identity=identity, **fields)
    if proof:
        record.update(route=route, route_sha256=nav._hash(route), provider=proof, success_verified=True)
    return entry, dict(items={key: entry}, sources={}, navigation_recovery={key: record})


def recovery(path):
    return path.startswith("plugin://script.infinity.commandcenter/?action=saved-recovery&")


def check(reason):
    if candidate:
        assert json.loads(logs[-1].split(" ", 1)[1])["outcome"] == reason, (reason, logs[-1])


trace = {"trace": nav._continue_trace} if candidate else {}
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    for provider, version, params in (
        ("plugin.video.umbrella", "6.8.02", dict(action="play_Item", tmdb="123456")),
        ("plugin.video.pov", "6.11.03", dict(mode="play_media", mediatype="movie", tmdb_id="123456")),
    ):
        directory = root / provider
        directory.mkdir()
        manifest = directory / "addon.xml"
        manifest.write_text(f'<addon id="{provider}" version="{version}"/>')
        roots[provider] = directory
        route = f"plugin://{provider}/?{urlencode(params)}"
        entry, data = fixture(123456, route)
        assert experience.verified_source(entry, route, **trace) == ""
        check("provider_version_not_approved")
        assert recovery(nav.navigation_target(entry, data, "", "continue", **trace))
        check("original_route_unavailable")
    cases.append("unsupported_provider_versions_remain_rejected")

    # The fake provider advertises no compatibility with real providers. It
    # exercises the remembered, byte-pinned route path independently.
    provider = "plugin.video.fixture"
    roots[provider] = root
    manifest = root / "addon.xml"
    manifest.write_text('<addon id="plugin.video.fixture" version="1.0.0"/>')
    pin = hashlib.sha256(manifest.read_bytes()).hexdigest()
    proof = dict(id=provider, contract=dict(pins={"addon.xml": pin}))
    valid = f"plugin://{provider}/?action=play&tmdb=234"
    invalid = f"plugin://{provider}/?tmdb=123&tmdb=999&credential=PRIVATE_URL_TOKEN"
    bad, bad_data = fixture(123, invalid, proof)
    good, good_data = fixture(234, valid, proof)
    for bucket in ("continue", "watchlist", "later"):
        shared = {}
        assert recovery(nav.navigation_target(bad, bad_data, "", bucket, shared, **trace))
        result = nav.navigation_target(good, good_data, "", bucket, shared, **trace)
        assert (result == valid) if candidate and bucket == "continue" else recovery(result)
        shared = {}
        assert nav.navigation_target(good, good_data, "", bucket, shared, **trace) == valid
        assert recovery(nav.navigation_target(bad, bad_data, "", bucket, shared, **trace))
    cases.append("source_cache_false_rejection_removed_only_for_continue" if candidate else
                 "source_cache_false_rejection_reproduced_in_signed_baseline")

    original, remembered_data = fixture(234, valid)
    record = remembered_data[nav.MEMORY][original["key"]]
    record["failed_routes"] = [{"sha256": nav._hash(valid)}]
    snapshot = json.dumps(remembered_data, sort_keys=True)
    assert recovery(nav.navigation_target(original, remembered_data, valid, "continue", **trace))
    check("original_route_previously_failed")
    assert json.dumps(remembered_data, sort_keys=True) == snapshot
    assert nav.navigation_target(original, remembered_data, valid + "&x=1", "continue", **trace) == valid + "&x=1"
    check("original_route_accepted")
    alternate = good_data[nav.MEMORY][good["key"]]
    alternate["route_sha256"] = nav._hash(invalid)
    assert recovery(nav.navigation_target(good, good_data, "", "continue", **trace))
    check("remembered_route_fingerprint_mismatch")
    alternate["route_sha256"] = nav._hash(valid)
    manifest.write_text('<addon id="plugin.video.fixture" version="2.0.0"/>')
    assert recovery(nav.navigation_target(good, good_data, "", "continue", **trace))
    if candidate:
        assert json.loads(logs[-2].split(" ", 1)[1])["outcome"] == "source_pin_mismatch_or_unreadable"
    cases.append("exact_failure_history_and_changed_provider_pins_remain_enforced")

    nav._protocol = lambda home: None
    nav.available = lambda media: ([dict(id="fixture", name="Fixture")], [])
    nav._mark_failed = deny_write
    nav.resolve = deny_write
    nav.xbmcgui.Dialog = lambda: SimpleNamespace(select=lambda *args: -1)
    try:
        nav._choose_recovery("/unsaved-fixture", original, "continue", remembered_data, object(),
                             lambda entry, sources: valid, resume_offset=258)
    except nav.Cancelled:
        pass
    else:
        raise AssertionError("dismissed chooser was not cancelled")
    assert json.dumps(remembered_data, sort_keys=True) == snapshot
    cases.append("chooser_cancel_has_no_profile_write")

    runtime_path = addons / "script.infinity.commandcenter/infinity_modules/uirepair/runtime.py"
    fn = next(node for node in ast.parse(runtime_path.read_bytes()).body
              if isinstance(node, ast.FunctionDef) and node.name == "home_continue_choice")
    node = compile(ast.Module(body=[fn], type_ignores=[]), str(runtime_path), "exec")
    properties, events = {}, []
    fallback = nav.navigation_target(original, remembered_data, valid, "continue", **trace)
    for choice, offset in (("resume", 258), ("begin", 0)):
        for target in (valid, fallback):
            ctrl = SimpleNamespace(hub=SimpleNamespace(KEY_RE=hub.KEY_RE, entry_identity=hub.entry_identity,
                           load_view=lambda profile: dict(items={original["key"]: original})),
                     PROFILE="/unsaved-fixture", number=float,
                     navigation_target=lambda *args, **kwargs: target,
                     recover_entry=lambda *args, **kwargs: events.append(("recover", kwargs["resume_offset"])),
                     _list_item=lambda *args: (target, SimpleNamespace(
                           setProperty=lambda key, value: properties.update({key: value}))))
            sys.modules["fixture.controller_access"] = SimpleNamespace(load=lambda: ctrl)
            context = dict(__package__="fixture", choose=lambda *args: choice, _continue_choice_clock=str,
                           xbmc=SimpleNamespace(Player=lambda: SimpleNamespace(play=lambda *args:
                               events.append(("play", float(properties["StartOffset"]))))))
            properties.clear()
            exec(node, context)
            context["home_continue_choice"](original["key"], "movie")
            assert events[-1] == ("recover" if target == fallback else "play", offset)
            if target == valid:
                assert float(properties["ResumeTime"]) == offset
    cases.append("resume_and_beginning_preserve_offsets_for_direct_and_recovery")

    manifest.write_text('<addon id="plugin.video.fixture" version="1.0.0"/>')
    key, token = original["key"], "a" * 32
    pending = dict(key=key, token=token, identity=original["identity"], bucket="continue",
                   original=valid, route=valid, provider=proof,
                   source_snapshot=nav._source_snapshot(original))
    receipt = dict(schema=2, key=key, token=token, bucket="continue", identity_verified=True,
                   phase="media_resolved", folder=False, epoch_ms=int(time.time()*1000),
                   original_sha256=nav._hash(valid), destination_sha256=nav._hash(valid))
    window = dict(Pending=pending, Success=receipt)
    nav._property = lambda home, name: window.get(name, {})
    nav.xbmcgui.Window = lambda window_id: SimpleNamespace(
        clearProperty=lambda name: window.pop(name.rsplit(".", 1)[1], None))
    nav.xbmc.getSkinDir = lambda: "skin.infinity.diggz"
    nav.hub.load_view = lambda profile: remembered_data
    nav._change_memory = deny_write
    before_logs = len(logs)
    assert not nav.confirm_saved("/unsaved-fixture", key, token,
                                 dict(infinity_original_route=invalid, type="movie"))
    assert len(logs) == before_logs
    persistence_calls = []
    nav._change_memory = lambda *args, **kwargs: persistence_calls.append(args[2])
    assert nav.confirm_saved("/unsaved-fixture", key, token,
                             dict(infinity_original_route=valid, type="movie"))
    assert persistence_calls == ["continue"] and not window
    if candidate:
        assert json.loads(logs[-2].split(" ", 1)[1])["outcome"] == "playback_verified"
    assert json.dumps(remembered_data, sort_keys=True) == snapshot
    cases.append("handoff_requires_exact_native_receipt_and_playback_provenance")


if candidate:
    assert logs and all(line.startswith("INFINITY_SAVED_NAVIGATION ") for line in logs)
    for line in logs:
        record = json.loads(line.split(" ", 1)[1])
        if record["stage"] != "continue_navigation":
            continue  # Existing baseline trace schema is unchanged.
        assert set(record) == {"schema", "stage", "epoch_ms", "monotonic_ms", "boundary", "outcome"}
        assert record["stage"] == "continue_navigation"
        assert all(value not in line for value in (
            "PRIVATE_URL_TOKEN", "plugin://", valid, invalid, original["key"], "source_snapshot"))
    cases.append("continue_diagnostics_exclude_private_fields")
print(json.dumps(dict(mode=mode, passed=cases), indent=2))
