#include "../runtime/native/overlay/xbmc/platform/android/activity/InfinityCheckpointFile.h"

#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>

namespace file = infinity::checkpoint::files;
namespace fs = std::filesystem;

#define CHECK(condition) do { if (!(condition)) throw std::runtime_error( \
  std::string(__func__) + ":" + std::to_string(__LINE__) + ": " #condition); } while (false)

struct Fixture
{
  std::string directory;
  std::string path;
  Fixture()
  {
    char pattern[] = "/tmp/infinity-file-checkpoint-XXXXXX";
    char* created = ::mkdtemp(pattern);
    if (!created)
      throw std::runtime_error("mkdtemp failed");
    directory = created;
    path = directory + "/state.json";
  }
  ~Fixture() { fs::remove_all(directory); }
  void Seed(std::string_view content, mode_t mode = 0640)
  {
    std::ofstream output(path, std::ios::binary);
    output.write(content.data(), static_cast<std::streamsize>(content.size()));
    output.close();
    CHECK(output.good());
    CHECK(::chmod(path.c_str(), mode) == 0);
  }
  std::string Content() const
  {
    std::ifstream input(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(input), {});
  }
  struct stat Stat() const
  {
    struct stat value{};
    CHECK(::stat(path.c_str(), &value) == 0);
    return value;
  }
  void NoTemporaries() const
  {
    for (const auto& entry : fs::directory_iterator(directory))
      CHECK(entry.path().filename().string().find(".infinity-checkpoint-") != 0);
  }
};

enum class Failure
{
  None, Write, ZeroWrite, SyncTemporary, SyncExisting, SyncDirectory,
  Rename, CloseTemporary, CloseExisting, CloseFinalDirectory, Read, Chmod,
  Create, OpenExisting, Stat, Unlink, ListAttributes, SetAttribute,
};

class TestIo : public file::PosixIo
{
public:
  enum class Kind { Directory, Existing, Temporary };
  Failure failure{Failure::None};
  bool interruptOnce{false};
  bool shortIo{false};
  bool failCleanupUnlink{false};
  bool denyAncestorReads{false};
  bool denyFinalParentRead{false};
  int writes{0};
  int renames{0};
  int fileSyncs{0};
  int directorySyncs{0};
  int temporaryCreates{0};
  int closeFailures{0};
  int interruptions{0};
  std::map<int, Kind> descriptors;
  std::map<std::string, bool> interrupted;
  std::string observedBeforeRename;

