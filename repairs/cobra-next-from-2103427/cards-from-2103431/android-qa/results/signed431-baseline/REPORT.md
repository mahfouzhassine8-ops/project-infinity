# Exact signed431 Cards baseline — run41001477356

The single selected run failed at UI observation after the normal source-save press. It did not establish Cards performance.

| Observation | Actual result |
|---|---|
| APK/signing | Original v1/v2/v3 signature and exact installed431 SHA256 verified. |
| Cold Cobra launch | One `am start -W` sample: TotalTime3148ms, WaitTime3245ms, COLD. Welcome observed after13.07s including native compatibility-notice/accessibility overhead; this is not first-frame latency or chooser transition. |
| Normal source form | All3 real fields filled; TEST&SAVE coordinate[878,884] lies in actual[736,813][1020,955] button. No IME obstruction observed. |
| Local provider | HTTP200 returned for20,226-channel M3U, XMLTV and syntheticqa1 stream. Decoder initialization appears in retained log. |
| Last successful hierarchy | 010 still shows the M3U form while validation begins. |
| First failing operation | Next `uiautomator dump` produced no fresh011XML although the command returned without error; `adb cat` then failed. The harness discarded dump stdout/stderr, so idle versus missing-root cause cannot be determined. |
| App state/crash evidence | Terminal Activity remains Cobra resumed/visible. Retained log has no FATAL EXCEPTION, Fatal signal, ANR, SIGBUS, SIGSEGV or OOM marker. This does not prove long-running stability. The skipped-frame warning belongs to the IME process, not Cobra. |
| Cards/warm/scroll/resources | Not reached; no first-card, warm-return, scrolling or finite new-scope resource result. |
| Terminal image | Missing: original finalizer tried hierarchy first; its failure skipped screenshot. Only cold Welcome and compatibility-notice images exist privately. |

The exact official artifact ZIP SHA256 is e3fb4da737ebd7ca7a7ca6c815c8fb65857a71dbf956486e45491ed24ce137da; EVIDENCE.json records every extracted file hash. This is a harness-observation failure after import started, not a demonstrated application crash or native defect. No rerun, app change, native change, shutdown test or physical Fold acceptance occurred.
