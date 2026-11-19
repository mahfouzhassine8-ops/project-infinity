"""Play a controlled clip through the real saved-movie and Helper callback paths."""
import argparse
import ast
import codecs
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tarfile
import time
import urllib.request
from xml.etree import ElementTree
from zipfile import ZipFile

from verify_android import (
    HERE, ROOT, PACKAGE, PROFILE, MANIFEST, adb, observe, launch_and_verify,
    package_record, file_sha, load, require, signature,
)
import common_release as release
from prepare_modules import CC, inventory, stage
from prepare_authority import BASE_COMMIT, DIAGNOSTIC_COMMIT, AUTHORITY, ref_blob
from release_driver import PUBLIC_KEY

HELPER = "plugin.video.themoviedb.helper"
QA = "script.infinityqatypedmovie"
FIXTURE = "plugin.video.infinityqaclip"
PROVIDERS = {choice: FIXTURE + choice.lower() for choice in ("A", "B")}
ADDONS = PROFILE + "/addons"
DATA = PROFILE + "/userdata/addon_data"
MOVIES = ("701001", "701002")
NATIVE = "lib/arm64-v8a/libkodi.so"
SIGNER = 397702717
SEED = HERE / "TYPED-MOVIE-ANDROID.json"
REPORT = "TYPED-MOVIE-PLAYBACK.json"


def get_input(row, filename, label):
    require(row["workflow_id"] == SIGNER, "Original APK signer workflow required")
    path = release.unique(release.obtain(row, label), filename)
    require(file_sha(path) == row["APK_sha256"], "Wrong exact APK bytes")
    signature(path)
    return path


def download(row):
    with urllib.request.urlopen(row["url"], timeout=120) as response:
        raw = response.read(28 * 1024**2 + 1)
    require(len(raw) <= 28 * 1024**2 and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "Publisher archive digest differs")
    return raw