  bool Interrupt(const char* operation)
  {
    if (!interruptOnce || interrupted[operation])
      return false;
    interrupted[operation] = true;
    ++interruptions;
    errno = EINTR;
    return true;
  }
  int Fail(int error) { errno = error; return -1; }
  int OpenAt(int dir, const char* path, int flags, mode_t mode) override
  {
    if (Interrupt("open"))
      return -1;
    if ((flags & O_DIRECTORY) && !(flags & O_PATH))
    {
      if ((denyAncestorReads && std::strcmp(path, ".") != 0) ||
          (denyFinalParentRead && std::strcmp(path, ".") == 0))
        return Fail(EACCES);
    }
    const Kind kind = (flags & O_DIRECTORY) ? Kind::Directory :
                      ((flags & O_CREAT) ? Kind::Temporary : Kind::Existing);
    if (kind == Kind::Temporary && failure == Failure::Create)
      return Fail(ENOSPC);
    if (kind == Kind::Existing && failure == Failure::OpenExisting)
      return Fail(EACCES);
    const int fd = PosixIo::OpenAt(dir, path, flags, mode);
    if (fd >= 0)
    {
      descriptors[fd] = kind;
      if (kind == Kind::Temporary)
        ++temporaryCreates;
    }
    return fd;
  }
  int Stat(int fd, struct stat* value) override
  {
    if (Interrupt("stat"))
      return -1;
    return failure == Failure::Stat ? Fail(EIO) : PosixIo::Stat(fd, value);
  }
  ssize_t Read(int fd, void* data, size_t size) override
  {
    if (Interrupt("read"))
      return -1;
    if (failure == Failure::Read)
      return Fail(EIO);
    return PosixIo::Read(fd, data, shortIo ? std::min<size_t>(size, 3) : size);
  }
  ssize_t Write(int fd, const void* data, size_t size) override
  {
    if (Interrupt("write"))
      return -1;
    ++writes;
    if (failure == Failure::Write && writes > 1)
      return Fail(ENOSPC);
    if (failure == Failure::ZeroWrite)
      return 0;
    return PosixIo::Write(fd, data, shortIo ? std::min<size_t>(size, 3) : size);
  }
  int Chmod(int fd, mode_t mode) override
  {
    if (Interrupt("chmod"))
      return -1;
    return failure == Failure::Chmod ? Fail(EPERM) : PosixIo::Chmod(fd, mode);
  }
  ssize_t ListAttributes(int fd, char* names, size_t size) override
  {
    return failure == Failure::ListAttributes ? Fail(EACCES) : PosixIo::ListAttributes(fd, names, size);
  }
  int SetAttribute(int fd, const char* name, const void* value, size_t size) override
  {
    return failure == Failure::SetAttribute ? Fail(EPERM) : PosixIo::SetAttribute(fd, name, value, size);
  }
  int Sync(int fd) override
  {
    if (Interrupt("sync"))
      return -1;
    const Kind kind = descriptors.at(fd);
    if (kind == Kind::Directory)
      ++directorySyncs;
    else
      ++fileSyncs;
    if ((kind == Kind::Directory && failure == Failure::SyncDirectory) ||
        (kind == Kind::Temporary && failure == Failure::SyncTemporary) ||
        (kind == Kind::Existing && failure == Failure::SyncExisting))
      return Fail(EIO);
    return PosixIo::Sync(fd);
  }
  int Close(int fd) override
  {
    const Kind kind = descriptors.at(fd);
    const bool fail =
        (kind == Kind::Temporary && failure == Failure::CloseTemporary) ||
        (kind == Kind::Existing && failure == Failure::CloseExisting) ||
        (kind == Kind::Directory && directorySyncs > 0 && failure == Failure::CloseFinalDirectory);
    descriptors.erase(fd);
    const int status = PosixIo::Close(fd); // The descriptor is consumed on Linux.
    if (fail)
    {
      ++closeFailures;
      return Fail(EINTR); // Must be recorded, never blindly retried.
    }
    return status;
  }
  int RenameAt(int fromDir, const char* from, int toDir, const char* to) override
  {
    ++renames;
    const int current = ::openat(toDir, to, O_RDONLY | O_CLOEXEC);
    if (current >= 0)
    {
      char buffer[1024];
      ssize_t count;
      while ((count = ::read(current, buffer, sizeof(buffer))) > 0)
        observedBeforeRename.append(buffer, static_cast<size_t>(count));
      CHECK(::close(current) == 0);
    }
    if (failure == Failure::Rename)
      return Fail(EIO);
    return PosixIo::RenameAt(fromDir, from, toDir, to);
  }
  int UnlinkAt(int dir, const char* path) override
  {
    return failure == Failure::Unlink || failCleanupUnlink ?
           Fail(EACCES) : PosixIo::UnlinkAt(dir, path);
  }
};

void ReplaceAndPreserveMode()
{
  Fixture f;
  f.Seed("old-state");
  const auto before = f.Stat();
  TestIo io;
  const auto result = file::SaveDirty(f.path, "new-state", io);
  CHECK(result.ok && result.replaced && result.dataAndDirectorySynced);
  CHECK(result.stage == file::Stage::None && result.error == 0);
  CHECK(f.Content() == "new-state");
  CHECK(io.observedBeforeRename == "old-state");
  CHECK(f.Stat().st_ino != before.st_ino);
  CHECK((f.Stat().st_mode & 07777) == 0640);
  CHECK(io.fileSyncs == 1 && io.directorySyncs == 1);
  CHECK(io.descriptors.empty());
  f.NoTemporaries();
}

void MatchingDirtyFileIsSyncedWithoutRewrite()
{
  for (const std::string& content : {std::string(), std::string("same-state\0binary", 17)})
  {
    Fixture f;
    f.Seed(content);
    const auto before = f.Stat();
    TestIo io;
    io.shortIo = true;
    const auto result = file::SaveDirty(f.path, content, io);
    const auto after = f.Stat();
    CHECK(result.ok && !result.replaced && !result.renameAttempted);
    CHECK(result.dataAndDirectorySynced);
    CHECK(before.st_ino == after.st_ino);
    CHECK(before.st_mtim.tv_sec == after.st_mtim.tv_sec);
    CHECK(before.st_mtim.tv_nsec == after.st_mtim.tv_nsec);
    CHECK(io.writes == 0 && io.temporaryCreates == 0 && io.renames == 0);
    CHECK(io.fileSyncs == 1 && io.directorySyncs == 1);
    CHECK(io.descriptors.empty());
  }
}

