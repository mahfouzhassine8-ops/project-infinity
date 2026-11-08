# Conditional two-file invocation observation scope

Independent source-only Astra review, 2026-11-08. This addendum narrows the open
invocation-binding question in `CONTRACTS.md`; it does not authorize or implement
production edits. No tests, native compilation, application execution, signing or
installation were performed. `contract-evidence/INVOCATION-SCOPE-HASHES.json`
binds all eleven supporting files to the retained signed-466 native source map;
all eleven hashes match.

## Verdict and proposed approval boundary

Exactly two additional production files form a concrete, conditional candidate
for closing the observed POV fresh-item gap:

1. `xbmc/interfaces/generic/ScriptInvocationManager.cpp`: observe the actual
   dispatched invoker ID immediately before both existing `Execute` calls.
2. `xbmc/interfaces/legacy/Player.cpp`: observe that same Python invoker when
   `playStream` copies the provider's new ListItem into the media-play message.

Both are outside the current seven-file authorization. Approval of this narrow
scope would permit implementing and evaluating the candidate, not certify its
correctness or remove the separate metadata/runtime gates. The existing approved
saved-navigation state/header and PluginDirectory/PlayerOperations files can own
the protocol. Source inspection demonstrates no current need to edit ScriptRunner,
LanguageHook, PythonInvoker, GUI, player callbacks, shutdown, or provider files.
This is not proof that every provider playlist/reentrant launch mode is covered.

## Source-backed data flow

`PluginDirectory.cpp:70-100` synchronously enters `RunScript` after selecting the
actual addon. An allowed change can establish an exception-safe, bounded TLS
resolver context around that call, only for verified Watchlist lineage.
`ScriptRunner.cpp:129-159` builds argv from the actual plugin URL, handle, query
and resume flag, then synchronously calls the invocation manager. Thus the
dispatch observer can compare the selected addon, script, complete arguments and
plugin handle against that TLS context without changing ScriptRunner or waiting
for its returned private script ID. The TLS context must be cleared/restored on
every return and must not accidentally authorize nested unrelated dispatch.

`ScriptInvocationManager.cpp:935-953` has the reused invoker's ID before its
`Execute` at 951. The new path assigns the ID at 963, registers the thread at
966-968, and has the same ID before `Execute` at 978. A bounded observation at
both sites can therefore publish the exact ID-to-origin receipt before Python
can make its player call. It must replace or clear that invoker's old association
on every observed dispatch, including ordinary non-Watchlist reuse. Recording a
dispatch is not permission to bypass any existing admission decision.

`LanguageInvokerThread.cpp:128` transfers that ID into the language invoker before
`Process` executes Python at 148. `PythonInvoker.cpp:1117` exposes the ID through
the interpreter's `__xbmcinvokerid__`; `LanguageHook.cpp:160-180` reads it.
`LanguageHook.cpp:119-138` similarly reads the addon ID. These existing virtual
methods are accessible without editing LanguageHook. They read Python objects,
so the values must be captured before `Player.cpp:92` constructs
`DelayedCallGuard`, which releases the GIL.

`Player.cpp:89-105` can then use the captured plain native values to validate a
bounded receipt and annotate only the fresh CFileItem copy destined for
`TMSG_MEDIA_PLAY`. Do not mutate the provider's original ListItem with origin
properties. Require matching provider, exact invoker registration, one-use nonce,
current Watchlist generation, reviewed typed media identity, profile and skin.
Missing/mismatched/expired/replayed provenance leaves the original playback path
and item semantics unchanged. This is first-party control-flow provenance, not
a security boundary against arbitrary malicious Python mutation of globals.

## Reuse, concurrency and lock-order requirements

- Reuse is not inferred from addon ID. `LanguageInvokerThread.h:34-36` requires
  `InvokerStateScriptDone` and the same script. The manager checks this at
  840-845. On successful execution, `PythonInvoker.cpp:577-654` waits for other
  interpreter thread states, clears pending calls and releases the GIL before
  publishing `ScriptDone`. This supports the proposed reuse handoff; the new
  observer must not weaken or change those lifecycle rules.
- The manager already holds `m_critSection` across both dispatch calls. An
  observer using the existing correlation mutex adds the order
  `manager m_critSection -> correlation mutex`. That order must be strictly
  one-way: no correlation-state operation may call back into the manager, GUI,
  Python, service broker, RPC or provider. Release the correlation mutex before
  the existing `Execute` call; never retain it across execution, waits or joins.
- In `playStream`, capture Python identity while the GIL is held, then release
  the GIL through the existing guard before correlation-state access. Do not
  call the Python getters while holding that state mutex. Profile/skin checks
  must use safely obtained snapshots or explicit generation validity, never
  GUI calls under the state mutex. No new lock or shutdown hook is proposed.
- Use bounded storage and fail-closed observer operations that cannot change
  existing dispatch return values, admission, quarantine, checkpoint ledgers,
  exceptions or player message delivery. Inspect actual getter failure handling
  and allocation/exception behavior during implementation review; an observer
  failure must not turn ordinary playback into an exception.
- Registration before `Execute` does not prove successful execution. Failed or
  cancelled dispatch, superseded generation, provider resolution failure,
  recovery retry and expiry must invalidate or make the receipt unconsumable.
  Consume only on the matching actual-item handoff; no playback progress is
  recorded until the existing AV-start path qualifies it.
- Matching invoker ID plus addon is necessary but not sufficient: retain the
  original route/handle/arguments binding and exact typed identity. A new child
  interpreter, plugin reentry or playlist call without that binding must remain
  unsupported, rather than inherit the last title's provenance.

## Acceptance remains conditional

The two observation sites remove the identified private-ScriptRunner-result-ID
race from the candidate design. They have not been implemented, compiled or
runtime tested. Review must still establish bounded memory/lifetime, cancellation
ordering, concurrent same-provider launches, new and reused invokers, ordinary
same-title launches, replay rejection and unchanged playback on every mismatch.
The separate complete-catalogue source/version checks and nonblocking acquisition
timing in `CONTRACTS.md` remain unresolved. Existing seventeen host projection
tests do not cover these native requirements and were not rerun for this review.