def make_fixture(root, clip, row, candidate):
    fixture = root / "kodi"
    addon_dir = fixture / "addons"
    addon_dir.mkdir(parents=True)
    shutil.copytree(candidate, addon_dir, dirs_exist_ok=True)
    helper = addon_dir / HELPER
    helper.mkdir()
    with tarfile.open(fileobj=io.BytesIO(download(row["helper"])), mode="r:gz") as archive:
        for item in archive.getmembers():
            path = Path(item.name)
            require(not path.is_absolute() and ".." not in path.parts and
                    (item.isfile() or item.isdir()), "Invalid publisher archive member")
            if item.isfile():
                target = helper.joinpath(*path.parts[1:])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(item).read())
    xml = (helper / "addon.xml").read_text()
    require(ElementTree.fromstring(xml).attrib["version"] == "6.22.4", "Wrong Helper publisher version")
    # Isolate only the metadata network boundary. Run the actual Router,
    # PlayerFiles, Choose Action, and PlayerResolver with the real Kodi handle.
    (helper / "addon.xml").write_text(xml.replace('library="resources/plugin.py"', 'library="resources/fixture_entry.py"', 1))
    (helper / "resources/fixture_entry.py").write_text(
        "import runpy\n"
        "from pathlib import Path\n"
        "from tmdbhelper.lib.player.dialog.details import PlayerDetails\n"
        "from tmdbhelper.lib.items.listitem import ListItem\n"
        "def fixture_details(self):\n"
        "    assert self.tmdb_type == 'movie' and str(self.tmdb_id) in ('701001', '701002')\n"
        "    return ListItem(infolabels=dict(mediatype='movie', title='Fixture ' + str(self.tmdb_id), duration=90),\n"
        "                    unique_ids={'tmdb': str(self.tmdb_id)}, infoproperties={})\n"
        "PlayerDetails.get_enriched_details = fixture_details\n"
        "runpy.run_path(str(Path(__file__).with_name('plugin.py')), run_name='__main__')\n")
    # Use the same vetted dependency inputs as the retained 2103468 fixture,
    # upgrading only the test copy of jurialmunkey to the 6.22.4 requirement.
    prior = "repairs/infinity-three-corrections-20261108/ANDROID-INPUT-PINS.json"
    pins = json.loads(ref_blob("2f18336ec766cf6e0234ecf7e9727ab4993247ff", prior))
    deps = [x for x in pins["archives"] if x["addon"] not in (HELPER, "plugin.video.umbrella", "script.module.jurialmunkey")]
    for dep in [*deps, row["jurialmunkey"]]:
        with ZipFile(io.BytesIO(download(dep))) as archive:
            require(all(Path(x.filename).parts[0] == dep["addon"] and
                        not Path(x.filename).is_absolute() and ".." not in Path(x.filename).parts
                        and (x.external_attr >> 16) & 0o170000 != 0o120000
                        for x in archive.infolist()), "Invalid dependency archive member")
            archive.extractall(addon_dir)
    for choice, addon_id in PROVIDERS.items():
        addon = addon_dir / addon_id
        addon.mkdir()
        (addon / "addon.xml").write_text(
            f'<addon id="{addon_id}" name="QA Playback {choice}" version="1.0.0" provider-name="QA">'
            '<requires><import addon="xbmc.python" version="3.0.1"/></requires>'
            '<extension point="xbmc.python.pluginsource" library="fixture.py"><provides>video</provides></extension>'
            '<extension point="xbmc.addon.metadata"><summary lang="en_GB">Disposable test clip</summary></extension>'
            '</addon>')
        (addon / "fixture.py").write_text(
            "import sys, xbmcplugin, xbmcgui, xbmcvfs\n"
            "from pathlib import Path\n"
            "from urllib.parse import parse_qs\n"
            "params = parse_qs(sys.argv[2][1:])\n"
            "assert params['tmdb'] in (['701001'], ['701002']) and params['choice'] in (['A'], ['B'])\n"
            "directory = Path(xbmcvfs.translatePath('special://profile/addon_data/" + FIXTURE + "'))\n"
            "directory.mkdir(parents=True, exist_ok=True)\n"
            "tmdb, choice = params['tmdb'][0], params['choice'][0]\n"
            "path = str(directory / ('fixture-' + tmdb + '.mp4'))\n"
            "item = xbmcgui.ListItem(path=path)\n"
            "item.getVideoInfoTag().setUniqueIDs({'tmdb': tmdb}, 'tmdb')\n"
            "item.getVideoInfoTag().setMediaType('movie')\n"
            "item.getVideoInfoTag().setTitle('Fixture ' + tmdb)\n"
            "(directory / ('selected-' + tmdb)).write_text(choice)\n"
            "xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)\n")
    observer = addon_dir / QA
    observer.mkdir()
    (observer / "addon.xml").write_text(
        f'<addon id="{QA}" name="Selected legacy movie QA" version="1.0.0" provider-name="QA">'
        '<requires><import addon="xbmc.python" version="3.0.1"/></requires>'
        '<extension point="xbmc.python.script" library="probe.py"/>'
        '<extension point="xbmc.addon.metadata"><summary lang="en_GB">Playback fixture observer</summary></extension></addon>')
    (observer / "probe.py").write_text("""import json, os, re
from pathlib import Path
import xbmc, xbmcgui, xbmcvfs

root = Path(xbmcvfs.translatePath('special://profile/addon_data/script.infinityqatypedmovie'))
root.mkdir(parents=True, exist_ok=True)
monitor = xbmc.Monitor()
(root / 'ready').write_text(str(os.getpid()))
last = -1
while not monitor.waitForAbort(.10):
    try:
        request = json.loads((root / 'request.json').read_bytes())
    except (OSError, ValueError):
        continue
    if request['sequence'] <= last:
        continue
    last = request['sequence']
    try:
        operation = request['operation']
        if operation == 'open':
            key = request['key']
            assert re.fullmatch('[a-f0-9]{64}', key)
            xbmc.executebuiltin('RunScript(script.infinity.uirepair,home-choice,' + key + ',movie)')
            result = {'opened': True}
        elif operation == 'menu':
            result = {'heading': xbmc.getInfoLabel('Control.GetLabel(1)'),
                      'popup': xbmc.getInfoLabel('Window.Property(Infinity.UI.Title)'),
                      'dialog': xbmcgui.getCurrentWindowDialogId(),
                      'menus': {}}
            for control in (50, 6, 3):
                count = int(xbmc.getInfoLabel('Container(%d).NumItems' % control) or 0)
                if 0 < count <= 8:
                    result['menus'][control] = [
                        xbmc.getInfoLabel('Container(%d).ListItemAbsolute(%d).Label' % (control, i))
                        for i in range(count)]
        elif operation == 'focus':
            control, index, label = request['control'], request['index'], request['label']
            assert control in (50, 6, 3) and 0 <= index < 8
            xbmc.executebuiltin('SetFocus(%d,%d,absolute)' % (control, index), True)
            assert xbmc.getInfoLabel('Container(%d).ListItem.Label' % control) == label
            result = {'focused': label}
        else:
            raise ValueError(operation)
        reply = dict(sequence=last, result=result)
    except Exception as error:
        reply = dict(sequence=last, error=str(error))
    path = root / 'reply.pending'
    path.write_text(json.dumps(reply))
    path.replace(root / 'reply.json')
""")
    userdata = fixture / "userdata"
    userdata.mkdir()
    (userdata / "guisettings.xml").write_text(
        '<settings version="2"><setting id="lookandfeel.skin">skin.infinity.diggz</setting>'
        '<setting id="general.addonupdates">2</setting><setting id="services.esenabled">true</setting>'
        '<setting id="services.esallinterfaces">false</setting></settings>')
    helper_data = userdata / "addon_data" / HELPER
    (helper_data / "players").mkdir(parents=True)
    (helper_data / "settings.xml").write_text(
        '<settings version="2"><setting id="combined_players">true</setting>'
        '<setting id="bundled_players">false</setting><setting id="default_player_kodi">0</setting>'
        '<setting id="force_recache_kodidb">false</setting></settings>')
    for index, choice in enumerate(("A", "B"), 1):
        player = dict(name=f"QA Playback {choice}", plugin=PROVIDERS[choice], priority=index,
                      is_resolvable=True, play_movie=f"plugin://{PROVIDERS[choice]}/?tmdb={{tmdb}}&choice={choice}")
        (helper_data / "players" / f"fixture-{choice}.json").write_text(json.dumps(player))
    hub = candidate / CC / "resume_hub.py"
    functions = {"_dict", "verified_ids", "media_identity", "identity_key"}
    body = [node for node in ast.parse(hub.read_bytes()).body if getattr(node, "name", None) in functions]
    ns = dict(re=re, hashlib=hashlib)
    exec(compile(ast.Module(body=body, type_ignores=[]), str(hub), "exec"), ns)
    provider_data = userdata / "addon_data" / FIXTURE
    provider_data.mkdir()
    control = userdata / "addon_data" / CC
    control.mkdir()
    entries = {}
    # Use independent legacy rows so the first playback session cannot update
    # the checkpoint tested by Play from Beginning.
    for tmdb in MOVIES:
        shutil.copyfile(clip, provider_data / f"fixture-{tmdb}.mp4")
        identity = ns["media_identity"]("movie", {"tmdb": tmdb})
        key = ns["identity_key"](identity)
        entries[key] = dict(key=key, media="movie", title=f"Fixture {tmdb}",
                            identity=identity, position=24.0, duration=90.0,
                            updated=int(time.time()) - 7 * 86400)
    state = dict(schema=2, revision=1, items=entries, sources={})
    (control / "continue-watching.json").write_text(json.dumps(state))
    return fixture, list(entries)


