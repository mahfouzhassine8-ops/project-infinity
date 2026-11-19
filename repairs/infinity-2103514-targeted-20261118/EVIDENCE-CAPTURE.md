# 2103514 evidence capture

## Continue Playing

The Android package contains Kodi Health Center and its Add-on Exporter.
It does not bundle the separate `script.infinity.support` add-on referenced
by the Command Center palette. The owner diagnostic does not identify an
installed copy of that optional add-on.

Health Center's diagnostic ZIP contains logs, component identity and diagnostic
metadata. The signed `khc_diagnostics.build_report()` has no saved-record output.
`default.export_installed_addon()` offers **Add-on files only** or
**Add-on files + saved settings/data**. The second option walks the selected
add-on's whole data directory. It is wider than the requested export. Command
Center's **Create Restore Point** captures more profile data and prunes old
restore points. **Restore** changes the profile. Neither action is needed.

**First choice.** Use a private Add-on Export or restore point that already
exists, and is from the affected profile near the failure. Read that ZIP in
place. The helper opens only the Command Center's store member, and emits only a
summary of the selected record.

If there is no existing snapshot, Kodi's built-in **File Manager** can copy only
the necessary JSON file to an already writable private destination. In its
built-in **Profile directory** source, browse
`addon_data/script.infinity.commandcenter/continue-watching.json`. Use **Copy**,
with only that file selected and a private, writable destination already available
in the other pane. Use a folder without an existing copy that could be overwritten.
If Kodi cannot offer an approved writable destination, stop at that permission
boundary.

On the owner's computer with Python 3.8 or newer, pass the existing private ZIP or private copy and the
full `saved_key` from the existing `saved_navigation_cancelled` log entry:

```sh
python3 selected_saved_route.py /path/to/private-snapshot "$SAVED_KEY"
```

Share only the JSON output. The helper computes the route fingerprints locally
and reports equality and failure matches. It emits no URLs, raw route hashes,
titles, media ID values, settings, or tokens. The typed movie identity check
prefers the matching canonical entry and then a single matching alias, like
signed 2103514. Missing, ambiguous and unsupported identities remain explicit.
The optional TMDb fallback comparison is conditional on the resolver being
enabled. An active provider, profile, or resolver choice cannot be inferred
from a copied store. If the summary identifies a relevant provider contract,
compare its exact installed dispatch source and hashes with the reviewed
publisher package before changing the verifier.

The existing four-log archive contains no store. Its recovery event names
only a saved key. No saved movie report could be produced from the currently
available evidence.

## Empty Shell during an ordinary launch

Retain signed 2103514 first. Any existing same-process Android stack or
`script_persistence.initialization_progress` receipt from the affected
session is useful. Health Center's ordinary export summarizes close attempts
and omits the per-writer initialization rows. It also cannot separate the two
native intervals by rereading the same Kodi events. A receipt from an unrelated
launch is not a substitute. No Exit test, process stop, or forced hang is needed.

An already authorized ADB connection can collect just the structured log
lines during ordinary use. Run this before a normal launch since the markers
are emitted early. If Empty Shell occurs naturally, note the device time and
stop the capture after the symptom. Run the command in a private local folder.

```sh
adb logcat -v threadtime -T 1 Kodi:I '*:S' |
  awk -f filter_startup_trace.awk > infinity-startup-trace.txt
```

The filter retains Android PID and native log TID, alongside the event's
request, invoker, worker TID and monotonic time. The event's worker TID is
distinct from its emitting TID because Kodi drains the ring on another thread.
The filter accepts the current 2103514 and proposed diagnostic formats.

With the proposed patch, a create marker identifies the add-on, and
`interpreter.returned value=1` proves Python returned before Kodi's
persistence-ledger call. The following `interpreter.created` shows that
bookkeeping completed. A missing marker is interpretable only with a
same-process capture past that point, active draining and no trace overflow.
A return marker selects the interval for stack investigation. It does not
name the lock owner on its own.

The exact APK member inventory and exporter files are verified against the
signed version's owner hashes. The File Manager profile entry and Android
Kodi log sink were checked against the retained ARM64 source map.