void ExtendedAttributesAndOwnershipSurviveReplacement()
{
  Fixture f;
  f.Seed("old");
  const char value[] = "private-checkpoint-metadata";
  CHECK(::setxattr(f.path.c_str(), "user.infinity.test", value, sizeof(value), 0) == 0);
  CHECK(::setxattr(f.path.c_str(), "user.infinity.empty", "", 0, 0) == 0);
  const auto before = f.Stat();
  CHECK(file::SaveDirty(f.path, "replacement").ok);
  CHECK(f.Stat().st_uid == before.st_uid && f.Stat().st_gid == before.st_gid);
  char actual[sizeof(value)]{};
  CHECK(::getxattr(f.path.c_str(), "user.infinity.test", actual, sizeof(actual)) == sizeof(value));
  CHECK(std::memcmp(actual, value, sizeof(value)) == 0);
  CHECK(::getxattr(f.path.c_str(), "user.infinity.empty", nullptr, 0) == 0);
  f.NoTemporaries();
}

void MetadataFailureNeverReplacesOriginal()
{
  for (const Failure failure : {Failure::ListAttributes, Failure::SetAttribute})
  {
    Fixture f;
    f.Seed("old");
    CHECK(::setxattr(f.path.c_str(), "user.infinity.test", "saved", 5, 0) == 0);
    TestIo io;
    io.failure = failure;
    const auto result = file::SaveDirty(f.path, "replacement", io);
    CHECK(!result.ok && !result.renameAttempted && io.renames == 0);
    CHECK(result.stage == (failure == Failure::ListAttributes ? file::Stage::ReadMetadata : file::Stage::PreserveMetadata));
    CHECK(f.Content() == "old" && io.descriptors.empty());
    f.NoTemporaries();
  }
}

void NewFileUsesPrivateMode()
{
  Fixture f;
  TestIo io;
  const auto result = file::SaveDirty(f.path, "new", io);
  CHECK(result.ok && result.replaced && result.dataAndDirectorySynced);
  CHECK(f.Content() == "new");
  CHECK((f.Stat().st_mode & 07777) == 0600);
  CHECK(io.descriptors.empty());
}

void FailuresBeforeRenamePreserveOriginal()
{
  const std::pair<Failure, file::Stage> cases[] = {
    {Failure::Write, file::Stage::WriteTemporary},
    {Failure::ZeroWrite, file::Stage::WriteTemporary},
    {Failure::SyncTemporary, file::Stage::SyncTemporary},
    {Failure::CloseTemporary, file::Stage::CloseTemporary},
    {Failure::CloseExisting, file::Stage::CloseExisting},
    {Failure::Read, file::Stage::ReadExisting},
    {Failure::Chmod, file::Stage::PreserveMode},
    {Failure::Create, file::Stage::CreateTemporary},
    {Failure::OpenExisting, file::Stage::OpenExisting},
    {Failure::Stat, file::Stage::StatExisting},
  };
  for (const auto& [failure, stage] : cases)
  {
    Fixture f;
    f.Seed("old-state");
    const auto before = f.Stat();
    TestIo io;
    io.failure = failure;
    io.shortIo = true;
    const auto result = file::SaveDirty(f.path, "new-state", io);
    CHECK(!result.ok && result.stage == stage && result.error != 0);
    CHECK(!result.replaced && !result.renameAttempted && !result.dataAndDirectorySynced);
    CHECK(f.Content() == "old-state" && f.Stat().st_ino == before.st_ino);
    CHECK(io.renames == 0 && io.descriptors.empty());
    if (failure == Failure::Write || failure == Failure::Create)
      CHECK(result.error == ENOSPC);
    if (failure == Failure::CloseTemporary || failure == Failure::CloseExisting)
      CHECK(io.closeFailures == 1 && result.error == EINTR);
    f.NoTemporaries();
  }
}

