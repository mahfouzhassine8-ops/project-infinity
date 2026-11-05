# Original-key signing gates passed; physical acceptance pending

The original sole-signer workflow issued testing APK **2103458** in run
[42108276626](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42108276626)
and higher-version forward recovery **2103459** in run
[42112995114](https://github.com/mahfouzhassine8-ops/project-infinity/actions/runs/42112995114).
Both runs passed the original pre-key authority, source, payload ownership,
original-certificate and exact-member gates. Both actual signed APK archives and
both matching component archives were subsequently downloaded, CRC/hash checked,
and compared with the official signed authorities. See [delivery evidence](DELIVERY.md).

The initial 456/457 preflight correctly refused the new source. That historical
rejection was resolved by a distinct, exact 458/459 registration under the user's
controlled-testing authorization, through the same original signing workflow.
Preparation 42106024906 and official artifact review 42107607016 passed before
registration. No old authority was reused for changed bytes. The signing key,
security-policy algorithm, module/installer verifier, durability safeguards and
accepted pointer remain unchanged. The configuration/routing changes are recorded
in the source history and the 11 focused packaging contracts.

2103458 preserves the exact delivered 2103456 native engine and all five DEX
files. Recovery 2103459 restores frozen 2103451 functional code with higher
authenticated module/skin generations. The original-key host recovery checks
passed; actual Android installation and recovery are **NOT RUN**. Existing 2103457
cannot be used to recover a higher 2103458 installation.

The two required Search failures remain FAIL. Favorites attribution and universal
browser/Fold acceptance remain unresolved. No signing success changes those
results. The installed Fold version is UNVERIFIED. Neither build was installed,
accepted, promoted or locked.
