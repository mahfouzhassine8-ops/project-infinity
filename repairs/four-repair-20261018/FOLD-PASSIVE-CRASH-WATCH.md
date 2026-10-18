# Infinity — Passive Fold Crash Watch (optional physical evidence)

This is an optional read-only diagnostics helper for a Mac connected by USB to the Samsung Fold running One UI 9.0 / Android 17. It captures logs while you use Infinity normally. You **do not need to reproduce the Stop sequence** or deliberately cause a crash.

The tool does not modify Infinity, install an APK or add-on, clear logs, force-stop a process, change a setting, request root, or upload diagnostics. It watches the `com.projectinfinity.kodi:kodi` process, records its observed PID, and saves Android process-exit, crash-buffer and available DropBox/tombstone information if that PID disappears for two consecutive checks **or is immediately replaced by a different PID**. A missing PID is **not automatically a crash**; Android may reclaim background processes. Each capture remains explicitly unclassified until its exit record is reviewed. ADB disconnection never counts as a crash.

## Optional Mac setup

1. Install Android platform tools if not already present: `brew install android-platform-tools`.
2. On the Fold, enable USB debugging and connect it to the Mac. Approve the trust/debugging prompt on the device. `adb devices` should display one authorized device.
3. Run from a Terminal in the folder containing `fold_passive_crash_watch.py`:

```bash
python3 fold_passive_crash_watch.py --out "$HOME/Desktop/Infinity-Fold-Capture-$(date +%Y%m%d-%H%M%S)" --hours 2
```

Now use Infinity normally, including background/foreground return, screensaver and movie browsing. Leave the USB connection and the Mac awake. Press Ctrl+C when done. You can shorten `--hours` or use a maximum of 24 hours. Logcat is kept to the latest **64 MiB** in four 16-MiB segments; extra event snapshots have separate 2-MiB per-command limits.

Only if the engine stops being observed will an `exit-###` folder appear. The output also contains `DEVICE.json` (firmware/package facts) and `TIMELINE.json`. Android permissions may prevent tombstone access; any missing evidence must be reported as unavailable, not as proof of a clean exit. This helper cannot guarantee capturing a fatal-signal backtrace, and it is not a crash fix.

**Privacy:** Keep the output folder private. Logs and Android reports may include account details, media titles, device information or URLs. Review/redact before sharing. Do not publish it in the public GitHub repository.

## Approval gates

No conclusion from this helper authorizes replacing the locked APK **2103384**, disabling Essential-First durability checks, locking experimental **2103386**, or claiming that the October 18 abnormal exit is fixed. The original crash case stays open until a verified native fault or Android exit cause is identified and corrected. The physical Fold remains the final acceptance device.