void RenameFailureIsNotAcknowledged()
{
  Fixture f;
  f.Seed("old");
  TestIo io;
  io.failure = Failure::Rename;
  const auto result = file::SaveDirty(f.path, "new", io);
  CHECK(!result.ok && result.stage == file::Stage::Rename && result.error == EIO);
  CHECK(result.renameAttempted && !result.replaced && !result.dataAndDirectorySynced);
  CHECK(f.Content() == "old"); // Injected syscall failed before mutation.
  CHECK(io.descriptors.empty());
  f.NoTemporaries();
}

void DirectorySyncFailureReportsVisibleButUnconfirmedReplacement()
{
  Fixture f;
  f.Seed("old");
  TestIo io;
  io.failure = Failure::SyncDirectory;
  const auto result = file::SaveDirty(f.path, "new", io);
  CHECK(!result.ok && result.stage == file::Stage::SyncDirectory && result.error == EIO);
  CHECK(result.replaced && result.renameAttempted && !result.dataAndDirectorySynced);
  CHECK(f.Content() == "new");
  CHECK(io.descriptors.empty());
  f.NoTemporaries();
  TestIo recovery;
  const auto retried = file::SaveDirty(f.path, "new", recovery);
  CHECK(retried.ok && !retried.replaced && retried.dataAndDirectorySynced);
  CHECK(recovery.fileSyncs == 1 && recovery.directorySyncs == 1);
}

void MatchingFileSyncFailuresAreNotAcknowledged()
{
  for (const Failure failure : {Failure::SyncExisting, Failure::SyncDirectory})
  {
    Fixture f;
    f.Seed("same");
    TestIo io;
    io.failure = failure;
    const auto result = file::SaveDirty(f.path, "same", io);
    CHECK(!result.ok && !result.replaced && !result.dataAndDirectorySynced);
    CHECK(result.stage == (failure == Failure::SyncExisting ?
                          file::Stage::SyncExisting : file::Stage::SyncDirectory));
    CHECK(result.error == EIO && io.writes == 0 && io.renames == 0);
    CHECK(io.descriptors.empty());
  }
}

void PrimaryAndCleanupErrorsRemainVisible()
{
  Fixture f;
  f.Seed("old-state");
  TestIo io;
  io.failure = Failure::Write;
  io.shortIo = true;
  io.failCleanupUnlink = true;
  const auto result = file::SaveDirty(f.path, "new-state", io);
  CHECK(!result.ok && result.stage == file::Stage::WriteTemporary && result.error == ENOSPC);
  CHECK(result.cleanupStage == file::Stage::RemoveTemporary && result.cleanupError == EACCES);
  CHECK(f.Content() == "old-state" && io.descriptors.empty());
}

void FinalDirectoryCloseIsChecked()
{
  Fixture f;
  f.Seed("old");
  TestIo io;
  io.failure = Failure::CloseFinalDirectory;
  const auto result = file::SaveDirty(f.path, "new", io);
  CHECK(!result.ok && result.stage == file::Stage::CloseDirectory && result.error == EINTR);
  CHECK(result.replaced && result.dataAndDirectorySynced);
  CHECK(io.closeFailures == 1 && io.descriptors.empty());
}

void InterruptedAndShortIoIsRetried()
{
  Fixture f;
  f.Seed("old-state");
  TestIo io;
  io.interruptOnce = true;
  io.shortIo = true;
  const auto result = file::SaveDirty(f.path, "new-state", io);
  CHECK(result.ok && f.Content() == "new-state");
  CHECK(io.interruptions == 6); // open, stat, read, write, chmod, fsync
  CHECK(io.writes == 3 && io.descriptors.empty());
}

void TraversesSearchOnlyAncestorsAndStillCommitsParent()
{
  Fixture f;
  f.Seed("old");
  TestIo io;
  io.denyAncestorReads = true;
  const auto replaced = file::SaveDirty(f.path, "new", io);
  CHECK(replaced.ok && replaced.replaced && replaced.dataAndDirectorySynced);
  CHECK(f.Content() == "new" && io.fileSyncs == 1 && io.directorySyncs == 1);
  const auto unchanged = file::SaveDirty(f.path, "new", io);
  CHECK(unchanged.ok && !unchanged.replaced && unchanged.dataAndDirectorySynced);
  CHECK(io.fileSyncs == 2 && io.directorySyncs == 2 && io.descriptors.empty());
  io.denyFinalParentRead = true;
  const auto denied = file::SaveDirty(f.path, "bad", io);
  CHECK(!denied.ok && denied.stage == file::Stage::OpenDirectory && denied.error == EACCES);
  CHECK(f.Content() == "new" && io.descriptors.empty());
  f.NoTemporaries();
}

