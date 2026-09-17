# Cobra 2103156: diagnostics export and end-to-end audit checkpoint

## Baseline and scope

This candidate starts from user-locked Cobra 2103155, commit
`4d1ed032df7e13fd27cc2170fc5e028f5059ec32`, run 35188339917.
Locked APK SHA-256:
`ee26af80797e0d881219314e16b06f86cbb6fd0a9667b0f661120c1844311834`.

The new candidate is NOT locked. The original branch, Kodi native engine,
installed user data, provider/playback decisions, five adaptive layouts,
rotation ownership, background/resume policy and Cinema mode are not rewritten.
This is a completed diagnostics implementation and host-regression checkpoint,
not a claim that every Cobra bug or physical-device scenario has been resolved.

## Confirmed defects repaired

1. Health identity was hard-coded to `candidate-2`. It now reads the installed
   Android package identity, with explicit unavailable status on read failure.
2. Active UI identification matched XML declaration `version="1.0"` before the
   addon version. It now parses the actual addon element and validates its ID.
   This fixes reporting; it does not silently install or replace a UI package.
3. Health Snapshot displayed a persisted historical event as current state.
   Its action now captures live guide/source requests, cached guide status,
   player state, error code, fallback, multiview, recording and lifecycle state.
   Historical event samples remain separately timestamped and labelled.
4. The legacy health file writer deleted its recovery copy before a replacement
   rename succeeded. Health now uses bounded asynchronous, synced atomic writes
   with no delete-before-replace. A failed replacement preserves the old file.
5. Existing redaction omitted access tokens, cookies, authorization and several
   credential-bearing URI formats. Export and diagnostic error recording use
   stronger bounded text redaction, including known raw/encoded account secrets.
6. A later successful state hid the earlier captured error. Bounded event history
   and a separate last-error record now retain it without changing retry logic.
7. There was no Cobra save-as ZIP action. Settings and Health Snapshot now expose
   Export Crash & Diagnostics ZIP with an explicit Android document picker.

## Export flow and contents

Install the candidate APK as an update over Infinity; do not uninstall or clear
app data. Matching UI remains the exact locked 1.3.9 package.

Open Cobra Settings -> Export Crash & Diagnostics ZIP -> Choose save location.
Android asks where to create the ZIP. Available local, removable and cloud
locations depend on the document providers installed and permitted on the device.
No destination is hard-coded, and no report is automatically sent to a server.

The ZIP contains fresh state, previous health state, bounded recent events and
last captured exception, current/previous Kodi log tails where accessible,
previous Infinity exit metadata where accessible, own-app Android exit records,
and bounded ANR text when Android makes it available. A manifest reports missing
or dropped data and event-queue flush status. Text entries deliberately use .txt:
aggressive redaction is not advertised as preserving arbitrary JSON syntax.

Crash history belongs to the shared Infinity app process, not necessarily to
Cobra alone. An empty history or blank error is NOT proof that no crash occurred.
Android exit history requires API 30+. This patch does not install an uncaught
exception handler or native signal hook. It does not capture every Java fatal
stack, obtain unrestricted logcat, or collect all system crash files.

Raw native protobuf tombstones are intentionally omitted because regex redaction
cannot safely remove credentials/private memory from binary traces. Native exit
reason/signal/timestamp metadata is retained. Raw account/settings databases,
playlists, recordings and media are never intentionally included. Redaction is
best effort on arbitrary logs: review the ZIP before sharing it.

Files are allowlisted, bounded and not recursively crawled. Trusted Android
storage-root aliases are supported; descendant log symlinks are rejected.
A ZIP is staged privately and read back before saving. Success is shown only
after the chosen output closes successfully. Null, denied, disk-full and close
failures do not report success; cleanup of the newly created partial document is
attempted. Cancellation writes nothing. Temporary private ZIPs are cleaned up.
The exporter runs off the UI thread; a malfunctioning document provider can still
block its own I/O and requires device testing. Picker recreation state is saved,
but an app force-stop/process kill during export is not a durable background job.

## Verification ledger

Before push, executable host checks passed:

- 47 production archive/redaction/atomic-write checks.
- 6 executions of the production UI-version reader with a StAX XML adapter.
- 26 executions of the production Android diagnostics helper with disclosed
  lifecycle/PackageManager/exit-history/JSON/document-provider doubles.
- 23 structural integration checks; 377 untouched Activity methods and all five
  renderer/layout-policy classes verified byte-identical to 2103155.
- 66 full guide-data cases and 9 short-guide cases against final generated code.
- 42,339 inherited algorithm assertions and 12,223 production layout-policy
  assertions. These are NOT screenshot or Android-rendering acceptance tests.

CI independently repeats the locked reconstruction gates, these regressions,
actual Android compilation, permanent signing, resource-ID/JNI checks and exact
native/assets byte comparisons. A pushed commit is not an installable build until
its signed-artifact upload succeeds. CI stores its results even on failure.

## End-to-end acceptance still pending

| Area | Evidence in this candidate | Still required |
| --- | --- | --- |
| Diagnostics/save-as | Host export, error, bounds, redaction and XML tests | Real picker, Downloads/cloud, cancellation, recreation, low storage |
| Providers/EPG/cache | Existing corrected production methods rerun with fixtures | User's actual providers, refresh/network loss/auth failures |
| Playback/multiview | Protected source, inherited state/math checks | Long playback, connection/decoder limits, 2/3/4 streams, recording |
| Lifecycle/Fold/input | Observer only; policy methods preserved | PiP, background/resume, Fold/cover/rotation, touch/D-pad |
| Visual layouts | Byte preservation, production geometry assertions | Android screenshots and user's final visual acceptance |
| Packaging/update | Exact baseline reconstruction and native/JNI/signer gates | Device installation and persistence checks |

The previously cancelled Android-rendering test is not silently counted as a
pass. Other branches' test results are not automatically applied to this source.
The remaining audit/acceptance items above stay open, rather than being marked
complete merely because host tests or packaging pass.

## Rollback

The workflow preserves the exact 2103155 APK, exact UI ZIP, repository archive,
generated Android source, receipts and hash ledger before applying this delta.
The artifact is `Cobra-2103155-Complete-Rollback-For-2103156`.
Device userdata is NOT backed up by CI. Android may refuse a lower versionCode;
do not uninstall or clear data simply to force a downgrade. Preserve a separate
device-data backup and arrange a reviewed rollback/update path if needed.
