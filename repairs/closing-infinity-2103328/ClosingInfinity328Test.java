/* SPDX-License-Identifier: GPL-2.0-or-later */
package com.projectinfinity.kodi;

import static org.junit.Assert.*;
import android.app.Notification;
import android.content.Context;
import org.junit.Test;

public class ClosingInfinity328Test {
  @Test public void presentationUsesNewChannelWithoutChangingGuardSafety() {
    assertEquals("infinity_normal_close_v2", InfinityCloseGuardService.CHANNEL);
    assertEquals(150000L, InfinityCloseGuardService.MAX_PROTECTION_MS);
    assertEquals(Context.BIND_IMPORTANT, InfinityCloseGuardService.BIND_FLAGS);
    assertEquals(10936, InfinityCloseGuardService.NOTICE);
  }

  @Test public void progressCategoryRemainsPlatformNotificationContract() {
    assertEquals("progress", Notification.CATEGORY_PROGRESS);
    assertTrue(Notification.PRIORITY_HIGH > Notification.PRIORITY_DEFAULT);
  }
}
