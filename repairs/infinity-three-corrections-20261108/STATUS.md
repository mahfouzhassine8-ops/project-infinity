# Infinity three corrections — release blocked by Android Search gate

The supplied installed-source evidence is verified. Original-key candidate
2103466 and matching forward recovery2103467 are built and authenticated.
Neither is cleared as a completed combined repair: the first cold Umbrella
Search timed out on the selected Android emulator. No Fold installation or
acceptance has occurred. The accepted release pointer is unchanged.

## Actual baseline and source evidence

Owner-confirmed displayed baseline: combined APK2103464, Infinity2103464,
Cobra2103445, CC0.3.5.62, Umbrella6.8.00, POV6.11.02 and Trakt sync1.2.8.
Trakt auto-update remains enabled.

Infinity_Source_Exports_For_Work.zip SHA256:
`e14b1e9c8441e78ce5c930dea8c7a5885053011d531df9ec51377fcb18298b65`.
All seven outer manifest entries, four nested export receipts, supplied file
checksums, ZIP CRCs and source-only/path constraints PASS. Supplied file counts:
CC65, POV210, Trakt145 and five targeted Umbrella files. This does not claim a
complete Umbrella tree was exported. Runtime QA uses unmodified publisher6.8.00
whose five captured files match the Fold texts after newline normalization.

CC's original RSA signature verifies. All62 exported signed CC records match
its78-file manifest. The other16 records belong to three first-party shim roots
and were not exported. Fresh installed APK hash and those16 source hashes are
still required before owner installation; displayed versions alone are not
installation clearance. See evidence/DEVICE-SOURCE-VERIFICATION.json.

## Umbrella and POV

Actual CC62 contains its old inventory plus the exact approved helper as an
unlisted, inactive file. This explains “Search interface not verified for this
category”. The two approved files from16af10e4 are reused unchanged:
provider_inventory.py and native_search_compatibility.py. Actual-source scans
admit only native movie/search and tv/search for both installed providers.
Host run42435806833 is reused. No provider code or other provider logic changed.
The obsolete CC61 ZIP is excluded.

Both new CC generations authenticate79 records with the original module signer.
CC64 activates the approved inventory/helper. CC65 recovery authenticates the
same helper but restores the old inventory; no source deletion is required.

## Native candidate

Retained SIGABRT42437719318 shows CGUIListItem property-map destruction through
GetMultiInfoLabel and Python getInfoLabel. The inspected production path copies
a live container item without the GUI guard already used by related APIs.
The candidate changes only ModuleXbmc.cpp: Infinity ListItem labels use existing
XBMCAddonUtils::GuiLock for evaluation and item release, with its existing
Python/GIL and GUI lock ordering. No global mutex, provider or observer repair.
This is an evidence-supported unsafe access path, not proof of every crash cause.

Real ARM64 compile/full native link PASS42453405536. Only one of9411 native
sources changed; all71213 strong exports and11 dependencies remain. Linked
native SHA256: ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794.
The candidate's actual AArch64 branch paths reach the unchanged GuiLock.
No native recompile is selected.

Diagnostic heading42441430136 and eight-cycle42443988873 attempt2 are retained
as diagnostic evidence. Their disposable observer workaround is excluded from
this production candidate and current observer. Eight-search and heading
acceptance for the compiled candidate remain incomplete.

## Silent Mode / Trakt

The exact dialog producer is script.module.tmdbhelper.sync.trakt1.2.8:
TraktAuthenticator.notify_failure(), called after
TraktStoredAccessToken.on_failure() records the failure and300-second cooldown.
The two-file correction from514a82e5 gates only automatic failure presentation
on Infinity Silent Mode and forwards existing force_login for manual sign-in.
Logging, cooldown, token operations, lists/tracking and other skins are retained.

All145 installed source files were audited. The two patch preimages exactly
match the reference. The installed public application identifier and Account
Manager Lite sentinel guard are preserved byte-for-byte. The original13 tests
plus the actual sentinel case PASS against the installed recovery dependency.
Before forward-version metadata,143 files remain identical. The packaged tree
changes those two notification files and addon.xml version metadata only.
No user settings, account/token data or databases were supplied or read.

Android run42465125757 attempt2 confirms Kodi selects all145 exact candidate
Trakt files from bundled1.2.8.1 over pre-existing external1.2.8. External source
and profile are not overwritten. Auto-update is unchanged; a future upstream
update can supersede this patch and needs its own source verification.

## Signed pair and preservation

| Purpose | APK / Infinity | Cobra | CC | Trakt | SHA256 |
| --- | --- | --- | --- | --- | --- |
| Internal candidate | 2103466 | 2103445 | 0.3.5.64 | 1.2.8.1 | d366e4b8aadba8484768cfcc0d362c2fc8e0181d78123ea77e04af4f028a3135 |
| Forward recovery | 2103467 | 2103445 | 0.3.5.65 | 1.2.8.2 | 03e43b2b6fb91627722559aeb835c498203e6217efe2f54f85083beb5ca58958 |

Original certificate:
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.
Sole original owner-gated signing workflow397702717 PASS:
42462319257 (candidate) and42463180613 (recovery). Original signer, gate,
assembler and key protections are unchanged. SIGNED-PAIR.json binds sources,
artifacts and APK hashes. No additional build/signing is selected.

Preparation42460784588: ten real unchanged-Java installer cases PASS, including
62→64, same-generation no-op,64→65 recovery, retaining a newer generation,
unknown/tampered/interrupted signature refusal and known partial resume.
Signed candidate has7615 unchanged existing APK members, seven necessary
existing changes and146 additions (CC helper plus145 installed Trakt files).
Recovery has7617 unchanged existing members and five metadata changes.
All DEX, Cobra, skin270, minimal Android contract and every unrelated member
remain byte-identical to authenticated464. No profile migration/updater added.

