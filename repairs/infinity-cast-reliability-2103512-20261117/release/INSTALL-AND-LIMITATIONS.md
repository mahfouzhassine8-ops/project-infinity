# Infinity 2103514 — Cast reliability QA

Install the original-signed QA over the existing application. Do not uninstall or clear data. Infinity 2103512 and the historical protected releases remain preserved; this candidate is not automatically accepted.

One Fold/receiver acceptance session:

1. Play the provider movie, select Onn 4K, and confirm sustained television video and sound through several fragments. Exercise pause/resume and a distant seek.
2. Repeat on Nest Hub Max. Check the 720p hardware path, synchronization and sustained delivery. Codec, thermal, read and resource guards remain enforced.
3. Use Return to Phone, then check position, local controls and Continue Watching. Check cancellation and disconnect after an interrupted transfer.
4. Perform normal Exit and same-profile relaunch. Confirm existing settings/add-ons/data and Cobra remain intact.

Engineering checks passed for complete 14 MB resources, authenticated HTTP/ranges, target prebuffer ownership, coalesced seeks, native cancellation, source video timestamps and the canonical AAC sample clock. The Kodi engine was reused unchanged. Tests used actual ARM64/JNI and Android MediaCodec/EGL with explicitly bounded CI media; they do not qualify physical Fold Main10 throughput, thermal behavior or television playback.

The prior receiver error 310 does not identify its decoder cause. Source-read planning, output limits and missing initialization parameters were independently reproduced. A new internal-fragment clock issue was caught and corrected before signing. Actual receiver acceptance remains pending.

Forward recovery 2103515 restores signed2103512 content with a higher version code, retaining the original signer and install-over compatibility. It does not reset user data.
