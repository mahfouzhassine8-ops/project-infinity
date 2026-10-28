The existing signed **2103426** delivery is preserved. This continuation repaired
an SDK prerequisite and attempted one focused journey on the previously usable
Android 17 infrastructure. It did **not** complete Android feature verification.

The first new run, [40726322312](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40726322312),
failed at SDK22 `sdkmanager --licenses` with exit 1 before APK installation.
The action hid stderr. Restoring the explicit Java17 setup from prior successful
jobs cleared that operation in the next run; exclusive Java causal attribution
is not established.

The second run, [40726662543](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40726662543),
successfully set up SDK22, booted Android 17/API37.1, checked the original signer
and exact signed APK, configured the existing documented emulator OS16KiB
backcompat properties, and issued one application launch. It then failed before
Kodi/Python: engine PID7568 received **SIGSEGV / SEGV_MAPERR** in
`libkodi.so+0x2bf49fc`, `talloc_lib_init+60`, during `dlopen` constructors.
`JSONRPC.Ping` never became ready, so the Home/Continue/Search/playback assertions
did not execute. No timing or performance result can be inferred from this run.

Read-only inspection of the delivered ELF resolves `getauxval(AT_RANDOM)`,
`rand()` and the four-byte load at that PC. Captured `x19=0x6ffc1f0b5fc0` and
`x8=7` sum to actual fault address `0x6ffc1f0b5fc7`. The library SHA256 is
`151128c176b6094f28bb3fc716cc07c3985a9aa38f1fe41e1bb1424f0285a47e`,
byte-identical to protected 2103425. Why the returned pointer was unreadable
is unresolved. Translation was present; a bridge-only cause and the cause of
physical Fold crashes are **not** established. No native patch, signal
suppression, longer deadline, app restart or repeated identical trial was used.

The earlier [40407451498](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40407451498)
actually booted Kodi/Python and displayed a saved card and cached QA bitmap on
this API37.1 OS-backcompat route. Its later playback-return observer failed.
The new run used the same image family, native-bridge SHA256 and two compatibility
property values. That earlier success was a legitimate reason to investigate
this accessible route, but does not establish current-build reliability.

Raw [RESULT](ANDROID17-40726662543.json), [constructor attribution](CONSTRUCTOR-40726662543.json)
and [run/artifact receipt](INVESTIGATION-RECEIPT.json) are retained. The complete
[CI artifact](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40726662543/artifacts/12833501798)
was downloaded and its ZIP SHA256 verified. Raw `application_restarts=0` refers
to harness requests: Android started a replacement main/Splash process after
the engine died. No successful engine recovery is claimed.

The seven focused harness guard tests and existing workflow-routing control
passed. Those are host tests, not application or physical-device acceptance.
This continuation changed only test orchestration, test fixtures and evidence.
No APK was rebuilt, no signing operation was run, and no production/native,
Cobra, chooser or shutdown bytes changed. The sole application invocation left
cleanup to disposal of the disposable emulator; shutdown tests were **NOT RUN**.

| Original requirement | Current status |
| --- | --- |
| Preserve baseline, features/data boundaries and protected owners | Delivered payload/signature gates passed; 2103425 remains recovery baseline. Physical feature acceptance remains pending. |
| Faster local Home/Resume projection | Implemented in signed2103426; actual production functions verified and measured on host fixtures. Cold/warm startup and first usable card on Android remain unverified. |
| Reuse/invalidate content efficiently | Selected-provider recognition and bounded Search answer invalidation implemented and host-verified. General Home restoration, provider refresh, poster/rendered-state reuse improvements remain unfinished. |
| Fewer native/background jobs | One batched directory submission and fewer selected-provider recognitions implemented. The 40–114 queued-job cause and device queue reduction remain unfinished; global scheduling is unchanged. |
| Search/native/ANR stability | Tracked-state Search races corrected and host-verified. Current Search runtime, native-provider cancellation, physical SIGBUS/SIGSEGV/ANR causes and repairs remain unfinished. The captured pre-Python emulator crash is a separate unresolved blocker. |
| Smooth scrolling/touch/transitions/focus/fold/animation | No redesign or runtime frame-rate change. Device responsiveness and frame pacing work remains unfinished and unmeasured. |
| Memory/battery/thermal efficiency | Reduced projection allocations measured on host. Long-running Android RSS/PSS/CPU, battery and temperature improvements remain unverified; broader work remains unfinished. |
| Consolidated original-key APK and exact components | Completed: signed2103426, matching four owner ZIPs, source/signature/checksums and successful build linked in ../DELIVERY.md. Install-over identity verified; physical install-over not executed here. |
| Physical Fold release acceptance | Pending user only; never inferred from host/emulator results. |

The remaining runtime blocker is a native failure before the Infinity-owned
code executes on the available authorized emulator route. The smallest useful
next runtime step is one focused current-build journey on a reachable supported
native-ARM Android17 environment or the installed Fold. No such device is attached
to this workspace. Changes to the shared native runtime require separate explicit
scope and causal investigation; that authorization alone would not establish a
safe fix. There is no evidence-based harness-only correction left for this crash.
The overall original performance assignment is therefore **partially delivered,
not fully complete**. No new Fold capture or release acceptance is claimed.