def rpc(method, params=None):
    request = dict(jsonrpc="2.0", id=288, method=method)
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 19090), timeout=12) as conn:
        conn.sendall(json.dumps(request).encode())
        reader = codecs.getincrementaldecoder("utf-8")()
        decoder = json.JSONDecoder()
        pending = ""
        while len(pending) < 512 * 1024:
            chunk = conn.recv(32768)
            if not chunk:
                break
            pending += reader.decode(chunk)
            try:
                reply, _ = decoder.raw_decode(pending.lstrip())
            except ValueError:
                continue
            require(reply.get("id") == 288 and "error" not in reply,
                    f"{method} rejected: {reply.get('error')}")
            return reply["result"]
    raise RuntimeError(f"Incomplete JSON-RPC response for {method}")


def until(action, label, seconds=45):
    deadline = time.monotonic() + seconds
    detail = None
    while time.monotonic() < deadline:
        try:
            value = action()
            if value:
                return value
        except (OSError, ValueError, RuntimeError) as exc:
            detail = str(exc)
        time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {label}: {detail}")


class Observer:
    def __init__(self, out, pid):
        self.path = out / "observer-request.json"
        self.sequence = 0
        self.pid = pid
        self.root = f"{DATA}/{QA}"
        require(rpc("Addons.ExecuteAddon", {"addonid": QA, "wait": False}) == "OK", "Observer launch denied")
        until(lambda: observe("shell", "cat", self.root + "/ready") == pid, "observer starts", 60)

    def command(self, operation, **values):
        require(observe("shell", "pidof", PACKAGE + ":kodi") == self.pid, "Selected Kodi process exited")
        self.sequence += 1
        self.path.write_text(json.dumps(dict(sequence=self.sequence, operation=operation, **values)))
        adb("push", self.path, self.root + "/request.json")

        def result():
            entry = json.loads(observe("shell", "cat", self.root + "/reply.json"))
            return entry if entry.get("sequence") == self.sequence else None

        answer = until(result, operation + " observer receipt", 10)
        require("error" not in answer, f"Observer request failed: {answer}")
        return answer["result"]

    def select(self, label, heading=None):
        def find():
            result = self.command("menu")
            for control, rows in result["menus"].items():
                if label in rows and (heading is None or result["heading"] == heading):
                    return int(control), rows.index(label)
            raise RuntimeError(f"Actual menu: {result}")

        control, index = until(find, "native menu action " + label, 60)
        focused = self.command("focus", control=control, index=index, label=label)
        require(focused["focused"] == label, "Native dialog focus differs")
        rpc("Input.Select")
        print("Selected real Kodi dialog control:", label, flush=True)


