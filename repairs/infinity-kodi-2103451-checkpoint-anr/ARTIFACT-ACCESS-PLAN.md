# Authorized Actions input recovery — no signing or application execution

The latest user continuation explicitly authorizes investigating secure retrieval
through the existing original-key GitHub Actions infrastructure. This preflight
uses its existing actions/download-artifact v4 mechanism with the repository's
standard ephemeral read-only token. It neither changes network restrictions nor
replaces credentials, accesses signing secrets, signs an APK or starts Kodi.

The original combined signer remains unchanged and branch-restricted. A separate
manual/read-only preflight is scoped to this P0 branch and one request file. Its
permissions are contents:read/actions:read. Official checkout/download actions
are pinned to the commits currently resolving their existing v4 tags. No new
dependency, native runtime or Android application execution is selected.

Before every download, require the exact artifact ID/name/run/digest/size and
non-expired state from GitHub metadata. Verify actual signed-451 APK SHA-256,
original certificate, matching owner ZIP hashes and actual retained native SHA.
The historical signed/native assets are source-provenance inputs only; they
cannot substitute for the signed-451 combined foundation.

Reconstruct native source using the exact producer commit of the successful
native build 40287479124, whose output SHA equals the signed-451 native member.
Use the existing full-source reconstruction and nine-file/four-new-file module
producer; compare every resulting file with the downloaded compiled 9411-file
source map before staging the five P0 edits. Refuse any mismatch. Preserve the
unmodified map and emit separate candidate-map/source deltas. No native build
or successor signing is part of this access preflight.

The read-only report must distinguish Actions retrieval from local-client access
and must not claim the local Forbidden response was repaired. A runner using its
already authorized repository token is an authorized service operation, not a
proxy bypass. If Actions also denies access, retain that actual error and stop;
do not seek alternate credentials or public copies.

## Selected checks before execution

```
PYTHONDONTWRITEBYTECODE=1 python3 repairs/infinity-kodi-2103451-checkpoint-anr/test_artifact_preflight.py
```

Only metadata identity/fail-closed checks, public certificate-pin parsing and
workflow permission/routing checks are selected. Do not repeat the 14 watched
and 7 lifecycle host cases unless the restored source binding differs.

Request one Actions run through ARTIFACT-PREFLIGHT-REQUEST.json after these local
checks pass. The job verifies/reconstructs artifacts, records current runner
capabilities, and exports provenance/source maps for subsequent authorized work.
No signing secrets or private diagnostic archive may be uploaded in its report.
The historical watched-job item route remains UNKNOWN until actual evidence or
a supported runtime observation identifies it; source recovery does not supply
that missing event attribution.
