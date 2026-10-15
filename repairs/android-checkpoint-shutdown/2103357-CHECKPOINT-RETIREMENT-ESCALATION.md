# 2103357 Checkpoint Retirement Escalation

Parent: exact green 2103356 commit `35120feb9feb96d5f8e8358858083764b1697128`.

## Evidence driving this candidate

Physical Fold diagnostics from 2103356 proved the quarantine/noisy-error policy was no longer the save blocker. Runtime errors were retained as advisory/non-blocking where appropriate, while Normal Close still timed out because foreign Python writers remained alive through the 25-second checkpoint deadline.

Observed lingering writers included Umbrella, POV, The Crew, Redlight, TMDb Helper, Trakt, and Infinity Continuity.

## Objective

Preserve the green 2103356 quarantine/probation behavior and add a bounded retirement escalation path for stubborn foreign Python writers without blocking the application/UI thread and without weakening persistence proof.

## Retirement policy

1. `BeginAndroidCheckpoint()` still closes script admission and sends the existing cooperative Monitor / legacy abort signals.
2. Foreign writers receive a 3-second cooperative grace window.
3. After that grace, still-running foreign writers may be escalated on background worker threads.
4. At most 8 escalations run in parallel.
5. The canonical Command Center resident and the hash-verified compatibility resident are never force-escalated.
6. Verified nonpersistent/reconstructible contracts are not force-escalated by this pass.
7. The application thread never waits on CPython teardown or joins these workers.

## Persistence remains authoritative

Escalation is only a retirement mechanism. It is not a save receipt.

A writer that still has an open transaction, unflushed buffer, unsupported persistence path, missing interpreter retirement receipt, or other hard persistence uncertainty must continue to block Normal Close.

The checkpoint cannot become SAFE while an escalation worker is still active.

## Quarantine isolation

A service that required checkpoint force escalation did not demonstrate a normal clean runtime.

Therefore forced retirement:

- may be recorded as shutdown diagnostic evidence;
- may still record a real runtime failure if one occurred;
- must **not** count as a clean probation success;
- must **not** clear a quarantined/noisy state by itself.

Only a genuine clean monitored probation with durable retirement may produce `restored_after_probation`.

## Diagnostic evidence

Native shutdown trace records:

- `scripts.checkpoint_escalation_start`
- `scripts.checkpoint_escalation_end`
- `scripts.checkpoint_escalated_retired`

with invoker/add-on/script context and whether a durable retirement receipt existed.

## Physical Fold acceptance

Install 2103357 over the current Infinity build, let add-ons fully initialize, then use Normal Close.

PASS requires:

- no UI-thread freeze caused by Python teardown;
- Command Center/compat remain protected;
- stubborn foreign services retire or are explicitly identified;
- Normal Close reaches SAFE only when all persistence owners are durable;
- any genuinely dirty writer still blocks instead of being falsely saved;
- Health Center diagnostics show which add-ons required escalation;
- existing 2103356 quarantine/probation behavior remains intact.

Physical device evidence remains the final authority.
