/*
 * Copyright (C) 2026 Infinity contributors
 * SPDX-License-Identifier: GPL-2.0-or-later
 */
#pragma once

#include <cstdint>
#include <string>

namespace KODI::FILEPREVIEW
{
constexpr int PREVIEW_CONTROL = 9410;
constexpr int CONFIRM_CONTROL = 9411;
constexpr const char* SCRIPT = "special://skin/resources/lib/infinity_file_preview.py";

struct Request
{
  uint64_t nonce{0};
  std::string path;
  bool folder{false};
};

inline bool IsZipInstallContext(const std::string& mask,
                               const std::string& heading,
                               const std::string& installHeading)
{
  return mask == "*.zip" && !heading.empty() && heading == installHeading;
}

inline bool CanOpen(bool installContext, bool optedIn, bool validSelection,
                    const std::string& path)
{
  return installContext && optedIn && validSelection && !path.empty() && path.size() <= 8192;
}

inline bool ShouldPrimePointer(bool rightClick, bool installContext, bool optedIn, bool pending)
{
  return rightClick && installContext && optedIn && !pending;
}

inline bool IsZip(const std::string& path)
{
  const auto length = path.size();
  return length >= 4 && path[length - 4] == '.' &&
         (path[length - 3] == 'z' || path[length - 3] == 'Z') &&
         (path[length - 2] == 'i' || path[length - 2] == 'I') &&
         (path[length - 1] == 'p' || path[length - 1] == 'P');
}

inline bool CanConfirm(const Request& request, const std::string& acceptedNonce,
                       bool installContext, bool optedIn, bool validSelection,
                       const std::string& selectedPath, bool selectedFolder)
{
  return CanOpen(installContext, optedIn, validSelection, selectedPath) && request.nonce != 0 &&
         acceptedNonce == std::to_string(request.nonce) && request.path == selectedPath &&
         !request.folder && !selectedFolder && IsZip(selectedPath);
}
} // namespace KODI::FILEPREVIEW