New recovery restores exact464 native engine and original inventory/Trakt
functional code with forward metadata. It restores pre-correction limitations;
it does not retain these repairs. Existing separately signed465/CC63 recovery
is untouched (SHA256 bec094103bca08abce081038669428ce9babf0aab1d99ca4cb0ec09ca1a729e9).

## Actual Android results and remaining gates

API37/4KiB x86_64 emulator runs the real ARM64 APK through Android's native
bridge. It is not a Galaxy Fold test or native ARM hardware performance proof.

- 42464385488 FAIL before cases: retained observer requested excluded playback
fixture. Only observer admission was narrowed; real live ListItem reads remain.
- 42465125757 attempt1 failed Python download HTTP504 before execution;
attempt2 reused the exact source after the transient download succeeded.
- 42465125757 attempt2 PASS: original464/CC62/external Trakt1.2.8 registered;
signed install-over to466; complete79 authenticated module files and all145
active Trakt files match the APK; profile sentinel preserved.
-First real cold Movie Search All FAIL: The Matrix returned POV21 results and
Umbrella timeout under the unchanged20-second native consumer deadline.
The same KodiPID returned110 snapshots, covering5988 live list-item label reads.
This is not an eight-cycle, heading, deadlock-safety or production crash PASS.
Retained evidence: evidence/ANDROID-COLD-SEARCH-FAIL.json and artifact13611653347.
- The remaining independent actual SDK Trakt ON/OFF/manual/success/other-skin,
forward recovery and ordinary Umbrella Movie/TV route timing diagnostics are
selected in run42467007998. Results pending. An ordinary provider-route timing
or subset PASS cannot clear the retained Infinity Search failure.

Before release, resolve/qualify the real Umbrella timeout and complete the
selected eight distinct Movie/TV Search cycles, four native heading activations,
TV result navigation, Trakt SDK behavior and signed Android recovery. Failed
mandatory gates remain visible. Do not lengthen the native lease, weaken source
validation, pre-seed fabricated results or modify third-party providers.

Before Fold installation, use an already authorized ADB host:

    python3 repairs/infinity-three-corrections-20261108/read_device_inventory.py --out INFINITY-INSTALLED-INVENTORY.json

This hashes the APK, declared first-party files and selected provider/Trakt code;
it reads no user settings/databases and writes only the JSON on the computer.
No phone writes, app launch/stop, installation, root or permission bypass. Access
denial remains a blocker. No re-export of the four supplied packages is needed.
One final owner Fold acceptance is still mandatory after engineering clearance.

Cobra, locked interfaces/themes/navigation, other providers, playback, Continue
Playing, Resume Hub, Watchlists and all user/account data remain protected.
Watchlist-to-Progress tracking and the optional Health Center exporter feature
remain deferred. No Health Center/database change or shutdown test is selected.

Run42467007998 failed before Trakt behavior because the disposable observer
did not mirror the installed module’s own helper/resources import setup. The
QA-only import now follows that exact existing consumer path. The next selected
retry retains this failure and exercises independent forward recovery even if
another SDK/diagnostic case fails; its overall result remains FAIL in that case.


Run42467845009 attempt1 failed before cases on a stock Android System UI ANR;
no Infinity/native repair behavior ran. Attempt2 PASS: real signed466→467 forward
recovery, all79 module/145 active Trakt files and profile sentinel. Ordinary
Umbrella movie route returned21 results in12.02054s;TV returned5 in6.34976s.
These ordinary provider timings do not pass Infinity Search or explain every
previous timeout.

Audit found the reported Silent-ON SDK PASS invalid: HTTP calls0 and cooldown
deadline0. Kodi XBPython.cpp explicitly sets Py_OptimizeFlag=1. SDK calls written
inside assert were omitted, including the retained first-provider-home calls.
All Trakt behavior claims from that attempt are rejected. The raw report and
explicit invalidation remain in evidence/ANDROID-PARTIAL-RECOVERY-AND-INVALID-SDK.json.
Only the disposable observer now converts assertions to equivalent if/raise
checks. Host optimize1 checks confirm the SDK call executes and a failed check
raises; every original live GUI-item read is preserved and now actually runs.
Host acceptance additionally requires HTTP-call/cooldown/device-code evidence.
No production source, APK, provider or native lease changed. The full selected
missing Search/Trakt journey is retried after actual provider-home initialization;
all earlier source/signing/link/recovery evidence is retained. No broad suite.

The owner requested and received a separate read-only Kodi identity diagnostic
1.0.0, source7fb1769f. Its immutable ZIP download is byte-verified, SHA256
ed9456568f4d4ce5d5ad331d988d7e3fffb3d5fbbf01873ba95384985ac8f6c1.
Nine local checks PASS. It uses explicit checks compatible with Kodi optimization,
reads the real APK path and active source files, and writes only a new JSON report.
No ADB/root/permissions/account-settings/database operation. Fold report pending;
Health Center integration remains deferred. See ../infinity-readonly-inventory-20261108/README.md.

Run42469886546 attempts1/2 did not reach application tests: repeated HTTP504
on the uncached host Python3.11.7 archive. The selected QA job now uses the
runner’s cached3.11 patch, records the exact version and requires host assertions
enabled. Actual Android/Kodi Python, sources and signed APKs remain unchanged.
This is a demonstrated test-infrastructure correction, not another APK build.
