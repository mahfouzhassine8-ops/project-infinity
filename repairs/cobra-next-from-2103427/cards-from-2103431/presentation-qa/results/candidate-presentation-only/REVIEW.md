# Presentation-only prototype — actual full-tick parity

The selected candidate test passed **15 cases, zero failures and zero errors**.
It reused the preserved twelve-case accepted-431 baseline without rerunning it,
then compared three additional bound-player-progress cases with a separately
executed genuine accepted-431 baseline. This is an unsigned single-method host
prototype, not the integrated projection prototype, an APK or device result.

Independent register-liveness review preceded execution. Fresh disassembly of
the accepted 431 DEX verified the selected preimage and unchanged final writer.
The supplied canonical source changes only `cobraRefreshProgrammeLabels`:
class metadata, fields and **1,801 other methods** are exact. Translation of the
pinned prototype DEX `6354ea6cdc1dfde1745b4463d1e8b17e714ac3a6b52119f597b32c18deab746d`
produced only the Activity overlay. All **4,989 other production class bytes**
and the support JAR remain exact. Input, tool, selected-source and test hashes
are retained in `INPUTS.json` and `OUTCOME.json`.

The comparison uses the original **full tick**, including the player labels;
it does not mistake player text left untouched by a direct mode-details call
for expected full-refresh state. All guide and three player-label text,
visibility, accessibility descriptions, details description, guide progress
and actual bound-player progress/max/visibility match in every case.
`FULL-FINAL-STATE-PARITY.json` records both canonical final-state hashes and the
complete state for each comparison.

| Native fixture invocation | Original 431 | Prototype |
|---|---:|---:|
| Guide Now `setText` | 27 | 15 |
| Guide Next `setText` | 27 | 15 |
| Guide `setProgress` | 17 | 10 |
| Guide `setVisibility` | 27 | 15 |
| Three player-label `setText` | 45 | 45 |
| Bound player `setProgress` | 2 | 2 |
| Guide Next `requestLayout` | 11 | 9 |

These totals cover this fixed mix of **12 active-guard and three fallback
cases**. They are not weighted production frequency, timing, frame-rate or
thermal measurements. The two fewer Next-label layout requests occur in the
current-only programme case; the current-plus-next case remains unchanged.

Both guard-false cases preserve the original single-write preliminary path.
With a valid programme and bound player bar, the original player continuation
still writes progress **500**, proving the reused float-1000 register path is
executed. A nonintegral stop-time offset retains **721 min left**, exercising
the reused 59999L rounding constant; next/empty strings and the time separator
are compared with the original player labels. The fixture uses the actual
feature runtime/default sandbox profile and actual timeline-availability
decision, with no constructed decoder/player or replaced production method.

No Activity lifecycle, screen builder, provider network, Android emulator,
APK/signing, shutdown test or user data operation ran. Pro is disabled in the
other style-string cases; no Pro-Hero rendering or Cards visual-parity claim
follows. The missing approved Cards image remains independent of these native
write-count and final-state findings.
