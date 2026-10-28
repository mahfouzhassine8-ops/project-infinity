**Continuation delivered:** [signed2103427](continuation/DELIVERY.md) includes the
two P0 corrections and further Home/TV/count optimizations while preserving this
2103426 implementation. The [completion ledger](continuation/COMPLETION-LEDGER.md)
retains all unfinished original requirements and exact runtime limits.

**Signed 2103426 delivered:** see [DELIVERY.md](DELIVERY.md) for the final APK,
matching components, checksums, original-signature verification and limitations.
The four production corrections below passed focused host checks and the full
signed payload gate. The user explicitly authorized the metadata-only chooser
exception and sole-signer branch/module preparation changes. The earlier
signing-blocker analysis at the end is retained as the resolved historical
reason that exception was necessary; no gate was bypassed.

The recovery baseline remains combined **2103425**, source
`db730100a3bfea7e06d2e6c3434e89aeb6fa8a15`, signed run
[40606707330](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/40606707330).
The exact APK SHA256 is
`f6d043d4791cfc851af65c5e705ef2f1b22e8d885c5f0180592f5291b6bc7612`.
Original certificate SHA256 is
`d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

The complete edited production sources are in `overlay/script.infinity.commandcenter/`.
`stage.py` applies only those five exact-preimage files to the actual signed
baseline, compiles the Python sources, reconstructs the native-authenticated
75-file module inventory, and removes the obsolete signature. It deliberately
does **not** attach an old signature to changed code or produce an installable
APK. The issued Command Center version is **0.3.5.50**, Infinity component
`2103420.isolation.1.performance.1`, combined version **2103426**. The separate
authorized `prepare_release.py` authenticates the module in the existing sole
signer; the final combined gate independently verifies the concrete owner vector.

| Demonstrated baseline behavior | Implemented correction | Focused verification |
| --- | --- | --- |
| Resume/Home lists copy nested metadata for every candidate before slicing to 20/100 displayed rows. | Sort, filter hidden rows and group exact IDs across the complete projection first; privately copy only the returned rows. Unbounded consumers preserve their full results. | Actual signed-source equivalence for movie, TV, history, later and custom lists; conflicting IDs, hidden rows, order, private copies and input preservation. |
| A 20-card list crosses the Python/native submission API 20 times. | Submit the same ordered `(target, ListItem, folder)` rows in one batch. | Exact rows and folder flags compared; original card builder, playback offsets, artwork, context actions, selection tokens and end-of-directory behavior preserved. |
| A selected-provider Search parses/verifies every installed provider again on submission. | Filter the freshly enumerated inventory to the explicitly selected ID before expensive recognition. Never publish a narrowed snapshot as the full cached inventory. | Four-provider transport verifies 4 → 1 for a selected search; Search All still verifies all four. Missing/invalid IDs and inventory-change races fail safely. Source/dependency dispatch verification remains exact. |
| Search cache keys omit dependency contracts, roots, provider settings and watched/progress revisions; a state change during a native request can cache/publish an old response. | Bind answers to profile, exact route, source root, complete contract/dependencies, file replacement stamps and existing UI revisions. Verify the state again after original source checks and before publication/cache insertion. | Unchanged repeat reuses one response; progress, dependency, root, settings and saved-state changes each fetch anew. Cache-hit/worker races cannot publish stale results. Cancellation, failure, disabled sources and linked/unknown state cannot create reusable answers. |

All route validation, raw pin checks, source authentication, native admission,
provider leases, cancellation cleanup and worker ownership remain unchanged.
The original four-response, 300,000-byte, 300-second Search caps remain exact.
No new service, worker, persistent cache, database, migration or timeout exists.
The property/file stamps are invalidation hints and grant no provider authority.

Host measurements use actual projection functions and an explicitly synthetic
1,000-row local saved-metadata fixture, including nested cast data. The finalized
same-host measurements were **78.2 → 11.6 ms median** and **9,361,080 → 1,041,712
traced peak bytes**, with **1,000 → 20** private entry copies per 20-card view.
These measure only projection work. They do not measure Android RSS/PSS, native
queue depth, provider latency, startup, first painted artwork, frame pacing,
battery or thermal behavior. CI records its own samples under separate machine
conditions; do not mix these numbers with the historical Fold observations.

The 14 additional focused negative/race controls pass locally. Baseline input
verification checks the complete owner-bundle payload inventory and original
RSA module signature. Seventy other authenticated first-party files and every
non-selected function/class remain exact; the full changed-member review is in
`results/PRESERVATION.json`. There are no resource/skin/layout edits. The manual
`infinity-performance-host` choice in the existing feature workflow executes
only this host comparison and source staging; its Android job is excluded.

Remaining work and limits:

- No physical device or Android emulator is attached here. Current 2103425
  startup, Continue-card delay, playback return, Search IME, scrolling, fold,
  CPU/PSS, FPS, heat and real native queue counts remain unmeasured. The prior
  0.55–10.23-second Fold observations apply to earlier builds.
- The demonstrated prior native-bridge `talloc_lib_init` constructor SIGSEGV
  occurred before Kodi/Python/Home execution. The historical physical SIGBUS
  lacks a matching current-build causal stack. No speculative allocator,
  threading, signal-handler or native timeout patch has been made.
- Upstream provider/network/account changes still depend on existing provider
  refresh and the original response TTL. The new invalidation covers observable
  local state, settings, source/dependency and revision changes; it does not
  invent a provider change-notification protocol.
- Native directory scheduling, global worker limits and protected persistence
  were left intact. Reduced projection work and selected-provider recognition
  do not establish a measured reduction of the earlier 40–114 native job queue.
- Shutdown is frozen and **NOT RUN**. Cobra/chooser runtime testing, stress
  matrices and destructive data operations are **NOT RUN**.

The following original signing conflicts were resolved through the user's
explicit exception, recorded in `RELEASE-AUTHORIZATION.json`:

1. `release_authority.transition()` requires an updated Infinity last-updated
   label and then raises `UPDATED_LABELS_REQUIRE_SHELL_BUNDLE` unless the
   chooser owner is changed. `validate()` binds that label to chooser-owned
   `assets/experience-component-updates.properties`. The current scope forbids
   modifying even that chooser payload, so this cannot be waived implicitly.
2. `release_gate.AUTHORITY_BRANCH` and the sole combined workflow's job guard
   allow only the previous isolation engineering branch. The current task must
   remain on the existing performance branch.
3. The current selected-owner assembler consumes already authenticated immutable
   bundles. A guarded new module-manifest signing stage must be added inside the
   existing sole original-key pipeline before the new Infinity component can
   be registered. No substitute signer or retired signer has been enabled.

See the historical `results/SIGNING-BLOCKERS.json` and final
`results/FINAL-CI-RECEIPT.json`. The reviewed authority now selects the exact
authenticated new Infinity and metadata-only chooser bundles. The original
payload/ownership/signature checks remain enforced. Accepted pointers,
protected branches, signing identity, shared runtime and shutdown remain
unchanged. Final physical Fold acceptance is exclusively the user's decision.
