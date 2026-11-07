# Infinity Search — native-provider-owned completed-result policy

**Isolated implementation candidate; not an installed update or APK.**
Candidate parent: `c75e6de691cc6263236d778cd16b50573e7eb348`.
Protected baseline: `86d5b5e2b65acb878632d407c3a3a07dd1af3b6d`.

## Existing functionality preserved
User enters one query through the existing Infinity Search UI. `search-all`
asks all currently enabled compatible providers to execute their own verified
native plugin-search URLs through the bounded `Files.GetDirectory` lease.
`search-provider` uses the same publisher for a selected provider.
The source, provider heading, original provider URI, and child URI semantics
remain unchanged. No parallel homegrown search engine, new provider adapter,
background provider invocation, retry loop, extra screen, or changed native
provider source.

## Correction
The previous response guard treated **settings file metadata** (inode/size/
mtime/ctime) as if it proved a native provider's freshly returned rows were
invalid. The user trace shows that it discarded 31 Nixtoons and 2 Crew rows.

The candidate changes one shared function, `_provider_result`: when a *fresh
request* really completed in the owning installed native provider, settings
files may change while that provider performs its own search. If **all**
changed response components belong to provider/dependency settings metadata,
keep the newly completed answer and its **original provider URIs**. A
completed result represents the provider's observed request, not a promise
that its settings are immutable across execution.

A cache hit is **not** freshly completed and retains strict full-file settings
revision binding; no cache hit gains this exemption. A freshly completed
answer is **not cached** if settings changed, preventing silent stale reuse.

**Preserved unchanged:** before/after verified route and enabled status,
source/dependency pins and manifest metadata, current app/skin/profile
identity, native worker and cancellation ownership, status/error handling,
response size/time limits, cross-provider failure isolation, and publication.

## Honest consistency boundary
This design intentionally delegates meaning of the provider's own settings
writes to that provider. A meaningful setting flip or A→B→A inside the native
request is *not* independently journaled or rejected by Infinity. Neither the
prior metadata-only validator nor this policy can prove a coherent immutable
provider settings snapshot; a complete native mutation journal would be
required for that stronger guarantee. A fresh provider-owned response can
therefore reflect the provider's transient settings. Re-running the search
uses the current settings.

This is a **deliberate product contract choice**, not evidence that meaningful
settings changes are harmless. It differs from the unimplemented strict
native-ABA-consistency release gate recorded in
`SEARCH-CONSISTENCY-NATIVE-CONTRACT-20261107.md`. Do not silently mark that
older gate as PASSED. The user must be accurately told the tradeoff if
this candidate is approved for production.

## Minimum acceptance

- Fresh native response with provider search-history/timing file writes:
  publish original 31/2 synthetic rows without a duplicate RPC.
- Fresh response with both provider and dependency settings updates: accept
  only when other source/profile/route checks hold.
- Native source/manifest/dependency file change, missing or linked settings
  state, profile change, disabled provider, changed route, cancellation,
  native errors and lease conflict: original refusal behavior.
- Cache hit with changed settings: reject; do not blindly reuse.
- Do not put settings-mutating fresh answers into the cache.
- Search All and selected provider route share one original publisher.
- Run source guard regression, host matrix, complete integration, original
  signer/recovery verification, then one actual Fold acceptance.
- Preserve all Cobra, Preview, Infinity locked UI, playback, settings,
  skin, third-party providers, touch, keyboard and graphics source.

**Status:** only source + host evidence. Not an APK, signed package,
native Search runtime proof, or phone-tested fix. No production promotion
until original-source bounds and all relevant tests are checked.
