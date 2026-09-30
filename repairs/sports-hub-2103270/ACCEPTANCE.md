# Cobra 2103270 Sports Hub — acceptance contract

2103269 is the locked rollback/source baseline. 2103270 is additive and is **not** locked by CI.

| Surface | Required behavior | Automated evidence | Physical-device boundary |
|---|---|---|---|
| Sports destination | First-class Cobra drawer owner; back/return state is deterministic | Production drawer action + actual stage at portrait/landscape narrow bounds | Samsung Fold drawer/focus/touch |
| Scoreboard repository | Real provider data is isolated behind a replaceable repository; production contains no fixture scores | Controlled ESPN-shaped JSON parser tests | Internet availability/rate behavior |
| My Teams | Team follow state persists and only changes the favorite set | SharedPreferences + immutable score fixture | Team-logo loading and real refresh |
| Hide Scores | Scores disappear consistently without altering underlying game state | Production formatter test | Visual review across hub/game/Multi-View |
| Game → channel resolver | Broadcast aliases + EPG matchup evidence are ranked; ambiguous matches never auto-play | Strong/ambiguous controlled resolver tests | Real provider naming/EPG quality |
| Watch Live | Strong unique match hands to existing `playChannel`; multiple candidates require user choice | Source ownership/preservation gate | Real decode/provider handoff |
| Smart Sports Multi-View | Reuses existing `openMultiView`; manual panes win; full 4-pane manual grid is protected | Full-grid pin protection test + inherited Multi-View suite | Real simultaneous streams/performance |
| Fullscreen return | Existing Multi-View session ownership remains unchanged | Inherited 2103229/2103269 regressions | Physical back/fullscreen interaction |
| Recording | Resolves to an actual EPG event and reuses existing program action path | Source-level ownership gate | Real recording service/provider |
| Stats/standings | Optional remote detail; failure does not affect Live TV | Failure-isolated repository design | Real endpoint completeness |
| Responsive UI | Sports uses current Cobra window helpers; actions stack in narrow panes | 320×720 / 720×320 production view test | Samsung split/pop-up/fold/unfold |
| Light/OLED preservation | Sports uses current Cobra glass/palette APIs and inherited screens remain pixel-protected | 2103269 protected render byte equality + inherited suites | Physical display review |
| Live TV isolation | Sports refresh/data failure cannot own/release/reprepare player/provider | Exact source delta + inherited Live TV/player tests | Real provider/network outage |

A green CI result means **automated test candidate**, not device-passed and not locked.
