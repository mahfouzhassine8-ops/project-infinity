# Actual Kodi renderer harness (test infrastructure only)

This harness runs a prebuilt **Kodi21.3 desktop executable** under Xvfb with Mesa
software OpenGL. PNGs come from Kodi's native `TakeScreenshot` command. They are
not HTML, Pillow or synthesized reconstructions and are not Samsung screenshots.

The fixture is a 364-file subset of verified Skin210. Every included payload has
an SHA-256 in `fixture-manifest.json`, including the original preview XML,
Python controller, fonts, textures and include files. Base64 is transport only.
The decoder verifies the archive and each source file before use.

The disposable test profile deliberately replaces its **test-only** `addon.xml`
(desktop dependencies and canvas size) and `Home.xml` (isolated startup). No
provider, normal Home worker or Infinity service is activated. Those fixture
changes are never copied into the installable skin candidate. The probe opens
the real desktop FileBrowser and injects a native-shaped selected ZIP/nonce
request into its real Window10126 before running the exact preview controller.
The ZIP contains real addon.xml metadata and is never installed or executed.

For the after case, pass the generated candidate delta directory to `--overlay`.
Every overlaid byte and the selected preview/controller hashes are recorded in
each `harness-receipt.json`; compare them with the final candidate ZIP before
presenting the screenshots as candidate evidence.

```
python3 runtime_harness/run.py --out render-evidence --overlay ../delta
```

The window and dp sizes are **declared test inputs**, chosen for narrow, broad,
landscape, split and floating geometries. They are not observed device metrics.
Stock Linux Kodi does not include Infinity's native adaptive-canvas or Android
touch changes. This proves real Kodi XML/control/API rendering and Back cleanup;
it does not prove native376 gesture ownership, Android density, physical Fold
behavior or installation. Original native/controller unit tests remain required.

Source verification: Ubuntu26.04 provides package `2:21.3+dfsg-1ubuntu1`
(`https://packages.ubuntu.com/resolute/kodi`), while Ubuntu24.04 provides20.5.
The workflow runs an Ubuntu26.04 container on a hosted Ubuntu24 runner, installs
the binary package, records `dpkg-query` and fails unless `kodi --version`
reports21.3. It does not compile Kodi. Kodi's upstream supported `KODI_DATA`
variable selects each disposable profile without changing HOME.
