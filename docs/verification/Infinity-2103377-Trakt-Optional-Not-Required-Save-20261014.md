# Infinity 2103377 — authoritative Trakt optionality decision

**User-approved behavior.** Trakt remains installed, enabled as the user chooses, and available for occasional manual use. Infinity **Resume Hub** is the in-house local-first source of truth for saved viewing progress, Continue Playing, finished-title removal, watched checkmarks and history. Infinity normal Close **must never require a Trakt account, Trakt network sync, Trakt library scan, Trakt API response or Trakt background service's optional bookkeeping as a prerequisite for completing Infinity's own required save receipts**.

**Do not** disable, uninstall, forcibly update or patch Trakt. The earlier `script.infinity.trakt.rc4patch-0.1.0-TEST.zip` is not part of the approved permanent solution. The existing signed RC4 APK merely changes the notification timing/labels; **it does not implement this policy**.

## Source facts and precise surgical boundary

The native `REQUIRED` list in `InfinityAndroidCheckpoint.cpp` contains **17 categories**, including `python_services` but **not** a dedicated Trakt owner. The currently observed `script.trakt:default.py` is admitted to the generic **unknown Python writer** ledger in `CScriptInvocationManager` because it has no verified persistence contract. `InfinityScriptPersistence::PollInventory()` currently waits for all admitted interpreters before finalizing `python_services`. Deleting a name from the 17-owner array would not solve the observed Trakt blocker.

The intended correction is a **bounded, Trakt-specific optional workload classification** in Infinity's native coordination, not a modification to Trakt or a global bypass of Python writers. Continue sending cooperative Monitor/Stop on normal Close; reject NEW expendable Trakt background reads/scans after Close, without interfering while Infinity is ON or with manual Trakt use. No Trakt optional network task may stall the mandatory Resume Hub/local finalization.

### Non-negotiable safety constraint

Optional **Trakt synchronization** is not mandatory for Infinity's local-first viewed-state receipts; **actual accepted filesystem/SQLite mutations, in-flight scrobbles/watched-state writes and native active-write handles must not be falsely recorded as committed**. A running script's elapsed time, completed cancellation, or absence of a Trakt-specific owner receipt is not proof that outstanding writes are durable. The implementation must distinguish disposable read-only sync from write work, preserve the existing native durability barrier and return explicit failure/recovery if an essential write is genuinely unresolved. No SIGTERM/force-kill workaround, no blanket Trakt network cancellation, no fake `17/17` status.

### Acceptance

- Infinity ON: Trakt optionally usable/updates normally, no change to its files/settings/API, Resume Hub remains independent.
- Close: Trakt **optional read-only background sync** does not gate Infinity's own 17 final owners; any **actual required accepted write** completes or is disclosed, not silently dropped.
- Reopen: Resume Hub positions, watched state, Continue Playing, settings, favourites, add-ons and optional Trakt work remain intact.
- Full-load Fold physical validation required; test real work-in-progress and no-write Trakt scenarios separately.
- Protected locked APK **2103376** and skin **1.0.5.211** unchanged; neither the 2103377 RC4 candidate nor any policy is production locked.

**Decision recorded, not yet implemented in the APK.**
