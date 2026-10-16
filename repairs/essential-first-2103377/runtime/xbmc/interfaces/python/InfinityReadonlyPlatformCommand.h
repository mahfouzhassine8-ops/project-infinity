/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once
#include <cstdlib>
#include <cstring>
#include <limits.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <unistd.h>

namespace InfinityReadonlyPlatformCommand
{
// AOSP builds the same uname applet in toybox and toybox_vendor. This is
// deliberately an identity check for that one OS applet, not permission for
// arbitrary executables on a read-only partition. Argument, environment and
// inherited-output checks remain mandatory in ReadonlyForkExec.
inline bool VendorUname(const char* path)
{
  if (!path || std::strcmp(path, "/vendor/bin/uname") != 0) return false;
  struct stat link{}, target{}, again{};
  struct statvfs mount{}, resolvedMount{};
  char resolved[PATH_MAX]{}, destination[PATH_MAX]{};
  if (::lstat(path, &link) != 0 || !S_ISLNK(link.st_mode) || link.st_uid != 0 ||
      ::statvfs(path, &mount) != 0 || !(mount.f_flag & ST_RDONLY) ||
      !::realpath(path, resolved) || std::strcmp(resolved, "/vendor/bin/toybox_vendor") != 0)
    return false;
  const auto length = ::readlink(path, destination, sizeof(destination) - 1);
  if (length <= 0 || (std::strcmp(destination, "toybox_vendor") != 0 &&
      std::strcmp(destination, "/vendor/bin/toybox_vendor") != 0)) return false;
  if (::lstat(resolved, &target) != 0 || !S_ISREG(target.st_mode) || target.st_uid != 0 ||
      !(target.st_mode & S_IXUSR) || (target.st_mode & (S_IWGRP | S_IWOTH | S_ISUID | S_ISGID)) ||
      ::statvfs(resolved, &resolvedMount) != 0 || !(resolvedMount.f_flag & ST_RDONLY) ||
      ::stat(path, &again) != 0 || target.st_dev != again.st_dev || target.st_ino != again.st_ino)
    return false;
  return true;
}
}
