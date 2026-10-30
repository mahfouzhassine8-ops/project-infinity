# Exact signed431 native Settings-return baseline

The actual native shell and guide builders run unchanged. Two selected baseline methods were exercised separately: one foundation observation and one five-scenario observation method. The passing observation assertions do not mean scroll retention passes: the240-item case reproduces a host defect.

| Case | Real GridView additions/removals during return | First visible before → after | Adapter count | Recorded guide jobs before → after |
|---|---:|---:|---:|---:|
| changed-favorites-profile | 2 / 2 | 0 → 0 | 2 | 0 → 0 |
| loaded-nonzero-scroll | 2 / 2 | 80 → 0 | 240 | 0 → 0 |
| null-preview | 2 / 2 | 0 → 0 | 24 | 0 → 0 |
| theme-geometry | 2 / 2 | 0 → 0 | 24 | 0 → 0 |
| uncached-EPG | 2 / 2 | 0 → 0 | 24 | 1 → 1 |

Every case rebuilds the native GridView twice on the same return stack. In the240-channel loaded case, an actual nonzero native firstVisiblePosition80 is lost and the stored context becomes[0,0]. The first rebuild requests selection restoration; before its layout, the second rebuild saves the new empty GridView’s initial position. Raw synchronous and post-measure snapshots are retained.

Other observations preserve the selected channel, current/next programme fields, the null-preview selection fallback, changed Favorites/profile filtering and native measured geometry/theme. The uncached EPG case retains its one existing request; no real HTTP executes. A recording executor holds real submitted Runnable objects, and autoplay stays disabled.

The source review advises retaining terminal post-shell layout/details/effects when considering deduplication: ShowGuideShell changes selection/loading state after its first renderer call. No settings-return production change was made. The separate Cards-reuse implementation may remove the redundant rebuild while retaining the pending native restore; this remains a candidate acceptance requirement.

Foundation uses real buildShell/ShowGuideShell/Layout/Render and native parents/GridView/adapters, not replacement controls or method stubs. Activity.get/visible is used without application lifecycle startup/stop/shutdown. Host viewport is941dp×1672dp atmdpi and an explicit760×1100 measured resize; this is not physicalFold or approved-PNG pixel acceptance. No timing/FPS/CPU/memory/power claim.

Two fixture failures remain preserved: missing native-window handoff, then cross-case synthetic locked-profile contamination. Corrections used the previously passing400ms host frame opportunity and the original public profile-selection API; attachment, policy and count assertions stayed strict.
