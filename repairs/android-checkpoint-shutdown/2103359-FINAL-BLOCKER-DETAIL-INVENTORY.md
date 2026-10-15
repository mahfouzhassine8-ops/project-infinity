# 2103359 Final Blocker Detail Inventory

Parent: exact green 2103358 commit `bc56a8699980d2735dc092e738cf3969e03a2ba7`.

## Physical Fold evidence

2103358 proved the prior Redlight retirement/finalization blocker is resolved:

- active Python writers: 0
- pending Python writers: 0
- retired writers: 80
- advisory retired writers: 7

Normal Close now reaches post-retirement durability and fails closed on two later blockers:

1. Python durability: `script_file_identity_or_type_unconfirmed`
2. Add-on settings: `conflicting_loaded_owners`

The 2103358 receipt did not retain the exact file paths for either blocker, so repairing them directly would require guessing.

## Objective

Expose the complete remaining path-level blocker inventory in one physical checkpoint without weakening any persistence rule.

## Python durability inventory

The durability worker now:

- checks every tracked path instead of stopping at the first mismatch;
- retains up to the existing bounded blocker limit;
- records exact path detail for:
  - `script_file_identity_or_type_unconfirmed`
  - `script_file_open_for_durability_failed`
  - `script_file_sync_or_identity_failed`
  - `script_namespace_parent_unconfirmed`
- retains the first detailed path as the primary failure detail;
- remains non-durable if any failure exists.

No missing, wrong-type, linked, unsynced, or identity-mismatched path is accepted.

## Add-on settings inventory

Loaded add-on settings validation now records the exact settings path for:

- `loaded_owner_baseline_unknown`
- `loaded_owner_not_serializable`
- `conflicting_loaded_owners`
- `loaded_owner_save`
- `deleted_settings_reappeared`

The pre-save inventory continues scanning loaded owners so multiple conflicting paths can be reported in one checkpoint. If any ownership/serialization conflict exists, no checkpoint add-on settings write phase begins.

## Regression coverage

The script persistence host test now creates multiple simultaneous path identity/type failures and proves that:

- all are retained;
- each blocker contains its exact path;
- the global checkpoint remains non-durable;
- the primary failure detail is populated.

## Physical Fold acceptance

Install 2103359 and use Normal Close after normal add-on initialization.

This candidate is diagnostic/preservation-first. It is expected to remain fail-closed if real blockers still exist.

PASS for this diagnostic stage means the exported receipt names every exact remaining Python durability path and every exact conflicting add-on settings path in one test, while all previously green owners remain durable.

The next repair must be based on those exact paths rather than broad exceptions.