void RejectsUnsafeTargets()
{
  Fixture f;
  f.Seed("original");
  const std::string link = f.directory + "/link";
  CHECK(::symlink(f.path.c_str(), link.c_str()) == 0);
  CHECK(!file::SaveDirty(link, "bad").ok);
  const std::string dangling = f.directory + "/dangling";
  CHECK(::symlink("missing", dangling.c_str()) == 0);
  CHECK(!file::SaveDirty(dangling, "bad").ok);
  const std::string fifo = f.directory + "/fifo";
  CHECK(::mkfifo(fifo.c_str(), 0600) == 0);
  const auto fifoResult = file::SaveDirty(fifo, "bad");
  CHECK(!fifoResult.ok && fifoResult.stage == file::Stage::ValidateExisting);
  const auto directoryResult = file::SaveDirty(f.directory, "bad");
  CHECK(!directoryResult.ok && directoryResult.stage == file::Stage::ValidateExisting);
  const std::string directoryLink = f.directory + "/directory-link";
  CHECK(::symlink(f.directory.c_str(), directoryLink.c_str()) == 0);
  CHECK(!file::SaveDirty(directoryLink + "/state.json", "bad").ok);
  CHECK(!file::SaveDirty(f.directory + "/../bad", "bad").ok);
  CHECK(!file::SaveDirty(std::string("/tmp/test\0truncated", 19), "bad").ok);
  CHECK(!file::SaveDirty("", "bad").ok);
  CHECK(!file::SaveDirty(f.directory + "/", "bad").ok);
  CHECK(f.Content() == "original");
  f.NoTemporaries();
}

void ProtocolRecordsUseFreshPrivateInodesAndRetainDurabilityGates()
{
  class ProtocolIo : public TestIo
  {
  public:
    int metadataReads{0};
    ssize_t ListAttributes(int, char*, size_t) override
    {
      ++metadataReads;
      return Fail(ENODATA);
    }
  };
  Fixture f;
  const std::string control = f.directory + "/.android-checkpoint";
  fs::create_directory(control);
  f.path = control + "/engine.json";
  f.Seed("retired-engine", 0640);
  const auto old = f.Stat();
  ProtocolIo io;
  const auto saved = file::SaveProtocolRecord(f.path, "current-engine", io);
  CHECK(saved.ok && saved.replaced && saved.dataAndDirectorySynced);
  CHECK(f.Content() == "current-engine" && f.Stat().st_ino != old.st_ino);
  CHECK((f.Stat().st_mode & 07777) == 0600);
  CHECK(io.metadataReads == 0 && io.fileSyncs == 1 && io.directorySyncs == 1);
  CHECK(io.descriptors.empty());

  for (Failure failure : {Failure::Write, Failure::ZeroWrite, Failure::SyncTemporary,
                         Failure::CloseTemporary, Failure::Rename, Failure::Chmod,
                         Failure::Create, Failure::OpenExisting, Failure::Stat,
                         Failure::CloseExisting})
  {
    f.Seed("previous-engine");
    const auto before = f.Stat();
    ProtocolIo failed;
    failed.failure = failure;
    failed.shortIo = true;
    const auto result = file::SaveProtocolRecord(f.path, "new-engine-longer", failed);
    CHECK(!result.ok && !result.replaced && !result.dataAndDirectorySynced);
    CHECK(f.Content() == "previous-engine" && f.Stat().st_ino == before.st_ino);
    CHECK(failed.metadataReads == 0 && failed.descriptors.empty());
    for (const auto& entry : fs::directory_iterator(control))
      CHECK(entry.path().filename().string().find(".infinity-checkpoint-") != 0);
  }
  ProtocolIo unsynced;
  unsynced.failure = Failure::SyncDirectory;
  const auto uncertain = file::SaveProtocolRecord(f.path, "visible-unconfirmed", unsynced);
  CHECK(!uncertain.ok && uncertain.replaced && !uncertain.dataAndDirectorySynced);
  CHECK(uncertain.stage == file::Stage::SyncDirectory && unsynced.descriptors.empty());
  ProtocolIo failedClose;
  failedClose.failure = Failure::CloseFinalDirectory;
  const auto closeFailure = file::SaveProtocolRecord(f.path, "closed-unconfirmed", failedClose);
  CHECK(!closeFailure.ok && closeFailure.stage == file::Stage::CloseDirectory);
  CHECK(failedClose.descriptors.empty());

  const auto rejected = file::SaveProtocolRecord(control + "/settings.xml", "bad", io);
  CHECK(!rejected.ok && rejected.stage == file::Stage::ValidatePath);
  CHECK(!file::SaveProtocolRecord(f.directory + "/engine.json", "bad", io).ok);
  const auto request = file::SaveProtocolRecord(control + "/request.json", "request", io);
  CHECK(request.ok && request.dataAndDirectorySynced);
  // The XML/user-state policy is still strict even inside the same directory.
  const auto strict = file::SaveDirty(f.path, "changed-user-state", io);
  CHECK(!strict.ok && strict.stage == file::Stage::ReadMetadata && strict.error == ENODATA);
  CHECK(f.Content() == "closed-unconfirmed");
  const std::string userFile = f.directory + "/user-settings.xml";
  { std::ofstream file(userFile); file << "keep-user-data"; }
  fs::remove(f.path);
  CHECK(::symlink(userFile.c_str(), f.path.c_str()) == 0);
  CHECK(!file::SaveProtocolRecord(f.path, "bad", io).ok);
  { std::ifstream file(userFile); std::string bytes; file >> bytes; CHECK(bytes == "keep-user-data"); }
}

