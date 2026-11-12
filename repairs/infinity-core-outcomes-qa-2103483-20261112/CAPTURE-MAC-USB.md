Use the existing authorized USB connection and your existing `adb` installation. This helper requires only Python3’s standard library and `adb`.

```sh
python3 capture_mac_usb.py --duration 900 --out "$HOME/Desktop/Infinity-Close-Capture"
```

If more than one transport is listed, add `--serial YOUR_USB_SERIAL`. The output directory must be new.

After installing the supplied QA APK, choose Done rather than Open. Start this command before opening Infinity. Wait for **READY**, then open Infinity yourself and perform **one** existing Close attempt. After its outcome is visible, press **Control-C on the Mac**. Final read-only receipt collection may take up to the remaining reserved minute. The helper does not start, close, stop, or change the app. The complete time budget is at most30minutes.

The folder contains:

- `android-logcat.txt` and `InfinityCoreQA-native.jsonl`: actual Android diagnostic messages. Host summaries are never inserted into Android logcat.
- `PROCESS-SNAPSHOTS.jsonl`: bounded observations of the exact Kodi process. `PROCESS-SUMMARY.json` includes the final observation; PID changes or absence do not prove clean persistence.
- `RECEIPTS-BEFORE.json`, `RECEIPTS-AFTER.json` and their raw JSON files: the two known coordinator receipts and at most two safe session-derived `CHECKPOINT_FAILED` receipts per phase. `android_receipt_fields.last_native_status` carries the existing native reason when readable.
- `SUMMARY.json`: unchanged prior receipts are explicitly marked stale for this capture. Changed or first-observed receipts are not automatically treated as successful Close evidence.

Denied, missing, oversized or malformed receipt reads are recorded explicitly. No root, run-as, permission changes, directory walks, maps reads, log clearing or device writes are attempted. Successful recording is not successful Close acceptance.
