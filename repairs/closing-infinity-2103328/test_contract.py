#!/usr/bin/env python3
"""Host contracts for the 2103328 Android-only shutdown presentation change."""
import argparse
from pathlib import Path

TARGET='tools/android/packaging/xbmc/src/InfinityCloseGuardService.java.in'

def require(ok,msg):
    if not ok: raise AssertionError(msg)

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
text=(a.source/TARGET).read_text()

for token in [
    'static final long MAX_PROTECTION_MS=150000;',
    'static final int BIND_FLAGS=Context.BIND_IMPORTANT;',
    'return START_NOT_STICKY;',
    'stopForeground(true);stopSelf();',
    'stopService(new Intent(this,InfinityCloseNativeLease.class))',
    'InfinityKodiShutdown.ownerAlive',
    'guard.time_bound_cleanup_unconfirmed',
]:
    require(token in text,'Preserved guard contract missing: '+token)

for token in [
    'static final String CHANNEL="infinity_normal_close_v2";',
    'NotificationManager.IMPORTANCE_HIGH',
    'channel.setSound(null,null);',
    'channel.enableVibration(false);',
    'channel.enableLights(false);',
    'setSmallIcon(R.drawable.notif_icon)',
    'setContentTitle("Closing Infinity…")',
    'setContentText("Saving state and finishing cleanup")',
    'setSubText("Saving • Services • Scripts • Cleanup")',
    'setProgress(0,0,true)',
    'setCategory(Notification.CATEGORY_PROGRESS)',
    'setVisibility(Notification.VISIBILITY_PUBLIC)',
    'setColor(0xFF39BEE8)',
]:
    require(token in text,'Approved notification contract missing: '+token)

for forbidden in ['killProcess(', 'forceStopPackage(', 'System.exit(', 'BIND_AUTO_CREATE',
                  'MAX_PROTECTION_MS=10000', 'MAX_PROTECTION_MS=30000']:
    require(forbidden not in text,'Prohibited shutdown shortcut introduced: '+forbidden)

require(text.count('startForeground(')==3,'Foreground service API branches unexpectedly changed')
require(text.count('new NotificationChannel(')==1,'Unexpected notification-channel count')
require(text.count('bindService(')==1,'Native lease binding count changed')
print('PASS: Closing Infinity notification polish preserves 2103327 shutdown ownership and safety contracts')
