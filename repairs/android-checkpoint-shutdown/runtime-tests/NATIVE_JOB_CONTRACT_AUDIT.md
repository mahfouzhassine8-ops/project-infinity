# Concrete native job persistence contracts

This audit follows concrete `CJob` implementations, their construction sites, completion callbacks and relevant callees in the preserved native runtime. It excludes `CLambdaJob`, which has a separate call-site audit. It is bounded source analysis, not device validation or a blanket classification of all Kodi jobs.

## Classification rules

- **Unknown** retains an unresolved lifetime obligation, including after the job returns or is destroyed. A class name, `GetType()` string, lack of a running thread, or a successful `DoWork()` return does not establish durability.
- **Required** needs an exact implementation/callback contract mapped to an existing checked persistence owner. The owner's final barrier must cover all accepted writes and semantic failures. Returning `true` while swallowing a failed open, commit, callback or required child operation is insufficient.
- **NonPersistent** means the bounded operation has no required user state to commit. A separately justified disposable cache may fit this category, but any SQLite transaction it opens still participates in database admission and lock/transaction drainage. This does not permit process termination while unaccounted database work is in flight.
- Require exact dynamic class identity, or a private `final` implementation with an exact owning callback. Subclasses, alternative callbacks and altered dispatch targets retain Unknown unless independently audited.
- Class contracts cover progress/completion/abort callbacks and destruction. Child jobs, script launches, provider dispatch, image decoder add-ons and deferred work need their own accounted contracts.

## Source-bounded nonpersistent contracts

| Exact class and submission | Work and callback evidence | Scope / status |
| --- | --- | --- |
| `CSysInfoJob`, produced by `CSysInfo::GetJob()` through `CInfoLoader::GetInfo()` | Reads system facts and network connectivity into `CSysData`; exact `CSysInfo::OnJobComplete` copies that data and updates in-memory refresh timers. | NonPersistent for exact class and exact `CSysInfo` callback, or null. Different subclass/callback remains Unknown. Core owns implementation. |
| `CZeroconf::CPublish`, `CZeroconf::Start` / `PublishService`, null callback | Android backend registers NSD advertisements and stores service references in memory. Settings changes in the caller's earlier `Start()` failure branch are outside this job and remain settings-owner work. | Android-only NonPersistent for exact class/null callback. Core owns implementation. |
| `PingResponseWaiter::CHostProberJob`, constructed by its owning waiter | Network/UPnP discovery probe; owning waiter's callback only sets `m_hostOnline`. | Private final class plus exact owner callback is NonPersistent. Core owns implementation. |
| `PVR::CPVREventLogJob`, null callback at `PVRClients`, `PVRTimers`, and `PVRGUIActionsTimers` submission sites | Queues optional toast notifications and appends `CNotificationEvent` objects to `CEventLog`'s in-memory vector/map, with a GUI event message. No PVR backend, timer, recording or database mutation occurs inside this job. | Implemented exact-class/null-callback NonPersistent contract. Subclasses, non-null callbacks and type-string spoofing remain Unknown. |
| `CTextureUseCountJob`, submitted through `CTextureCache::IncrementUseCount` | Only updates Textures DB use-count/last-used maintenance. Exact `CTextureCache::OnJobComplete` enters `OnCachingComplete` only for texture-image jobs; a use-count job falls through to ordinary queue bookkeeping. | Candidate NonPersistent for exact class and exact `CTextureCache` callback, or null: this is optional cache-eviction metadata. Keep database transaction fencing/drainage. No production classification was added by this audit. |

`CGetDirectory::CGetJob` restricted to the exact `XFILE::CPosixDirectory` implementation and a null callback would be a read-only bound: Android's implementation performs `opendir/readdir/stat` and builds in-memory items. However, the enclosing `CGetDirectory` helper is not instantiated anywhere in the inspected `Directory.cpp`. It is **not** a demonstrated common startup job, and no latent exemption was added. The active directory path has separate admission handling.

## Required-state candidates needing checked contracts

These are plausible owner mappings, not permission to mark the current jobs safe merely because they finished.

| Exact class / call site | Actual required side effects | Candidate owner and remaining proof |
| --- | --- | --- |
| `CMACDiscoveryJob` / `CWakeOnAccess::QueueMACDiscoveryForHost` | Work probes a MAC address, but exact `CWakeOnAccess::OnJobComplete` calls `SaveMACDiscoveryResult` and `SaveToXML`, changing wake-on-access configuration. | `xml_files`. The global TinyXML save path covers serialization/storage operations during checkpoint, but the void callback and XML-construction early returns need explicit semantic failure/owner handling. It is not a read-only job. |
| `MUSIC_UTILS::CSetSongRatingJob` / `UpdateSongRatingJob`, null callback | Writes user song ratings through `CMusicDatabase`. | `native_databases`; require checked database open and verified rating write. Current `DoWork` returns true even when `Open()` fails. |
| `CSetUserratingJob` in `GUIDialogMusicInfo.cpp`, dialog-deinit submission, null callback | Writes an album's user rating through `CMusicDatabase`. | `native_databases`; same unchecked open/always-true issue, plus checked target/update semantics. |
| `MUSIC_UTILS::CSetArtJob` / `UpdateArtJob`, null callback | Writes user-selected music artwork and modification date, clears derived playlist cache, and updates in-memory current-playback art. | `native_databases` for authoritative rows, with required setter/readback checks. Current native SQL error coverage does not prove a semantically correct target/update by itself. |
| `CVideoLibraryMarkWatchedJob` / `CVideoLibraryQueue` | Changes playcount and resume rows; folders recurse; PVR recording and UPnP paths can update remote state. | A bounded local-native-database variant could use `native_databases` after checked commits/readback. The current whole class cannot: remote provider/recording semantics and recursive dispatch require separate contracts. |
| `CVideoLibraryResetResumePointJob` / `CVideoLibraryQueue` | Deletes resume points locally or updates PVR/UPnP owners; folders recurse. | Same bounded-owner requirement as mark-watched. Current `CommitTransaction()` result is ignored. |
| `CMusicLibraryImportJob` / music library queue | Imports user/library metadata through `CMusicDatabase::ImportFromXML`. | Potential `native_databases`, but the job currently ignores the semantic import result and returns true. Input parsing/partial-import outcomes need an explicit contract. |

