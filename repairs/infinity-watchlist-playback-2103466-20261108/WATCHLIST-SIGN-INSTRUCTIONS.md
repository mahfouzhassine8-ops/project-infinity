# Root integration instructions — fragment only, not executed

`WATCHLIST-SIGN-JOB.yml` is a proposed job entry for the existing sole combined
workflow's `jobs:` map. This task did not change any workflow, registry, signer,
gate, preparation implementation or runtime source. No signing or workflow ran.

Root should append the fragment to `.github/workflows/infinity-combined-release.yml`
and add `sign-watchlist` to its existing manual operation choices. Keep the sole
workflow ID/branch and unchanged original-key secret route. This is internal QA
only: artifact upload does not publish a release or update an accepted pointer.

Before committing the official preparation source, settle these exact paths and
then freeze them so `register_release.bindings()` source equality remains true:

- `RELEASE-REQUEST.json`: operation `sign-watchlist-internal-QA`, integer `version`
  2103468 or 2103469, `publication: false`. The job maps them to generations 55
  and 56 and requires the actual registered authority already matches the pair.
- `PREPARED-PAIR-REQUEST.json`: existing `register_release.request_data()` schema:
  integer `run_id`, full `source_commit`, `artifacts` keyed by both versions with
  exactly `id`, `name`, `digest` (`sha256:...`), `size_in_bytes`, and
  `module_audit_sha256`. Fill only after successful official preparation.
- `evidence/MODULE-UPGRADE-RECOVERY.json`: commit the exact actual 13-case Java
  module upgrade/recovery audit produced by official preparation; its hash must
  equal the pair request. If root uses another path, update both fragment audit
  arguments and the preflight path before freezing the preparation source.

Do not mutate the already prepared runtime/evidence/tool sources after official
preparation: `register_release.check_registered` recomputes all source bindings
and the reviewed authority proposal. Request/authority/workflow commits follow
the existing registration sequence; no proposal from this fragment changes them.
Register/sign 68 first, then review/register/sign the same pair's forward recovery
69 using the existing authority transition. Never reuse an issued version.

The job downloads baseline 66 only from artifact 13609794621/run 42462319257.
It verifies the exact requested official prepared archive's GitHub metadata,
whole SHA, byte count, safe ZIP names/links and extracted member correspondence
through the unchanged registration helper. The archive stays beside its extracted
version directory as required by that helper. Tools come only from immutable run
39867073954 at `tools/receipt-evidence/tool-jars`; existing release-gate pinning
checks the actual jars before keys. No replacement tools or signer exist here.

The signing order is the existing sign-three pattern: sole signer policy → exact
official registration → original combine → frozen unsigned SHA → complete
baseline-member comparison → unchanged release_gate → existing secrets scoped
only to unchanged assemble.py sign → exact signed-member/original-cert comparison
→ internal QA upload. The unchanged assembler independently rechecks the gate,
remote authority and payload before/after original signing. Failure before the
final comparison prevents the installable QA upload; failure evidence is retained.

The unchanged assembler creates `signed-combined/BUILD-RECEIPT.json`, including
its existing source/version/generation/unsigned and signed digest fields, plus
`SIGNATURE.txt` and `SHA256SUMS`. The fragment uploads that directory intact and
does not rewrite or replace this known receipt. Native/Android consumers should
continue reading the original assembler receipt convention. Root's canonical
authority 67 sync, then 68 and 69 registration remain separate commits so each
unchanged transition can recover its real predecessor and expected-head pointer.

Review the YAML and embedded Python statically before append. This draft does
not run behavioral suites, Android, shutdown, application tests, builds or signer
commands. Root owns integration, official registration and authorized execution.
