# Search policy release review — November 7, 2026

Reviewed candidate: `776e2e46006129b603275119bc3643021790456f`.
Scoped correction: `8f51c0415c8a96ffc1ae3d8c3c9e1d7ac92a9a75`.

The candidate implements a native-provider-owned response contract. It does
not implement an immutable settings snapshot or a complete mutation journal.
Fresh successful native results may reflect meaningful provider/dependency
configuration changes, including intermediate A→B→A changes. Those changes
are deliberately accepted under this contract. This review does not classify
the observed Crew/Nixtoons writes as harmless or identify their actual writer.

Original route, enabled-provider, pinned source/dependency, manifest, profile,
native lease, cancellation, result-publication and size controls remain in
place. A settings-mutating fresh response is not put into the cache. Cached
responses retain the original whole-signature validation. Every provider uses
the same rule; no provider source or provider-specific exception is added.

The review found an uncovered discrepancy: deleting an existing settings file
while a request completed still published 31 synthetic rows, whereas the
minimum-acceptance text implied missing state would refuse publication.
`PRECORRECTION-SEARCH-COUNTEREXAMPLE.json` retains that actual observation.

The correction records only settings-file existence bits from the exact stamps
already collected by `_query_signature`. It rejects disappearance of any
previously existing provider/dependency settings file, even when another
dependency creates its file concurrently. Creation of initially absent
settings remains valid initialization, and a file that is absent throughout
may still represent valid provider defaults. This adds no filesystem reread,
settings parser, RPC, provider modification, or settings/cache write.

The original returned signature identity is unchanged. An independent complete
AST comparison confirms `_query_signature` is identical after removing only
the new same-snapshot existence assignment. Relative to the integrated parent,
the only changed runtime functions are `_query_signature` and `_provider_result`.

The full selected 28 host cases passed in
[run 42422768029](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42422768029).
They include the original 24 contracts plus disappearance, first creation,
unchanged absence and dependency disappearance/creation exchange cases.
The 31/2 row counts in these tests are synthetic fixtures. They are not new
live-provider Android evidence.

The earlier local attempt recorded 26 passing cases and two socket-related
failures because the local sandbox denied AF_UNIX socket creation. The actual
GitHub host then ran all 28 cases successfully, without mocking or removing
the modal ownership primitive. That local failure remains recorded in
`SEARCH-REVIEW-SELECTION.json`.

Production promotion remains blocked by the mandatory coordinated runtime and
release gates. The stronger historical requirement to independently refuse all
meaningful settings/ABA changes is not PASSED by this implementation. If that
stronger contract is required, this candidate does not satisfy it; changing
the wording cannot establish such consistency.
