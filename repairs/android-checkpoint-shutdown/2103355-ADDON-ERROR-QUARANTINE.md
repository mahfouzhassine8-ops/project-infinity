# 2103355 Add-on Error Quarantine

Parent: exact 2103354 line `work/infinity-save-retirement-job-contracts-2103354`.

Runtime authority: physical Fold diagnostics through `Infinity-Diagnostics-20261009-222247.zip`.

## Objective

Broken or unused background add-ons must not hold Infinity's normal Close hostage merely because they produced an application/runtime error.

The safety rule remains strict:

> An error may become advisory/quarantined only after Infinity proves that invocation has no unresolved persistence obligation.

An open SQLite transaction, unflushed file/buffer, unsupported native persistence path, unknown writer, or any other hard persistence uncertainty continues to block Save Real User State.

## Quarantine behavior

### SlyGuy

The physical Fold repeatedly reports a startup error from `script.module.slyguy`, and the user does not use that background service.

2103355 seeds only the `script.module.slyguy` resident `service.py` into quarantine.

The add-on/module files are NOT uninstalled or deleted. Imports from another dependency can still use the shared SlyGuy Python module. Only the noisy resident service launch is suppressed.

The seed is reversible: it is applied only when no existing quarantine decision is present.

### Automatic quarantine

Other services are not quarantined after one error.

A service receives a strike only when:

1. it terminates with the reviewed advisory `uncaught_script_failure_before_persistence_receipt`; and
2. the persistence observer completes; and
3. the exact interpreter receives a durable retirement receipt.

Two consecutive cleanly-retired uncaught failures quarantine that service.

A clean successful service retirement before the second failure clears the pending strike.

Protected Infinity services are never auto-quarantined:

- `script.infinity.commandcenter`
- `service.infinity.compat`
- `script.kodihealthcenter`
- `service.infinity.continuity`

Only `service.py` launches are eligible. Plugins, user-invoked scripts and shared library imports are not suppressed.

## Close semantics

The quarantine system does not convert hard save failures into success.

The existing Python persistence observer still owns the save verdict. A failed service can become advisory only after all tracked SQLite/file resources have been proven settled.

Quarantined services are not launched on the next startup, therefore they create no new resident writer obligation or repeated add-on error popup.

## Health Center

The Health Center export now includes a bounded `checkpoint/addon-quarantine.tsv` snapshot and an Add-on error quarantine section in `report.txt`.

It reports only:

- add-on ID;
- consecutive failure count;
- quarantine state;
- reason.

No provider credentials, account settings, URLs, tokens or media data are collected.

## Preservation

2103355 preserves all 2103354 save-retirement and job-contract work, including:

- Health Center dir_fd deletion proof;
- exact CPython uuid child environment contract;
- cooperative Monitor + legacy service retirement;
- stock Kodi background-job ownership;
- full blocker inventory;
- pinned Pillow native imports;
- private bytecode-cache handling;
- direct SQLite observation;
- Command Center/compat participants;
- permanent signing and protected APK payload.

Physical Fold testing remains the authority. Success still requires the native coordinator to prove every actual required owner durable before `SAFE_TO_TERMINATE`.
