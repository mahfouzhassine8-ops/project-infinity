/*
 *  Copyright (C) 2010-2018 Team Kodi
 *  This file is part of Kodi - https://kodi.tv
 *
 *  SPDX-License-Identifier: GPL-2.0-or-later
 *  See LICENSES/README.md for more information.
 */

#pragma once

class CBookmark;
class CFileItem;

class CSaveFileState
{
public:
  static void DoWork(CFileItem& item,
                     CBookmark& bookmark,
                     bool updatePlayCount);
  // Checks semantic readback and actual commit result. False is never a save
  // acknowledgment, even when a lower-level API historically returned void.
  static bool DoWorkChecked(CFileItem& item, CBookmark& bookmark, bool updatePlayCount);
};

