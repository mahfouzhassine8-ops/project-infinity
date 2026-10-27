# Scoped isolation contract

The immutable 2103420 APK is the byte source. `results/scoped-correction/final`
records 64,143 original methods checked, 311 copied methods checked, and 8,833
unchanged class definitions. Only the explicit boundary instructions differ.
All native libraries and existing assets remain byte-identical. The accepted
combined-release pointer remains the user-approved 2103420 baseline.

| State | Owner and preservation rule |
| --- | --- |
| Kodi profiles, databases, add-ons, progress and native state | Infinity; original paths and bytes |
| `infinity_runtime` background preference | Infinity; original preference wrapper and key |
| `infinity_cobra_live`, Cobra feature/provider/player preferences | Cobra; existing files and keys, distinct Cobra persistence queue/barrier |
| `infinity_experience` | Chooser shell; existing file and launch modes, checked owner port |
| Player rotation | Infinity retains `infinity_player_rotation`; Cobra receives the existing mode once in `cobra_player_rotation` |
| Cobra background setting | Once copied from the existing value to `cobra_background_runtime`; later writes are independent |
| Refresh policy/runtime files | Infinity retains `.kodi/userdata/addon_data/service.infinity.refresh`; Cobra receives a byte-preserving first-use snapshot at `.cobra/refresh` |
| Java protected writes and receipts | Three separately instantiated persistence queues and barriers; original sync, readback, atomic rollback, path/hardlink checks and failure accounting |
| Mini-player/media-session/PiP background state | Separate service classes, singleton fields, callbacks, generations, action names and notification IDs |

Snapshot publication uses protected commits/readback and file/directory sync,
cross-process file locks and a final completion marker. Existing owner values
win. The original files are never removed or rewritten by the snapshot. Each
storage root has its own refresh marker, including external-storage fallback.
The first container entry seeds these narrowly scoped values before an
Infinity background-setting action can change the former shared value. This
is the explicit one-time initialization exception; it starts no background
worker or playback session. No user database is migrated.

Infinity's original service stays in `:kodi`. Cobra's copied service runs with
its activity in the default process. The launcher, Infinity coordinator and
all other existing component/process attributes are unchanged. The existing
OS notification channel remains a container contract so its user preference
survives. Service actions and notification IDs are distinct.

`CombinedDurability` is a versioned container termination contract, with
Infinity, Cobra and shell ports. Locks are acquired in that order, then the
Cobra retention lock. A quiescent process needs all three original receipts
under their original locks before the existing termination callback runs.
Pending writes, failed durability, late writes, a wrong receipt, or a newly
active Cobra lease cannot authorize termination.

If Cobra was active when Infinity closed, Cobra and the chooser remain
writable. That plan can never authorize killing their process, even if Cobra
subsequently becomes inactive. Only the coordinator's existing verified
engine-retired boundary reopens admission for a retained process; it does not
erase failures or pending writes. Native-lease authorization keeps the stricter
termination path. Activities and services release retention after their
original cleanup; overlapping reminder jobs hold independent parameter leases.

Container exceptions are explicit in `ownership-reviewed-roots.json`: immutable
Android adapters and resources, chooser presentation supplied by Cobra, the
checked preferences/chooser ports, read-only diagnostic export of Infinity
logs, and generic asset extraction of the Cobra theme resource package. The
theme owns no Python engine entry point. Reflection sites and all native/JNI
symbols are inventoried; existing dynamic loaders remain byte-identical and
bound to their owner payloads. Static evidence cannot predict arbitrary future
reflection strings, so future owner updates must repeat dependency review.

The focused tests use disposable data and callbacks, never the user's files
or actual process termination. They establish the corrected boundaries; they
do not claim physical Fold acceptance or a new shutdown stress-test pass.
