# 2103356 Quarantine Probation

Parent: exact 2103355 line `work/infinity-addon-error-quarantine-2103355`.

## Objective

Quarantine must be reversible and must distinguish:

1. a service that merely stopped throwing a visible error;
2. a service that is actually safe to persist user state.

A quarantined service is never considered healthy simply because its popup disappeared.

## Probation flow

A quarantined background `service.py` remains quarantined by default.

Infinity can temporarily grant exactly one monitored probation run when either:

- Command Center / Health Center issues a one-shot `Test again` request; or
- the quarantined service script itself changed on disk, indicating an update/repair.

The quarantine classification remains authoritative while probation runs.

### Runtime result

If the probation run ends with the reviewed clean uncaught-service failure:

- the error toast is suppressed for that probation run;
- the failure is recorded;
- the service returns to quarantine;
- the new service signature is retained.

If the probation run completes without that runtime failure and the exact interpreter receives a durable retirement receipt:

- failures reset to zero;
- quarantine is removed;
- the durable health reason becomes `restored_after_probation`;
- future launches run normally.

If the probation run has any hard persistence uncertainty, including an open SQLite transaction, unflushed buffer, unsupported persistence path, unknown native writer or failed retirement proof:

- the save barrier still fails closed;
- the service is not restored;
- quarantine remains in force for the next process start.

## Health Center / Command Center bridge

Command Center's Crash Recovery / Quarantine menu now exposes:

`Test quarantined service again…`

It writes a durable one-shot request to:

`.android-checkpoint/addon-probation.request`

The native quarantine owner consumes the request only for the exact requested add-on ID.

This request does not remove quarantine. It only allows the next resident service launch to become a monitored probation run.

The direct Command Center action is also available as:

`quarantine-test <addon_id>`

so Kodi Health Center can call the same reviewed bridge without owning native quarantine state itself.

## Quiet probation

During a probation run only, the ordinary Kodi Python error toast is suppressed.

The error itself is still recorded in the persistence/quarantine evidence. This prevents repeated nuisance popups while Health Center is deliberately testing a known noisy service.

## Automatic repair detection

When a quarantined service first becomes suppressed, Infinity records a bounded signature of its service script using file size and modification time.

If that service script changes later, Infinity grants one probation run automatically.

This catches normal add-on updates/repairs. Dependency/authentication/configuration repairs that do not change the service file can still be tested explicitly through Health Center / Command Center.

## Recovery receipt

Successful probation is retained in the quarantine ledger as:

`restored_after_probation`

rather than deleting all history. Health Center can therefore report that a previously noisy service was retested and restored.

## Preservation and safety

2103356 preserves all 2103355 behavior:

- SlyGuy resident service is seeded into quarantine while its shared module remains installed;
- automatic quarantine still requires two consecutive cleanly-retired service failures;
- protected Infinity services remain ineligible for auto-quarantine;
- quarantine never substitutes for SQLite/file durability proof;
- all 2103354 shutdown retirement, background-job ownership and full blocker inventory work remains intact;
- permanent signing and protected APK payload remain required.

Physical Fold testing remains the final authority.
