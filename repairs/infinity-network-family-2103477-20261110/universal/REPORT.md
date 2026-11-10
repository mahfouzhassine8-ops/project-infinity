# Networking continuation: findings and release blockers

**No new installer is cleared.** Original-signed 2103478 and 2103479 remain frozen; protected 2103477 is unchanged.
This continuation contains source investigation, one selected matched startup control, and evidence records.
It introduces no production correction because the evidence does not support a safe one within the present attachment boundaries.

## What the existing implementation actually controls

The System Hub selection persists to Command Center and is read by native `CCurlFile` for subsequent HTTP/HTTPS
connections. Retained Android run 42774629373 verifies selected strict-family, redirect, TLS and failure cases,
and real HTTP/VFS video advancement while the mode changes. Those results are reused, not rerun.
They do not establish full provider-to-playback enforcement, completed Stop/cancellation, restart persistence,
forward recovery, or physical Fold acceptance.

The [transport/source matrix](TRANSPORT-BOUNDARIES.md) follows the real handoff and identifies the specific limits:

- Reviewed provider Python clients construct their own requests/urllib clients. No supported external
  Session/opener factory was found in the inspected paths. POV is installed-export evidence; the other
  HTTP implementations are publisher/reference evidence, with installed equivalence explicitly unproven.
- Unchanged Kodi input selection can switch an HTTP/HLS item to direct FFmpeg after a cURL probe.
  Pinned FFmpeg 6.0.1 has no supported TCP address-family option. An invented AVOption cannot enforce it.
- Inputstream add-ons require separate contracts; a VFS-delegated request can be covered, independent sockets cannot.
- No global socket patch, provider singleton mutation, protocol rewrite, or protected dependency change has been made.

Thus, the policy is functional on native cURL paths but **is not universal**. Adding an unused adapter would not
repair the actual chain. The owner's explicit boundary requires stopping individual changes that need protected
third-party or shared-runtime modifications. Those attachment contracts are a concrete remaining implementation blocker.

## What the actual Fold report proves

The owner reports unsuccessful playback in IPv4 Only and IPv6 Only on 2103478 / CC0.3.5.76,
Galaxy Fold8 Ultra / Android17, regular Wi-Fi. Provider, title and exact error were not recorded.
Blade Queen is not a confirmed failed attempt. The named diagnostic ZIP is owner-described version evidence,
without a playback log or connection traces, and was not located in this workspace.

The failure stage remains **UNCLASSIFIED**. The present evidence cannot distinguish source availability,
family support, DNS, connection, TLS, authentication, provider resolution, decoder or another failure.
The fact that some transports bypass the policy is a demonstrated coverage gap, not proof of the historical failure cause.
No repeated playback was selected or performed in this continuation.

## Matched startup result

[Run 42793257656](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42793257656)
ran exactly one first start of each original signed APK on separate fresh VMs with matching qualified
stock API36 image, bridge, emulator configuration and bootstrap settings. No playback, shutdown acceptance,
APK build, signing, data clear, or automatic retry was selected.

| Exact APK | Result | Meaning |
| --- | --- | --- |
| 2103477 | PASS: reached Infinity Home; retained PID through the selected ten-second observation | One successful startup control, not a universal stability claim |
| 2103478 | FAIL: SIGSEGV/SEGV_MAPERR, uptime six seconds; first observed native PID5212 died | A real failed selected start; not a pure-virtual recurrence |

The full, size-stable text tombstone and protobuf were captured and their original artifact hashes verified.
The text includes guest frames below the host translation frame:

`talloc_lib_init+32 → linker call_array → soinfo::call_constructors → do_dlopen → dlopen_ext → native bridge`.

Astra compared this with the same guest constructor stack in earlier unchanged2103469 runs42570831467
(SIGSEGV) and42604600259 (SIGBUS). The new result is consistent with that previously observed constructor/translation
failure, but does not establish a specific bridge defect or production networking cause.

The frozen77 and78 native libraries have identical resolved975-entry constructor target sequences.
Their100-byte `talloc_lib_init` functions differ only in two relinked call displacement fields; targets remain
`getauxval` and `rand`. Normalized instruction bytes match. The recorded guest PC equals LR after the `rand` call;
the retained offset32 instruction is not a load/store. It must not be described as proven to access the host fault address.

The earlier78 **SIGABRT “Pure virtual function called!” in42777116255 remains unresolved**.
This control did not reproduce its signature and cannot relabel it inherited, fixed, or passed.
No source evidence supports changing lifecycle, callback publication, constructors or networking to address either crash.

Evidence: [selected startup results](STARTUP-RESULT-42793257656.json),
[ELF and stack review](STARTUP-ELF-AND-STACK-REVIEW.json),
[original77 report](evidence/startup-42793257656/2103477/STARTUP-CONTROL.json),
[original78 report](evidence/startup-42793257656/2103478/STARTUP-CONTROL.json),
[guest stack excerpt](evidence/startup-42793257656/2103478/GUEST-STACK.txt).
Complete raw logs/maps/tombstones remain in the immutable workflow artifacts linked by the result record.

## Remaining gates and preservation

Release remains blocked by unsupported universal client attachment contracts and unresolved startup attribution.
Native user Stop/pending-play cancellation, process-restart mode persistence, front/inner viewport verification,
signed forward-recovery execution and physical Fold acceptance remain incomplete. Existing host, ARM64 linkage,
signature, module-authentication and selected Android passes remain valid within their original scope.
The historical five-second resolver-cleanup timeout failure remains FAIL under the owner-approved baseline comparison.

No production source, provider, native dependency, Java/DEX, Cobra component, skin layout, Search,
Trakt/tracking/playback implementation, signed APK, owner setting, database, account or library was modified
in this continuation. Only the selected diagnostic harness/workflow route and evidence records changed.
The existing original-key signing request remains disabled. No version was reserved and no new signing/build was initiated.
Future release numbers must be reconciled above all already-issued versions; 2103478/79 cannot be reused.

This is a documented engineering block, not completion or a request for another owner playback cycle.
