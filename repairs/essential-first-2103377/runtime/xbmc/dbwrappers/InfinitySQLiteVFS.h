/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
#include "platform/android/activity/InfinityProtectedWrites.h"
#include <sqlite3.h>
#include <cstring>
#include <memory>
#include <vector>
#if defined(TARGET_ANDROID)
#include "platform/android/activity/InfinityAndroidCheckpoint.h"
#endif

// A subordinate I/O adapter for the existing persistence ledger. SQLite passes
// the ACTUAL filename here, including ATTACH/URI targets and WAL/journal files.
// No SQL parsing, Python finalization, synthetic commit, or transaction rollback.
namespace InfinitySQLiteVFS
{
namespace Ledger = InfinityScriptPersistence;
struct File
{
  sqlite3_file base;
  sqlite3_file* real;
  const char* path;
  int flags;
  int lock;
  unsigned shm;
};
struct Vfs
{
  sqlite3_vfs api;
  sqlite3_vfs* real;
  std::string name;
};
inline File* F(sqlite3_file* f) { return reinterpret_cast<File*>(f); }
inline Vfs* V(sqlite3_vfs* v) { return static_cast<Vfs*>(v->pAppData); }
inline bool SavePermission()
{
#if defined(TARGET_ANDROID)
  return InfinityAndroidCheckpoint::IsPersistingOnThisThread();
#else
  return false;
#endif
}
inline std::string Path(File* f) { return f->path ? f->path : InfinityScriptPersistence::NonPersistentTarget(); }
inline std::string DatabasePath(File* f)
{
  auto path = Path(f);
  if ((f->flags & SQLITE_OPEN_WAL) && path.size() > 4) path.resize(path.size() - 4);
  if ((f->flags & SQLITE_OPEN_MAIN_JOURNAL) && path.size() > 8) path.resize(path.size() - 8);
  return path;
}
inline std::string Key(File* f, const char* suffix)
{ return "sqlite:" + std::to_string(reinterpret_cast<uintptr_t>(f)) + ":" + suffix; }
inline bool Draining(File* f)
{ return Ledger::HasProtectedTransaction(DatabasePath(f)); }

inline int Close(sqlite3_file* file)
{
  auto* f = F(file);
  std::unique_ptr<Ledger::ProtectedOperation> guard;
  if ((f->flags & SQLITE_OPEN_DELETEONCLOSE) && f->path)
  {
    // Some Unix builds defer the unlink until xClose. Keep that mutation
    // inside the same barrier even when the handle predates Close.
    guard.reset(new Ledger::ProtectedOperation(Ledger::CurrentWriteOwner(), {Path(f)},
        "sqlite.vfs.delete_on_close", SavePermission(), Draining(f)));
    if (!*guard) return SQLITE_READONLY;
  }
  const auto result = f->real->pMethods->xClose(f->real);
  if (result == SQLITE_OK)
  {
    Ledger::SetProtectedTransaction(Key(f, "rollback"), Path(f), false);
    Ledger::SetProtectedTransaction(Key(f, "wal"), Path(f), false);
  }
  else Ledger::ProtectionFailure("sqlite_vfs_close_failed:" + Path(f));
  f->base.pMethods = nullptr;
  return result;
}
inline int Read(sqlite3_file* file, void* bytes, int count, sqlite3_int64 offset)
{ auto* f = F(file); return f->real->pMethods->xRead(f->real, bytes, count, offset); }
inline int Write(sqlite3_file* file, const void* bytes, int count, sqlite3_int64 offset)
{
  auto* f = F(file);
  Ledger::ProtectedOperation guard(Ledger::CurrentWriteOwner(), {Path(f)}, "sqlite.vfs.write", SavePermission(), Draining(f));
  if (!guard) return SQLITE_READONLY;
  return f->real->pMethods->xWrite(f->real, bytes, count, offset);
}
inline int Truncate(sqlite3_file* file, sqlite3_int64 size)
{
  auto* f = F(file);
  Ledger::ProtectedOperation guard(Ledger::CurrentWriteOwner(), {Path(f)}, "sqlite.vfs.truncate", SavePermission(), Draining(f));
  if (!guard) return SQLITE_READONLY;
  return f->real->pMethods->xTruncate(f->real, size);
}
inline int Sync(sqlite3_file* file, int flags)
{ auto* f = F(file); return f->real->pMethods->xSync(f->real, flags); }
inline int Size(sqlite3_file* file, sqlite3_int64* size)
{ auto* f = F(file); return f->real->pMethods->xFileSize(f->real, size); }
inline int Lock(sqlite3_file* file, int level)
{
  auto* f = F(file);
  if (level < SQLITE_LOCK_RESERVED) return f->real->pMethods->xLock(f->real, level);
  Ledger::ProtectedOperation guard(Ledger::CurrentWriteOwner(), {Path(f)}, "sqlite.vfs.write_lock", SavePermission(), f->lock >= SQLITE_LOCK_RESERVED);
  if (!guard) return SQLITE_READONLY;
  const int result = f->real->pMethods->xLock(f->real, level);
  if (result == SQLITE_OK)
  {
    f->lock = level;
    Ledger::SetProtectedTransaction(Key(f, "rollback"), Path(f), true);
  }
  return result;
}
inline int Unlock(sqlite3_file* file, int level)
{
  auto* f = F(file); const int result = f->real->pMethods->xUnlock(f->real, level);
  if (result == SQLITE_OK)
  {
    f->lock = level;
    if (level < SQLITE_LOCK_RESERVED) Ledger::SetProtectedTransaction(Key(f, "rollback"), Path(f), false);
  }
  return result;
}
inline int Reserved(sqlite3_file* file, int* result)
{ auto* f = F(file); return f->real->pMethods->xCheckReservedLock(f->real, result); }
inline int Control(sqlite3_file* file, int operation, void* argument)
{
  auto* f = F(file);
  if (operation == SQLITE_FCNTL_FILE_POINTER) { *static_cast<sqlite3_file**>(argument) = file; return SQLITE_OK; }
  // Inquiry controls do not mutate bytes. All other controls stay inside a
  // write lease; SIZE_HINT, COMMIT_PHASETWO and platform-specific controls can.
  if (operation == SQLITE_FCNTL_LOCKSTATE || operation == SQLITE_FCNTL_LAST_ERRNO ||
      operation == SQLITE_FCNTL_VFSNAME || operation == SQLITE_FCNTL_HAS_MOVED ||
      operation == SQLITE_FCNTL_DATA_VERSION || operation == SQLITE_FCNTL_COMMIT_PHASETWO)
    return f->real->pMethods->xFileControl(f->real, operation, argument);
  Ledger::ProtectedOperation guard(Ledger::CurrentWriteOwner(), {Path(f)}, "sqlite.vfs.file_control", SavePermission(), Draining(f));
  if (!guard) return SQLITE_READONLY;
  return f->real->pMethods->xFileControl(f->real, operation, argument);
}
inline int Sector(sqlite3_file* file)
{ auto* f = F(file); return f->real->pMethods->xSectorSize(f->real); }
inline int Characteristics(sqlite3_file* file)
{ auto* f = F(file); return f->real->pMethods->xDeviceCharacteristics(f->real); }
inline int ShmMap(sqlite3_file* file, int page, int size, int extend, void volatile** result)
{
  auto* f = F(file);
  if (!f->real->pMethods->xShmMap) return SQLITE_IOERR_SHMMAP;
  Ledger::ProtectedOperation guard(Ledger::CurrentWriteOwner(), {Path(f)}, "sqlite.vfs.shm_map", SavePermission(), Draining(f));
  if (!guard) return SQLITE_READONLY;
  return f->real->pMethods->xShmMap(f->real, page, size, extend, result);
}
inline int ShmLock(sqlite3_file* file, int offset, int count, int flags)
{
  auto* f = F(file);
  if (!f->real->pMethods->xShmLock || offset < 0 || count <= 0 || offset + count > 32) return SQLITE_IOERR_SHMLOCK;
  const unsigned mask = (count == 32 ? ~0U : ((1U << count) - 1)) << offset;
  const bool acquiring = (flags & SQLITE_SHM_LOCK) && (flags & SQLITE_SHM_EXCLUSIVE);
  std::unique_ptr<Ledger::ProtectedOperation> guard;
  if (acquiring)
  {
    guard.reset(new Ledger::ProtectedOperation(Ledger::CurrentWriteOwner(), {Path(f)}, "sqlite.vfs.wal_lock", SavePermission(), f->shm != 0));
    if (!*guard) return SQLITE_READONLY;
  }
  const int result = f->real->pMethods->xShmLock(f->real, offset, count, flags);
  if (result == SQLITE_OK)
  {
    if (acquiring) f->shm |= mask;
    else if (flags & SQLITE_SHM_UNLOCK) f->shm &= ~mask;
    Ledger::SetProtectedTransaction(Key(f, "wal"), Path(f), f->shm != 0);
  }
  return result;
}
inline void ShmBarrier(sqlite3_file* file)
{ auto* f = F(file); if (f->real->pMethods->xShmBarrier) f->real->pMethods->xShmBarrier(f->real); }
inline int ShmUnmap(sqlite3_file* file, int remove)
{
  auto* f = F(file);
  if (!f->real->pMethods->xShmUnmap) return SQLITE_OK;
  Ledger::ProtectedOperation guard(Ledger::CurrentWriteOwner(), {Path(f)}, "sqlite.vfs.shm_unmap", SavePermission(), Draining(f));
  // Releasing a mapping is safe; deleting protected shared-memory state is not
  // authorized after the seal. Do not falsify a successful requested deletion.
  if (!guard && remove) return SQLITE_READONLY;
  return f->real->pMethods->xShmUnmap(f->real, remove);
}
inline int Fetch(sqlite3_file* file, sqlite3_int64 offset, int count, void** result)
{
  auto* f = F(file);
  if (f->real->pMethods->iVersion < 3 || !f->real->pMethods->xFetch) { *result = nullptr; return SQLITE_OK; }
  return f->real->pMethods->xFetch(f->real, offset, count, result);
}
inline int Unfetch(sqlite3_file* file, sqlite3_int64 offset, void* pointer)
{
  auto* f = F(file);
  if (f->real->pMethods->iVersion < 3 || !f->real->pMethods->xUnfetch) return SQLITE_OK;
  return f->real->pMethods->xUnfetch(f->real, offset, pointer);
}
inline const sqlite3_io_methods METHODS{3, Close, Read, Write, Truncate, Sync, Size, Lock, Unlock,
  Reserved, Control, Sector, Characteristics, ShmMap, ShmLock, ShmBarrier, ShmUnmap, Fetch, Unfetch};

inline int Open(sqlite3_vfs* vfs, const char* path, sqlite3_file* file, int flags, int* out)
{
  auto* v = V(vfs); auto* f = F(file);
  std::memset(f, 0, sizeof(*f));
  f->real = reinterpret_cast<sqlite3_file*>(reinterpret_cast<unsigned char*>(f) + sizeof(File));
  f->path = path; f->flags = flags;
  const bool writing = flags & (SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_DELETEONCLOSE);
  std::unique_ptr<Ledger::ProtectedOperation> guard;
  if (writing)
  {
    guard.reset(new Ledger::ProtectedOperation(Ledger::CurrentWriteOwner(), {Path(f)}, "sqlite.vfs.open", SavePermission(), Draining(f)));
    if (!*guard) return SQLITE_READONLY;
  }
  const int result = v->real->xOpen(v->real, path, f->real, flags, out);
  if (f->real->pMethods) f->base.pMethods = &METHODS;
  return result;
}
inline int Delete(sqlite3_vfs* vfs, const char* path, int sync)
{
  auto* v = V(vfs); std::string target = path ? path : "";
  std::string database = target;
  for (const auto* suffix : {"-journal", "-wal"})
  {
    const auto size = std::strlen(suffix);
    if (target.size() > size && target.compare(target.size() - size, size, suffix) == 0)
      database.resize(target.size() - size);
  }
  Ledger::ProtectedOperation guard(Ledger::CurrentWriteOwner(), {target}, "sqlite.vfs.delete", SavePermission(), Ledger::HasProtectedTransaction(database));
  if (!guard) return SQLITE_READONLY;
  return v->real->xDelete(v->real, path, sync);
}
inline int Access(sqlite3_vfs* vfs, const char* path, int flags, int* result)
{ auto* v = V(vfs); return v->real->xAccess(v->real, path, flags, result); }
inline int FullPath(sqlite3_vfs* vfs, const char* path, int size, char* result)
{ auto* v = V(vfs); return v->real->xFullPathname(v->real, path, size, result); }
inline void* DlOpen(sqlite3_vfs* vfs, const char* path)
{
  if (Ledger::RejectOpaqueMutation("sqlite_native_extension")) return nullptr;
  Ledger::ProtectionFailure("sqlite_native_extension_not_protected");
  auto* v = V(vfs); return v->real->xDlOpen(v->real, path);
}
inline void DlError(sqlite3_vfs* vfs, int size, char* result)
{ auto* v = V(vfs); v->real->xDlError(v->real, size, result); }
inline void (*DlSym(sqlite3_vfs* vfs, void* handle, const char* symbol))(void)
{ auto* v = V(vfs); return v->real->xDlSym(v->real, handle, symbol); }
inline void DlClose(sqlite3_vfs* vfs, void* handle)
{ auto* v = V(vfs); v->real->xDlClose(v->real, handle); }
inline int Random(sqlite3_vfs* vfs, int size, char* result)
{ auto* v = V(vfs); return v->real->xRandomness(v->real, size, result); }
inline int Sleep(sqlite3_vfs* vfs, int micros)
{ auto* v = V(vfs); return v->real->xSleep(v->real, micros); }
inline int Time(sqlite3_vfs* vfs, double* result)
{ auto* v = V(vfs); return v->real->xCurrentTime(v->real, result); }
inline int LastError(sqlite3_vfs* vfs, int size, char* result)
{ auto* v = V(vfs); return v->real->xGetLastError ? v->real->xGetLastError(v->real, size, result) : 0; }
inline int Time64(sqlite3_vfs* vfs, sqlite3_int64* result)
{
  auto* v = V(vfs);
  if (v->real->iVersion >= 2 && v->real->xCurrentTimeInt64) return v->real->xCurrentTimeInt64(v->real, result);
  double day = 0; const int status = v->real->xCurrentTime(v->real, &day);
  *result = static_cast<sqlite3_int64>(day * 86400000.0); return status;
}
inline bool Install()
{
  static std::mutex mutex;
  static auto* installed = new std::vector<std::unique_ptr<Vfs>>;
  std::lock_guard<std::mutex> lock(mutex);
  if (!installed->empty()) return true;
  auto* originalDefault = sqlite3_vfs_find(nullptr);
  if (!originalDefault) { Ledger::ProtectionFailure("sqlite_default_vfs_unavailable"); return false; }
  std::vector<sqlite3_vfs*> originals{originalDefault};
  // All POSIX VFS names shipped by SQLite's unix backend. Do not traverse or
  // mutate SQLite's private pNext list or a registered VFS object.
  for (const auto* name : {"unix", "unix-excl", "unix-dotfile", "unix-none", "unix-posix", "unix-flock", "unix-afp", "unix-namedsem"})
  {
    auto* found = sqlite3_vfs_find(name);
    if (found && std::find(originals.begin(), originals.end(), found) == originals.end()) originals.push_back(found);
  }
  for (auto* original : originals)
  {
    auto wrapper = std::make_unique<Vfs>();
    wrapper->real = original; wrapper->name = original->zName;
    wrapper->api = {2, static_cast<int>(sizeof(File)) + original->szOsFile, original->mxPathname,
      nullptr, wrapper->name.c_str(), wrapper.get(), Open, Delete, Access, FullPath,
      DlOpen, DlError, DlSym, DlClose, Random, Sleep, Time, LastError, Time64, nullptr, nullptr, nullptr};
    if (sqlite3_vfs_unregister(original) != SQLITE_OK ||
        sqlite3_vfs_register(&wrapper->api, original == originalDefault) != SQLITE_OK)
    { Ledger::ProtectionFailure("sqlite_protected_vfs_registration_failed"); return false; }
    installed->push_back(std::move(wrapper));
  }
  return true;
}
} // namespace InfinitySQLiteVFS
