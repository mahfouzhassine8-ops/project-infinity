# Infinity 2103377 RC5 — failed run saved, green evidence preserved, correction repushed

## Exact failure (not a production native compile error)
- Failed full-native workflow: **38516229281** at source SHA **9d418baf84d96057675468c8ca457f5adf420921**.
- RC3+RC5 source reconstruction **passed**, including installed-source preservation and early Curl tests.
- Host method compile failed before the full native engine compile step because the **mock** `Invoker` omitted `GetId()` and the **mock** `InfinityVfsOpenTrace::Request(int,const char*)` was undeclared. The production RC3 invoker/vfs instrumentation was already present and was not changed by this correction.
- Repaired exactly those test-harness definitions in `repairs/shutdown-rc5-2103377/verify_optional.py`. No production source patch, skin, Trakt add-on, Resume Hub or required-save barrier was changed.

## What remains verified green
| Evidence | Run | Result |
| --- | --- | --- |
| Original RC5 Java/Android cases and donor build | `38514680851` | **274/274 passing, zero failures; donor verified** |
| RC5 compiled C++ original classifier + cooperative-stop method host scenarios | `38517351538` | **17/17 passing** |
| RC3 original full native Curl/early-save correction | `38498786704` | **Green preserved reference, not the RC5 binary** |
| RC4 timing and dynamic recovery notification | `38508366685` | **274/274 original cases + targeted UI checks, green** |
| Locked production APK and skin | **2103376 / 1.0.5.211** | **No modification** |

### Resumed build
- **Corrected production branch:** `work/infinity-2103377-rc5-optional-python-retirement`
- **Source SHA after tested harness repair:** `645b0e8b15c45d4c170a8b664073a87cb848b831`
- **Full native rebuild:** `38517386755` — triggered by that exact source SHA.
- **Packaging preparation branch:** `work/infinity-2103377-rc5-green-package`, cloned from the corrected native parent and pinned to native SHA `645b0e8b15c45d4c170a8b664073a87cb848b831` and Android SHA `5a1a427cb5bdcc248b0e2a7887f9d6682ca53877`. Workflow staged under `repairs/shutdown-rc5-2103377/rc5-signed-workflow.pending.yml`, **not activated until full native build passes**.

## User-approved behavior
- **Trakt remains installed and updateable**, usable anytime; its optional service receives native Close Stop but is not treated as an Infinity-required save owner.
- **Infinity Continuity** diagnostic remains active while Infinity runs; its known, SHA-pinned diagnostic monitor stops on Close without gating Resume Hub saves.
- No Trakt patch, no uninstall, no disabling.
- **Resume Hub remains local-first, authoritative**, all 17 mandatory save owners, actual database durability, final authorize-to-terminate, health state and Android Recents remain protected.
- Physical full-load Fold exit, 17/17 true save receipts and reopen state remain **not verified**. No APK is locked or promoted based on green CI alone.

## Integrity boundary
Build at exactly `645b0e8b15c45d4c170a8b664073a87cb848b831`; do not merge unrelated changes, do not restart wide diagnostics, do not fabricate passed stages. On a failure, inspect the failing step and carry forward the already-green receipts.
