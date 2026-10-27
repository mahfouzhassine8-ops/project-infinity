# Isolation implementation status

**READY_FOR_FOLD_CHECK — signed 2103421 delivered.**

See [the signed APK, exact hashes and verification receipt](DELIVERY.md).

Codex remains the sole engineering owner. The authorized persistence/barrier
and background-service corrections are implemented. The protected 2103420 lock
and user-accepted release pointer remain unchanged.

- 8,929 actual DEX classes have explicit owners; no direct Infinity/Cobra feature
  calls remain. Each component has its own compiled DEX payload and version.
- All 64,143 original methods are exact after only the enumerated boundary
  substitutions; 311 copied methods retain their original algorithms.
- Fifteen owner-contract cases and thirteen focused production-boundary tests
  passed. No repetitive shutdown cycles or physical acceptance are claimed.
- Independently built component branches passed the actual APK combination
  matrix. Higher-version stale Infinity and stale Cobra, a changed common
  manifest, cross-owner code changes and protected-contract edits were rejected.
- The signing gate checks the latest remote authority, actual packaged hashes,
  current dependency ownership, source-bound evidence, and retired historical
  signing routes before using the permanent key.

See [the data/lifecycle contract](DATA-AND-LIFECYCLE-CONTRACT.md),
[final focused evidence](results/scoped-correction/final), and
[the candidate component authority](release-authority.json). The latter records
engineering review for a candidate, not user acceptance.

The earlier failed gates remain failures. Their evidence and the preceding
implementation status are preserved in
[historical checkpoints](HISTORICAL-IMPLEMENTATION-CHECKPOINTS.md).

The only permitted distribution is the combined original-key APK. Component
ZIPs are build inputs, not separately installed applications. Physical Fold
acceptance remains pending until the signed candidate is delivered and tested.