def seconds(value):
    return 3600 * value["hours"] + 60 * value["minutes"] + value["seconds"] + value["milliseconds"] / 1000


def active_video():
    return next((v["playerid"] for v in rpc("Player.GetActivePlayers") if v["type"] == "video"), None)


def playback(tmdb, choice, offset):
    def get_state():
        player = active_video()
        if player is None:
            return None
        values = rpc("Player.GetProperties", {"playerid": player,
                     "properties": ["time", "totaltime", "speed", "currentvideostream", "currentaudiostream"]})
        item = rpc("Player.GetItem", {"playerid": player, "properties": ["uniqueid", "file"]})["item"]
        if seconds(values["totaltime"]) < 89 or values["speed"] != 1 or not values.get("currentvideostream"):
            return None
        return player, values, item
    player, first, item = until(get_state, "Kodi opens and decodes the selected clip", 65)
    start = seconds(first["time"])
    require(offset - 0.5 <= start <= offset + 3.0, f"Expected start near {offset}, actual {start}")
    require(item.get("type") == "movie" and str(item.get("uniqueid", {}).get("tmdb")) == tmdb,
            "Opened playback identity differs from saved movie")
    require(bool(first.get("currentaudiostream")), "Expected a real audio stream")
    require(observe("shell", "cat", f"{DATA}/{FIXTURE}/selected-{tmdb}") == choice,
            "The actual selected Helper action did not invoke its declared provider clip")
    later = until(lambda: (state if (state := get_state()) and seconds(state[1]["time"]) > start + 0.75
                  else None), "actual playback clock advances", 12)
    rpc("Player.Stop", {"playerid": player})
    until(lambda: active_video() is None, "clip stopped")
    return dict(tmdb=tmdb, action=choice, requested=offset, observed=start, advanced=seconds(later[1]["time"]))


