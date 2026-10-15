# Locked 2103304 native shutdown audit copies

These two C++ files are exact recovered copies of the locked engine's source,
not native modifications and not inputs to a replacement build. They are stored
outside `xbmc/` so the existing build source and locked baselines remain intact.
See `docs/Infinity-2103305-Close-Power-Audit.md` for provenance and limitations.

With the unexpired native artifact from run 37189319805 extracted locally:

```sh
python3 audits/2103305-native-shutdown/verify.py \
  --manifest /path/to/engine3304/source-manifest.json \
  --engine /path/to/engine3304/libkodi.so
```

Verification is read-only and fails closed on any unexpected source, manifest or
library hash. It proves source ownership and evidence identity, not successful
device shutdown, crash resolution or completion of the repair brief.
