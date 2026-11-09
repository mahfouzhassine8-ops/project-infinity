# Selected tracking module installer host contract

Status: NOT RUN. Execution requires root's confirmed version admission and both
complete module manifests signed by the existing original key. Prospective
version numbers are not reserved by this document or tool.

Selected command, only after signed modules exist:

`python verify_tracking_modules.py --prepared <prepared-pair> --out <fresh-host-output>`

The prepared layout follows `prepare_tracking_release.py`: exact signed69
`baseline-modules/`, `SOURCE-PINS.json`, `VERSION-ADMISSION.json`, and
`<admitted-versionCode>/{INPUTS.json,modules/}` for each member of the pair.
Before importing a producer, verify original generator, template, composition
plan, public key, host Java adapters and retained verifier/evidence against
immutable original69 source `a76e29b84996304241e6b309d56a31e6659ad190`.

Before compiling or executing the unchanged Java installer, verify the original
public-key signatures and complete80-file payloads of baseline, candidate and
recovery. Candidate changes exactly plugin.py, resume_hub.py, service.py and CC
version metadata. Recovery restores all original69 functional source bytes with
forward CC metadata. The authenticated inactive saved_playback.py stays unchanged.

Execute exactly these thirteen changed-input cases:

1. Signed69 to admitted candidate installs all80 authenticated sources and preserves data.
2. Same candidate is an idempotent no-write invocation.
3. Forward recovery restores exact69 functional80 sources and preserves data.
4. Older candidate retains the authenticated newer recovery without writing.
5. Older candidate refuses an incomplete newer recovery, retaining every byte.
6. Unknown installed tracking source is refused without writes.
7. Missing installed signature is refused without writes.
8. Mismatched partial signature is refused without writes.
9. Known signed partial replacement of the three tracking sources resumes safely.
10. Tampered packaged tracking source is refused without writes.
11. Tampered packaged signature is refused without writes.
12. Original69/CC67 packaged assets retain the complete signed tracking generation without writes.
13. Original69/CC67 packaged assets refuse an incomplete newer tracking generation without writes.

Cases12–13 were selected before execution after Astra identified the specific
original69 restart path required by the internal authenticated module fixture.

Settings, tracking state, a database byte sentinel, unrelated provider code and
unknown files exist only inside disposable temporary fixtures. Positive cases
compare their bytes; every refusal compares the entire fixture tree. Java calls
have finite timeouts. No real profile, provider, database or settings are opened.

The existing thirteen-case80-file installer evidence is retained and hashed as
historical evidence; this selection does not rerun that suite. Results will be
written to `MODULE-UPGRADE-RECOVERY.json` only after actual execution. This is a
host installer contract, not Android playback, APK installation, native build,
signing, Fold acceptance, release acceptance or shutdown verification.
