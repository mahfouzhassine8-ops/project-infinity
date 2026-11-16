# Infinity 502 — Empty Shell three-path investigation (read-only, 2026-11-15)

**Scope:** Assess (1) native Python script admission, (2) add-on initialization/execution, (3) installed-versus-packaged skin/components. No production code, user data, signing or recovery was changed for this investigation. The issue is **NOT yet causally diagnosed or repaired**.

**Exact signed source packages** (already authenticated by the signed APK/native-map audit):
- 2103486: APK SHA256 `550b67fa095e2f1c702c073433f754ba3db7cc057e42f1d05fe0789ff264f197`; native SHA256 `b75747363c83a548d61463c2fd434be909f27c07d4872fa9d9c61642a3757635`.
- 2103502: APK SHA256 `f35b6e6015d91185d76a12b4f21cec17c9eaa65ef07b17d8fed91a547dfffb28`; native SHA256 `ed2d955d1825bf838ea50a712782e54b69926d40605270a2f241efd913202ee7`.
- Between 86 and 502, exact native source hashes match for `xbmc/interfaces/generic/ScriptInvocationManager.cpp`, `xbmc/interfaces/python/PythonInvoker.cpp`, `xbmc/interfaces/python/XBPython.cpp`, `xbmc/interfaces/builtins/AddonBuiltins.cpp`, `xbmc/interfaces/python/AddonPythonInvoker.cpp`, and the startup/lifecycle implementation. The CPython3.11.7 NULL-return GIL double-restore correction from `679807f7` remains present in the signed502 source. Therefore a direct rollback of this correction is **excluded**, but successful runtime operation is **not proven**.

## A. Script admission after failed checkpoint — confirmed code mechanism, incident attribution pending

At the source-equivalent `CScriptInvocationManager` implementation:
- `BeginCheckpointStartupAdmission()` permanently sets `m_checkpointStartupAdmissionClosed=true` within that manager instance.
- `BeginShutdown()` / `BeginAndroidCheckpoint()` set `m_shutdownRequested=true`.
- Both `GetLanguageInvokerForAdmission()` and `ExecuteAsync()` reject new scripts when shutdown is requested, or when startup admission is closed except for a narrow authenticated first-party checkpoint participant.
- `AddonBuiltins::RunScript()` discards the negative `ExecuteAsync` return and returns `0` for the public built-in. Thus a menu action can appear to have been dispatched while no Python script was admitted; native skin remains responsive. This is **confirmed source behavior**, not proof of the owner's particular Empty Shell event.

Two **historical Nov14** diagnostics (prior to 502, and not equivalent to a 502 failure) independently record `CHECKPOINT_FAILED` after about 25 seconds, `admission_sealed=true`, 11 reported blockers, and **no verified engine process death**. The Nov14 21:40 native checkpoint trace for the same close PID contains `scripts.checkpoint_new_background_admission_closed`. There is **no matched post-failure menu request and no proof the identical PID remained active to produce Empty Shell**.

A newer Nov15 diagnostic for installed 500 recorded **successful 2.852s engine shutdown**, zero blockers and confirmed engine process death. This is a different process/session; it neither resolves the earlier failure nor demonstrates a current stuck admission.

**Discriminator:** Correlate the next failure's actual engine PID/launch token, `m_shutdownRequested`, `m_checkpointStartupAdmissionClosed`, request admission result and checkpoint generation. A rejected Health Center/Command Center request in the **same PID after failed Close** establishes the causal chain. A fresh PID with admission open excludes retained same-manager closure for that occurrence. Do not reopen gates or bypass durability without source-specific evidence.

## B. Add-on initialization — command registration intact; targeted runtime failure still possible

The signed502 `script.infinity.commandcenter/addon.xml` still declares `service.py` with `start="startup"`, and the add-on version is 0.3.5.83. The Nov14 installed inventory matches the six sampled Command Center files byte-for-byte against packaged 502; the later Nov15 installed500 diagnostic records **27/27 sampled Command Center files matching the packaged version**. This argues against a wholesale replacement of Command Center, but the inventory is not proof that its Python service, Health Center menu, or providers actually completed execution.

Command Center's entry points install a first-party `module_contract.active_contract` guard and can reject conflicting runtime module generations. Its source and the Kodi Python startup entry points did not change from 500 to 502. Available traces do not show a matched failing Health Center invocation/result/interpreter-stage.

The historical Nov14 quarantine snapshot includes provider entries for Otaku and POV with repeated uncaught service failure reasons; these rows establish retained quarantine records, **not** that those providers were blocked during a specific Empty Shell occurrence. Do not equate a provider quarantine with a process-wide Python runtime failure.

**Discriminator:** For one matched failing menu action, record the real `ExecuteAsync` result before first Python entry, interpreter initialization/GIL stage if admitted, first-party module-contract accept/refuse outcome and service errors. Separate a rejected native script from a Python-started-but-failed add-on.

## C. Installed component mismatch — confirmed differences, runtime role not yet established

Signed502 APK packaged versus **historical installed 500** add-on inventory:

| Component | Packaged 86 | Packaged 502 | Reported installed 500 | Interpretation |
|---|---|---|---|---|
| `skin.infinity.diggz` | 1.0.5.273 | **1.0.5.274** | **1.0.5.268** | Version mismatch, active runtime skin root unknown |
| `script.kodihealthcenter` | 2.5.27 | **2.5.27** | **2.5.26** | Installed version older than packaged |
| `service.infinity.compat` | 0.7.2 | **0.7.2** | **0.8.2** | Installed version newer than packaged; on-device inventory names `runtime_service.py`, packaged service declarations differ |
| `script.infinity.commandcenter` | 0.3.5.78 | **0.3.5.83** | **0.3.5.83** | Same version, and sampled hashes match |

The Nov15 read-only skin comparison includes **17 differences among 2,224 reported files**, chiefly 13 `DialogButtonMenu.xml` variants plus skin metadata/VideoOSD. No inventoried Home widget differs. This is **not** proof of an older active runtime skin (the evidence explicitly marks runtime active root as UNKNOWN), nor proof that a newer compatibility service or older Health Center is incompatible.

**Discriminator:** In the failing PID, establish active `special://skin` and `xbmc.getSkinDir()` path/identity, and actual `xbmcaddon.Addon(id).getAddonInfo('path')` and source hashes for the three mismatched add-ons. Compare active installed, packaged and any profile/overlay copy. Read only; never mass-upgrade, overwrite, clear data, reinstall or migrate to force version equality.

## Focused next gate (Astra + Codex; no broad repair)

1. Bind one actual Empty Shell symptom/action and the nearest successful request to the **same** PID and process generation. The available November 14/15 evidence doesn't contain that matched pair. Do not pretend the symptom is proven to persist on signed502 without a 502 incident record.
2. Check native dispatch admission before Python import, and separate `-1` refusal / quarantine from Python initializer/GIL failure / module-contract failure. Source already contains bounded startup tracing; verify whether a shipped build enables it before relying on absent trace events.
3. Verify active runtime installed copy of skin, Health Center, compatibility service and Command Center without modifying user files.
4. Only then propose a one-boundary correction. Preserve actual 502, signed originals, profiles, shutdown gates, existing Cast and Cobra. No rollback to 86, no guessed repair, no broad provider changes.

**Current result:** Three hypotheses investigated with concrete source and packaging evidence. The failed-checkpoint admission mechanism and installed-component mismatches are real. The precise cause of the reported Empty Shell symptom remains **UNPROVEN** without a same-PID failure-to-request correlation. No production modification authorized by this research note.
