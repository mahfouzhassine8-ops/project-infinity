# Native keyboard/scaling source review — owner-authorized 2026-11-07

Isolated branch from protected86d5b5e2. Search candidate72fefa8f and both existing branches remain untouched.
Reuse existing native input restoration and existing native workflow; add only a branch-specific source-review job.
Scope: restore signed451 inputs + existing touch/navigation/Downloads to the exact compiled APK4629411-file source map. Inspect selected keyboard callback/dialog, graphics origin-stack and Android touch ownership.
Selected verification: input metadata/digests, exact full source map, original source helper reuse and unchanged protected runtime sources. No repeated Search tests, symbolication or physical reproduction.
No native patch, compile, APK, original signer access, shutdown suite or application execution in this first job.
Choose a native correction only after the matching source establishes its cause. User scope permits subsequent focused proof and real ARM64 compilation; this stage is read-only preparation.