void MetadataReadFailuresIdentifyOperationAndPreserveOriginal()
{
  class MetadataIo : public TestIo
  {
  public:
    bool failValue{false};
    ssize_t ListAttributes(int, char* names, size_t size) override
    {
      const char name[] = "user.checkpoint_test";
      if (names && size >= sizeof(name))
        std::memcpy(names, name, sizeof(name));
      return sizeof(name);
    }
    ssize_t GetAttribute(int, const char*, void*, size_t size) override
    {
      if (!failValue || size)
        return Fail(ENODATA);
      return 8;
    }
  };
  for (bool failValue : {false, true})
  {
    Fixture f;
    f.Seed("original");
    const auto before = f.Stat();
    MetadataIo io;
    io.failValue = failValue;
    const auto result = file::SaveDirty(f.path, "updated", io);
    CHECK(!result.ok && result.stage == file::Stage::ReadMetadata && result.error == ENODATA);
    CHECK(std::string(result.metadataOperation) == (failValue ? "fgetxattr_value" : "fgetxattr_size"));
    CHECK(result.metadataAttribute == "user.checkpoint_test");
    CHECK(!result.replaced && !result.renameAttempted && !result.dataAndDirectorySynced);
    CHECK(f.Content() == "original" && f.Stat().st_ino == before.st_ino);
    CHECK(io.renames == 0 && io.descriptors.empty());
    f.NoTemporaries();
  }
  Fixture f;
  f.Seed("original");
  TestIo io;
  io.failure = Failure::ListAttributes;
  const auto result = file::SaveDirty(f.path, "updated", io);
  CHECK(!result.ok && result.error == EACCES);
  CHECK(std::string(result.metadataOperation) == "flistxattr_size");
  CHECK(result.metadataAttribute.empty() && f.Content() == "original");
}

int main()
{
  try
  {
    ReplaceAndPreserveMode();
    MatchingDirtyFileIsSyncedWithoutRewrite();
    ExtendedAttributesAndOwnershipSurviveReplacement();
    MetadataFailureNeverReplacesOriginal();
    MetadataReadFailuresIdentifyOperationAndPreserveOriginal();
    ProtocolRecordsUseFreshPrivateInodesAndRetainDurabilityGates();
    NewFileUsesPrivateMode();
    FailuresBeforeRenamePreserveOriginal();
    RenameFailureIsNotAcknowledged();
    DirectorySyncFailureReportsVisibleButUnconfirmedReplacement();
    MatchingFileSyncFailuresAreNotAcknowledged();
    PrimaryAndCleanupErrorsRemainVisible();
    FinalDirectoryCloseIsChecked();
    InterruptedAndShortIoIsRetried();
    TraversesSearchOnlyAncestorsAndStillCommitsParent();
    RejectsUnsafeTargets();
    std::cout << "PASS: critical file checkpoint contracts and injected failures\n";
    return 0;
  }
  catch (const std::exception& error)
  {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
