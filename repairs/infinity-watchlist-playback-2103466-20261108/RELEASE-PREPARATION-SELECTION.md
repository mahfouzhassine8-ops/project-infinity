# Selected preparation integrity checks

Scope: release preparation tooling only. No application, CI, compilation,
signing, installation, shutdown, or repeated host behavior tests are selected.

Before execution, select one read-only `prepare_release.py inventory` against
the retained original-signed 2103466 APK and official prepared 2103466 bundle.
It checks the APK hash, complete owner bundle inventory, original DEX bytes,
typed Android version metadata, native466 bytes, unchanged Trakt version,
all 79 authenticated first-party source records, original public-key module
signature, and exact retained INSTALL-BASELINE.v1 preimages. Extraction uses a
disposable temporary directory. Write its report to contract-evidence only.

Reuse HOST-PROJECTION-RESULT.json's seventeen existing cases as historical
evidence; this preparation does not rerun or relabel them as Android acceptance.
Inputs/finish remain unexecuted until root confirms the live unused version pair,
freezes all Python/native source hashes, and obtains the matching ARM64 artifact.
