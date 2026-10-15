# Infinity 2103374 / Skin 208 / Health Center 2.5.20 packaging RC1 — locked baseline

User instruction on 2026-10-12 (America/Detroit): **“lock and use as bace”**.

These three delivered packages are now the user-approved bases for future work. The exact hashes, source commits, signer, branch names, checks and rollback identities are recorded in [Infinity-2103374-Skin208-Health2520-PackagingRC1-LOCK.json](Infinity-2103374-Skin208-Health2520-PackagingRC1-LOCK.json).

| Component | New base | Build/source commit |
|---|---|---|
| Cobra APK | 2103374 · Verified Deadweight RC1 | `9c3af2e9271402486c4c998efc62b5d08b872f29` |
| Infinity Skin | `skin.infinity.diggz` 1.0.5.208 | `38d916bb885fe434f923bb951e605e65ff1fb34f` |
| Health Center | 2.5.20 · Packaging Cleanup RC1 | `ccbcfc3d41fc015f711da92d9745d34f21d46cc7` |

Future APK work starts from `locked-cobra-2103374-verified-deadweight-user-approved-20261012`; skin and Health Center work start from their separately pinned lock branches listed in the JSON. The APK lock contains this documentation-only commit atop the exact green build commit. Component branches are separate source lineages and must not be treated as one merged runtime tree.

Cobra 2103373, skin 207 and the original Health Center 2.5.20 package remain preserved for rollback. Health Center's runtime version remains 2.5.20, so use the exact package filename and checksum to identify the new packaging base.

All recorded automated tests and package preservation checks passed. This lock records the user's acceptance; no physical device tests or full provider acceptance were performed by the assistant. Legacy Live TV and active optional Pro score overlays are retained, with the unresolved dependency/policy details documented in the delivered implementation report.

The previously delivered candidate-only reports remain historical evidence. This explicit lock record supersedes their no-lock status. No package was rebuilt, re-signed, repackaged, installed or merged into the default branch for this lock.
