# Exact RC22 rollback

Protected-by-workflow-convention source: `locked-infinity-cobra-2103242-onn4kpro-tv-final-product-audit-passed`.

Commit: `f95e84676932470ec6093bf6408a920d40239702`.

APK: `Infinity-1.0.9-Cobra-Onn4KPro-TV-Final-Product-Audit-RC22.apk`.

SHA-256: `2e0480ae719a319125ad9482840439e3e8406fe47c8181424469a719b44b9754`.

Original successful workflow: `36022909060`; original candidate artifact: `10818415852`.

Permanent signer SHA-256: `d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7`.

Package: `com.projectinfinity.kodi`; version code 2103242; ARMv7.

The audit-source snapshot contains the exact baseline repository archive, reconstructed Android sources and hash inventories. It was produced by workflow `36024863257`, artifact `10819611742`.

The RC23 workflow separately preserves the actual original RC22 APK as a rollback artifact. It never writes the locked branch. Naming a branch locked is not a claim that GitHub server-side protection rules are enabled.

Before installing a candidate, preserve the application's exported settings/provider configuration and any required recording files. An older APK with a lower version code may be rejected by Android's installer. The rollback file's integrity is verified here; an in-place downgrade on the physical device is not. Do not automatically uninstall or clear data to force a downgrade. Do not re-sign or increase the rollback APK's version: that would cease to be the exact locked artifact.

The source rollback is the pinned commit. The runtime rollback is the original signed APK plus the user's preserved data/configuration, following the device's supported restore procedure.