def run(out, preparation_run):
    row = load(SEED)
    require(os.environ.get("GITHUB_ACTIONS") == "true" and
            os.environ.get("GITHUB_REPOSITORY") == release.REPO and
            os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and
            file_sha(SEED) == os.environ["SELECTED_AUTHORIZATION"] and
            file_sha(Path(__file__)) == row["driver_sha256"] and
            preparation_run == str(row["prepared_evidence"]["run"]), "Unrecognized selected playback request")
    require(adb("shell", "getprop", "ro.kernel.qemu").strip() == "1" and
            "arm64-v8a" in adb("shell", "getprop", "ro.product.cpu.abilist") and
            "versionCode=" not in observe("shell", "dumpsys", "package", PACKAGE),
            "Fresh disposable emulator with ARM64 execution required")
    out.mkdir()
    baseline = get_input(row["baseline"], "Infinity-2103514-Combined-Original-Signer.apk", "typed-514")
    instrumentation = get_input(row["diagnostic"], "Infinity-2103516-Combined-Original-Signer.apk", "typed-516")
    evidence = release.obtain(row["prepared_evidence"], "typed-prepared-receipt")
    prep = load(release.unique(evidence, "PREPARATION.json"))
    require(prep["source"] == row["prepared_evidence"]["source"] and
            prep["status"] == "PASS_UNSIGNED_514_OWNER_PREPARATION", "Candidate not packaged through verified staging")
    baseline_addons = out / "baseline/assets/addons"
    baseline_scope = load(HERE / "SCOPE.json")["baseline"]
    require(row["baseline"]["APK_sha256"] == baseline_scope["apk_sha256"], "Incorrect protected app")
    rules = json.loads(ref_blob(DIAGNOSTIC_COMMIT, AUTHORITY))["payload"]
    before_rules = json.loads(ref_blob(BASE_COMMIT, AUTHORITY))["payload"]
    names = [key.removeprefix("member:assets/addons/") for key in before_rules
             if key.startswith(tuple(f"member:assets/addons/{aid}/" for aid in
                 (CC, "script.infinity.rails", "script.infinity.uirepair", "script.infinity.watchedbridge")))]
    with ZipFile(baseline) as archive, ZipFile(instrumentation) as diag:
        with diag.open(NATIVE) as src:
            engine = hashlib.file_digest(src, "sha256").hexdigest()
        require(engine == rules["member:" + NATIVE]["sha256"], "Wrong retained diagnostic engine")
        for name in names:
            target = baseline_addons / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read("assets/addons/" + name))
    modules = out / "modules"
    stage(baseline_addons.parents[1], modules, PUBLIC_KEY)
    candidate = modules / "candidate/assets/addons"
    manifest = candidate / MANIFEST.removeprefix("addons/")
    detached = release.unique(evidence, "INFINITY-MODULES.v1.sig")
    shutil.copyfile(detached, manifest.with_suffix(".v1.sig"))
    subprocess.run(["openssl", "dgst", "-sha256", "-verify", PUBLIC_KEY, "-signature", detached, manifest], check=True)
    delta = [name for name, sha in inventory(candidate).items()
             if rules["member:assets/addons/" + name]["sha256"] != sha]
    require(set(delta) == {CC + "/" + name for name in
            ("plugin.py", "INFINITY-MODULES.v1", "INFINITY-MODULES.v1.sig", "addon.xml")},
            "Unexpected change to the original 2103516 modules")
    clip = out / "fixture.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=24",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "90",
                    "-c:v", "libx264", "-crf", "34", "-preset", "ultrafast", "-g", "24",
                    "-c:a", "aac", "-b:a", "32k", "-movflags", "+faststart", str(clip)],
                   check=True, timeout=90, capture_output=True)
    fixture, keys = make_fixture(out, clip, row, candidate)
    require("Success" in adb("install", instrumentation), "Existing signed 2103516 failed to install")
    identity = package_record()
    require(identity["versionCode"] == "2103516", "Actual installed application differs")
    adb("shell", "input", "keyevent", "82")
    adb("shell", "appops", "set", PACKAGE, "MANAGE_EXTERNAL_STORAGE", "allow")
    observe("shell", "pm", "grant", PACKAGE, "android.permission.POST_NOTIFICATIONS")
    adb("root")
    adb("wait-for-device")
    require(adb("shell", "id", "-u").strip() == "0" and adb("shell", "getenforce").strip() == "Enforcing"
            and identity["uid"].isdigit() and int(identity["uid"]) >= 10000, "Fixture must use SELinux-enforced emulator")
    adb("shell", "mkdir", "-p", PROFILE)
    adb("push", str(fixture) + "/.", PROFILE + "/")
    backing = f"/data/media/0/Android/data/{PACKAGE}/files/.kodi"
    uid = identity["uid"]
    adb("shell", "chown", "-R", f"{uid}:{uid}", backing)
    adb("shell", "restorecon", "-RF", backing)
    boot = launch_and_verify(file_sha(manifest))
    require(boot["complete"], f"Normal launch did not activate the staged signed module: {boot}")
    adb("forward", "tcp:19090", "tcp:9090")
    until(lambda: rpc("JSONRPC.Ping") == "pong", "local playback observation interface", 150)
    for addon in (HELPER, *PROVIDERS.values(), "script.infinity.uirepair", QA):
        detail = until(lambda: rpc("Addons.GetAddonDetails", {"addonid": addon,
                       "properties": ["enabled", "version"]})["addon"], "installed " + addon)
        if not detail["enabled"]:
            require(rpc("Addons.SetAddonEnabled", {"addonid": addon, "enabled": True}) == "OK",
                    "Fixture add-on could not be enabled")
    observer = Observer(out, str(boot["engine_pid"]))
    results = []
    for i, (label, choice, offset) in enumerate((("Resume from 0:24", "A", 24.0), ("Play from beginning", "B", 0.0))):
        require(observer.command("open", key=keys[i])["opened"], "Home action denied")
        observer.select(label)
        observer.select("QA Playback " + choice, heading="Choose Action")
        results.append(playback(MOVIES[i], choice, offset))
        print(json.dumps(results[-1]), flush=True)
    require(observe("shell", "pidof", PACKAGE + ":kodi") == str(boot["engine_pid"]), "Engine process changed")
    (out / REPORT).write_text(json.dumps(dict(status="PASS_ACTUAL_TYPED_MOVIE_PLAYBACK", results=results,
        candidate_plugin_sha256=file_sha(candidate / CC / "plugin.py"), module_manifest_sha256=file_sha(manifest),
        engine_sha256=engine, preparation_run_id=int(preparation_run), Fold="NOT_RUN", shutdown="NOT_SELECTED"), indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--preparation-run", required=True)
    args = parser.parse_args()
    try:
        run(args.out, args.preparation_run)
    except Exception:
        print("Kodi pid at the observation failure:", observe("shell", "pidof", PACKAGE + ":kodi"), flush=True)
        state = observe("logcat", "-d", "-v", "threadtime", "-s", "Kodi:I", "DEBUG:E", "libc:F", "AndroidRuntime:E")
        evidence = [line for line in state.splitlines()
                    if any(term in line for term in ("continue_navigation", "Fatal signal", "backtrace:",
                        "tid:", "Abort message:", "libkodi.so", "libndk_translation", "libpython",
                        "Error Type:", "fixture_entry.py", "QA Playback", "PythonToCppException"))]
        print("\n".join(evidence[-100:]), flush=True)
        print(observe("logcat", "-d", "-b", "crash", "-t", "60"), flush=True)
        picture = subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True, timeout=15)
        if picture.returncode == 0 and picture.stdout.startswith(b"\x89PNG"):
            (args.out / "typed-movie-observation.png").write_bytes(picture.stdout)
        raise
