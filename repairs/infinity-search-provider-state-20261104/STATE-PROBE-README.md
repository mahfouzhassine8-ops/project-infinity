# Read-only Infinity Search state probe

The actual standalone script is [infinity_search_state_probe.py](infinity_search_state_probe.py). It is delivered as source, not an add-on, service, APK or production patch. It has not been installed or run on the Galaxy Fold. No equivalent standalone probe was found in the existing Search work before creating this one.

Script SHA-256: `3766875cb003ed56b86ce44342349e4c2313b4aa133e9677812669e5266bcdb3`.

## What it observes

During one user-driven search session it samples for up to 60 seconds, every 0.5 seconds, with a hard limit of 121 samples and 256 retained events. It does not invoke a provider, repeat a search, change validation, read request tokens, change settings or clear anything.

- Installed version and selected source SHA-256 values for Command Center, Crew, its dependency and WatchNixtoons2, before and after observation. Umbrella, Seren and Otaku have identity-only observations. Unavailable, unreadable and oversized inputs are reported explicitly.
- Changes in the three selected provider settings files, with counts by field category only: search history, request timing, integration status, credential-related, configuration/other. These categories do **not** authorize ignoring any change.
- Byte-identical settings rewrites versus changed contents; initial read states; profile changes; the existing seven global revision properties; the actual Command Center Continue Playing file's metadata.

Settings values and key names are processed only in RAM, using per-session salted comparisons. Neither values, key names, comparison digests, queries, URLs, media paths, credentials nor raw tokens enter the report or script log messages. Source paths in the report are fixed public relative filenames. No provider module is imported. Kodi metadata access uses `getAddonInfo`, not `getSetting`/`SaveSettings`.

The only persistent write by the script is one newly created JSON report under `special://temp`, with an exclusive filename and mode 0600. Existing files cannot be overwritten. Kodi may record its normal script invocation in its own log; that platform behavior is not changed. Keep the output private when sharing it for investigation.

## Launch and access boundary

**Current blocker:** this execution environment has no connected authorized Kodi console, EventServer/script-launch route or Android device connection. Therefore device execution and installed-provider attribution are pending. This does not prevent delivery of the script itself.

If an **already enabled and authorized** Kodi console or control route is available, put the downloaded `.py` in a location Kodi can already read, verify the SHA above, and execute the existing built-in with that actual path:

```text
RunScript("/already-readable/path/infinity_search_state_probe.py")
```

The path above is a placeholder, not a claimed Android location. The preserved native `AddonBuiltins.cpp::RunScript` accepts a script path and submits it to the existing asynchronous invocation manager. This source check is not proof of device permissions or successful execution.

1. Start from the normal Infinity session and invoke the script once using that existing route.
2. When its observation notification appears, perform the ordinary Infinity Search → TV Shows operation that reproduces the problem. The script does not choose or submit a query. If normally practical within the same observation, include a working provider for comparison; do not interrupt or duplicate an in-flight provider merely for the probe.
3. After completion, the notification names `Infinity-Search-State-<UTC>-<suffix>.json` in `special://temp`. Retrieve that file through an existing authorized file/diagnostic route. Do not send raw settings files.

Do not install this as an add-on, modify Favorites/keymaps or installed source, enable new remote-control services, weaken authentication, grant unrestricted storage, or alter the APK merely to launch it. If no existing route is available, stop at the delivered file and keep device execution pending. A production hook would be a separate, reviewable change.

## What this cannot establish

It cannot read the original native request outcome, cache-hit flag, cancellation state, request identity or writer identity. Those are explicitly marked unobservable. Source identity is captured at the endpoints, not continuously. Other dependency settings files are outside this bounded probe. Sampling may coalesce writes, miss short-lived changes or miss a change that returns to its starting value. Empty event output is not proof that nothing changed; inspect initial states and truncation flags.

The 60-second/sample limits bound the loop, but cannot interrupt a blocked Kodi API. No claim is made that a script can safely force native operations to return. No settings-retirement, native, shutdown, provider or playback change is involved.

## Verification

[Ten focused host checks](STATE-PROBE-HOST-RESULTS.txt) pass: privacy, unchanged inputs, identical rewrites, malformed/entity/oversized XML, symlinks, sample/abort/event limits, actual Command Center profile lookup, sanitized identity, profile changes and exclusive report creation. The native call path was inspected to ensure `getAddonInfo` reads metadata rather than calling the settings getter/saver. Android and real-provider tests were not run.

[Bounded host cost evidence](STATE-PROBE-COST.json) uses synthetic settings and 121 simulated samples. With three unchanged 16,271-byte files, the instrumented pass took 0.083131 seconds and peaked at 359,053 traced Python bytes. Rewriting all three at each interval took 3.217119 seconds including 360 fixture writes and allocation tracing; its report hit the 256-event cap. Three unchanged 227,521-byte files took 0.365913 seconds, peaking at 3,390,068 traced bytes. These are host fixture costs, not Android overhead, native-memory measurements or physical acceptance. Source hashing and platform API latency remain unmeasured on the device.

Reproduce only these selected checks:

```bash
PYTHONDONTWRITEBYTECODE=1 python repairs/infinity-search-provider-state-20261104/test_state_probe.py
PYTHONDONTWRITEBYTECODE=1 python repairs/infinity-search-provider-state-20261104/measure_state_probe.py
```

The prior 15 shipped-source checks and 7 provider-side-effect checks are retained, not rerun by these commands. No production Search code, provider, user data, Preview, Cobra, native 2103453, recovery lock or UI454/455 package changed.
