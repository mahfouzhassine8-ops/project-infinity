# Selected actual-installer checks for the new authenticated80 pair

Selection recorded before execution. Run only after both complete80 manifests
receive original-key detached signatures through the existing authorized owner
workflow. No local signing, APK/native build, device, application or shutdown
execution is selected. The unchanged Java installer is compiled only into a
temporary host test directory with its original Android API transport fixtures.

The changed signed inputs justify these thirteen focused cases:

1. Signed CC64 (APK66) upgrades to CC66, installing all80 exact sources and retaining data.
2. The same CC66 is a byte-for-byte no-op.
3. CC66 advances to CC67 recovery: every baseline66 functional module byte returns, the same helper remains authenticated and inactive, and user/unknown files remain.
4. Older CC66 retains a complete authenticated CC67 without writes.
5. Older CC66 refuses a newer authenticated CC67 whose helper is missing, without writes.
6. A loose unknown helper on baselineCC64 refuses upgrade without writes.
7. A missing installed signature refuses upgrade without writes.
8. An unmatched partial installed signature refuses upgrade without writes.
9. Exact known candidate partial hub/helper writes resume safely from signed CC64.
10. A tampered installed CC66 helper refuses recovery without writes.
11. A tampered packaged helper refuses without writes.
12. A missing packaged helper refuses without writes.
13. A tampered packaged signature refuses without writes.

Missing packaged helper and incomplete newer-generation cases are refusal
contracts. A missing installed same-generation source may be repaired by the
original resumable installer and is not falsely required to refuse.

Reuse the historical ten-case installer evidence at
`repairs/infinity-three-corrections-20261108/evidence/MODULE-UPGRADE-RECOVERY.json`;
do not rerun that old suite. Pin its original helper and generated Java/transport
hashes in the new report. The seventeen host projection cases also remain reused.

Invocation: `python verify_modules.py --prepared STAGED_PAIR --out FRESH_AUDIT_DIR`.
Preparation/installer checks do not establish native or Android behavior, signer
admission, installation acceptance, or physical Fold acceptance.
