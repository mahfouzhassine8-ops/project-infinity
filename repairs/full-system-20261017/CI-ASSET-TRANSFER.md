# Infinity CI asset transfer — awaiting the original ZIP upload

This is an experimental integration-test input handoff. It changes no APK,
native library, skin payload, Rails helper, or existing installed user data.

## Exact locally verified bundle

- File: `Infinity-Full-Stack-CI-Inputs-225.zip`
- Size: `59543129` bytes
- SHA-256: `852dce3899b1976556b3b46f696a805b668eca4a513df6194c642d108da58834`
- Contents: original full `skin.infinity.diggz-1.0.5.225-PhaseD-TEST.zip`
  (SHA-256 `8ca8fc72ce24ae88d558d06485345ec37a2cd491ebea5805e169d84acf8ed235`);
  original `script.infinity.rails-0.2.6-Stability-Evidence-RC1-TEST.zip`
  (SHA-256 `5e4ff64592d6f8660d17db1077ed85a368c02f4eb14442760797b1d133c08179`);
  `FULL-STACK-ASSET-SOURCE.json`.

The existing GitHub integration cannot transfer this 59 MB binary directly.
It is **not yet uploaded to GitHub**. No full-stack Android pass may be
claimed before its hash-matched asset is accessible to the workflow.

## Restricted transfer (not a public source commit)

1. GitHub repository: `mahfouzhassine8-ops/project-infinity`.
2. Open **Releases → Draft a new release** while signed in with write access.
3. Tag: `infinity-ci-assets-20261017`; target working branch:
   `work/infinity-full-repair-20261017-gpt6`.
4. Attach the exact bundled ZIP as a binary asset, then select **Save draft**,
   **not Publish release**. Draft releases are intended to remain unpublished.
5. Confirm the private draft upload. The working-branch integration workflow
   `.github/workflows/infinity-complete-full-stack-android.yml` can then be
   triggered with a change to `repairs/full-system-20261017/CI-ASSETS-READY.marker`.
   It downloads this draft asset using the repository-scoped GitHub token
   and rejects it if SHA-256 differs.

A matching artifact from a previous Actions run may be selected with the
optional `assets_run` workflow input instead, but must satisfy the SAME
hash. Do not upload the ZIP to the public repository's source tree.

## Actual Android requirements and remaining limitations

- Signed TEST4 is reference-only, signed TEST3 retains improvements.
- The exact original Infinity skin and Rails ZIP must remain byte-identical.
- The three mandatory skin dependencies are fetched as official Kodi Omega
  add-on **dependency packages**, not as a stock Kodi application. Their
  source provenance/version is logged. This does **not** prove exact Fold
  installed-version parity.
- The original signed Infinity Android package `com.projectinfinity.kodi`,
  native engine, Command Center, startup, full skin selection, Rails,
  Essential-First Power Close and reopen are the application-under-test.
- No code or source-level green result can bypass real Android Close/owner
  durability checks. Existing cold/early failures remain recorded.
- The script rejects physical user devices and cannot substitute for the
  user's physical Galaxy Fold validation.
- Full Diggz profile/provider parity and final APK lock remain separate gates.

**Status:** upload action pending; full-stack Android run unexecuted.
