# Internal Core outcome diagnostic — protected 2103483

This candidate observes the installed Core 1.0.2 implementation. It does not apply the library-path correction, disable Core, change shutdown admission, or certify native drain. The source and native image must match the owner-established hashes in SCOPE.json and the frozen Android selection.

## Evidence recorded

- `core.load.begin`, followed by `core.load.returned` or `core.load.error`: the existing ctypes delegate, actual result or exception, and known Core target. Namespace rejection is reported without raw exception text.
- `operation.begin`, followed by `operation.return` or `operation.error`: correlated `copy2`, `chmod`, `utime`, and `setxattr` calls, their safe targets and before/after metadata. A successful call is not a durability receipt.
- Source-bound native-call progression, exceptions, and assigned start result. The original service discards its stop result, so that result is explicitly unobserved. Running flags, mapped images, or call returns never constitute a verified native drain.
- Read-only maps inspection occurs inside Infinity itself. Only Core mapping counts and executable-mapping presence are emitted; addresses and unrelated mappings are excluded. Incomplete observation remains explicitly incomplete.

Output goes directly to Android logcat under `InfinityCoreQA`. Recording is bounded. No credentials, xattr values, raw exception messages, or unrelated file contents are exported. Other target paths are masked.

## Mac USB capture after the verified QA APK is supplied

Start capture before opening Infinity, using the existing authorized USB connection:

```sh
adb logcat -v threadtime -s InfinityCoreQA:I '*:S' > Infinity-CoreQA.txt
```

After the existing investigation scenario, stop this Mac command with Control-C. Do not clear logcat, uninstall Infinity, reset data, activate another Core path, or change service state. This command collects evidence; it does not authorize or certify a successful Close.

## Verification boundaries

Focused host checks cover delegate/result/exception preservation, metadata semantics, privacy, bounds, and cleanup. Full ARM64 compile/link and exact83 source/ABI preservation are required. The selected pre-sign Android check uses an isolated disposable VM with the original83 APK and only its extracted native engine substituted before first launch. It exercises the original Core failure path and actual local Python, Health Center, and authenticated Command Center operation. This is native runtime verification, not signed APK installation acceptance or physical Fold acceptance.

No successful Core activation or verified native stop is claimed. A signed QA APK is a diagnostic instrument, not the completed shutdown repair.