The existing database barrier covers registered native SQLite connections, queued writes, transactions and SQL errors. It does not establish remote server durability, correct affected rows, complete source-file exports, or private writes made by dispatched add-ons. The XML barrier similarly does not certify arbitrary VFS/file operations just because one adjacent XML save is wrapped.

## Classes that must remain unclassified as a whole

| Class / family | Why no class-wide exemption or simple existing-owner mapping is justified |
| --- | --- |
| `CDirectoryJob` in `guilib/listproviders/DirectoryProvider.cpp` | Calls general `CDirectory::GetDirectory`, then thumbnail/media loaders. The target may be a Python provider or other VFS implementation. Display output does not bound producer side effects. |
| `CGetDirectory::CGetJob` with an arbitrary `IDirectory` | Dispatch target is virtual and not intrinsically read-only. Exact CJob identity alone does not bound the directory implementation. |
| `CGUIMultiImage::CMultiImageJob` | Resolves texture paths and calls general directory/MIME handling. Its UI callback is memory-only, but that does not prove all dispatched work is nonpersistent. |
| `CImageLoader` and `CTextureCacheJob` | Read images through arbitrary VFS paths and `ImageFactory`, which can instantiate binary image-decoder add-ons. Special image loaders can parse media/album/folder/PVR sources. Cache-image completion also changes texture DB mappings. A cache destination alone does not prove every callee has only optional side effects. |
| `CThumbnailWriter` | Writes an externally supplied thumbnail destination. The class does not restrict it to a disposable cache namespace. A path- and caller-bounded variant could be reviewed separately. |
| `CRecentlyAddedJob` / `CGUIWindowHome` | Not purely GUI work: `CVideoThumbLoader` can write video-library art and stream details, extract media information, and start cache work. The callback can schedule another refresh. A successful presentation refresh is not a complete persistence proof. |
| `CGetSongInfoJob`, `CGetInfoJob`, `CRefreshInfoJob` | Follow tag, artwork, scanner/scraper and directory paths. The top-level “get info” name is not a side-effect boundary. |
| `CWeatherJob` | Launches the configured Python weather service and waits for its invocation to stop. That service has its own persistent-state contract; script disappearance supplies none. |
| `CSubtitlesJob` / `CGUIDialogSubtitles` | General provider directory execution; completion/download handling may copy a subtitle to media/storage paths and change player subtitle state. Neither the directory result nor an unconditional true return proves those effects persisted. |
| `CRepositoryUpdateJob` / `CRepositoryUpdater` | Updates add-on DB metadata and texture invalidation; its callback can call `CheckAndInstallAddonUpdates`, schedule more updates, and publish events. Whole callback/child installation behavior must be bounded. |
| `CAddonInstallJob`, `CAddonUnInstallJob` | Download, replace/remove add-on files and optionally data, change add-on DB/registration, and run installation lifecycle paths. Need a dedicated checked installer/file transaction contract. |
| `CFileOperationJob` | General copy/move/delete/create operations over VFS and arbitrary destinations. Native SQLite/XML owners do not cover it. |
| `CCDDARipJob` | Writes encoded user media, may copy a temporary file to a remote destination, and uses encoder add-ons. Needs checked output/namespace and encoder contracts. |
| Music/video scanning, cleaning, refreshing and export jobs | Scanner/scraper work, database mutations, asynchronous scanner ownership, export files and completion outcomes differ by concrete operation. Base-library-job or queue identity is not enough. Export destinations are user data, not disposable cache. |
| `CAutorunMediaJob` | Opens a modal dialog and executes a builtin/window action; resulting directory/provider work is not bounded by the top-level class. |
| `CPVRChannelEntryTimeoutJob` | Calls `SwitchToCurrentChannel`, initiating playback/PVR effects. It is not interchangeable with the information-hiding timeout job. |
| `CPVRChannelInfoTimeoutJob` | Changes GUI preview/info state and publishes navigator events. This is a possible narrower UI-only candidate, but event subscribers were not fully audited here. |
| `CPeripheralCecAdapterReopenJob` | Reopens device/adapter state and calls additional peripheral logic; it is not covered merely by a peripheral-settings filename. Not needed for an Android-only proof without platform/build evidence. |

## Implemented change and validation

Only `xbmc/pvr/PVREventLogJob.h` and `.cpp` were changed by this audit after the parent authorized that narrow integration. The job reports operation `pvr-memory-event-notification`; it returns NonPersistent only for the exact dynamic class and null callback. Unknown is preserved for alternative implementations or callback behavior.

`runtime-tests/test_pvr_event_job_contract.py --source-root <native-source-root>` compiles the **actual production implementation and header**, with host boundaries for toast/event services. It tests exact-class acceptance, subclass rejection, arbitrary-callback rejection, `GetType()` spoof rejection, real event/toast execution, and an unavailable event log. It passes. This is a contract unit test, not a full Android build or an audit of every GUI event subscriber.

Common startup coverage is still incomplete: directory/provider, texture/media-loading, recently-added and repository jobs require additional bounded contracts. No unsupported job becomes safe by completion, no callbacks are silently discarded, and no add-ons or features are disabled by this audit.
