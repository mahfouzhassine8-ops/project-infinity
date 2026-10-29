# Consolidated candidate431 — final signing pending

**Do not install unaccepted2103430.** Its original-key signing and payload checks passed, but the new light adaptive icon failed actual native drawable inflation with a density override. It is superseded before delivery and has not been accepted or promoted.

Final2103431 retains both P0 corrections and all2103429 work. The light background now uses a nested white shape. Original dark assets, existing resource table/IDs, five light density PNGs, Infinity2103427, shared executable/native/manifest/non-icon payloads, chooser behavior and shutdown remain frozen. The button implementation remains byte-identical to430; only genuine component version metadata advances.

Actual host Android resource inflation now passes for default/420density, normal/round icons and day/night, including exact baseline dark rendered pixels. Signed430's density failure is retained as a required negative control. The final CI producer, original-key signing, exact component verification and Android UI evidence will be linked after completion. No phone installation or lock promotion occurred.
