#!/usr/bin/env python3
"""Apply only the approved Android Closing Infinity notification polish."""
import argparse
import hashlib
import json
from pathlib import Path

CANDIDATE = 2103328
PARENT = 2103327
PARENT_MAP = '7a40be4f2515ed1304af01debb25529298b1db043c1af20fce7397b368c31e15'
TARGET = 'tools/android/packaging/xbmc/src/InfinityCloseGuardService.java.in'
PREIMAGE = '7d72aeda0d4a43fa7f7256e0511928395eb9207554f94f65632ee521cbf2175b'
ALLOWED = {TARGET}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def map_digest(value: dict[str, str]) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())

def snapshot(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): sha(p.read_bytes())
        for p in root.rglob('*')
        if p.is_file() and '.git' not in p.relative_to(root).parts
    }

def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def once(text: str, old: str, new: str) -> str:
    require(text.count(old) == 1, 'Unexpected source preimage: ' + old[:100])
    return text.replace(old, new, 1)

def transform(text: str) -> str:
    text = once(
        text,
        '  static final String CHANNEL="infinity_normal_close";',
        '  static final String CHANNEL="infinity_normal_close_v2";'
    )
    old_channel = '''        NotificationChannel channel=new NotificationChannel(CHANNEL,"Infinity shutdown",NotificationManager.IMPORTANCE_LOW);
        channel.setShowBadge(false);manager.createNotificationChannel(channel);'''
    new_channel = '''        NotificationChannel channel=new NotificationChannel(CHANNEL,"Infinity closing",NotificationManager.IMPORTANCE_HIGH);
        channel.setShowBadge(false);
        channel.setSound(null,null);
        channel.enableVibration(false);
        channel.enableLights(false);
        manager.createNotificationChannel(channel);'''
    text = once(text, old_channel, new_channel)

    old_notice = '''      Notification.Builder builder=Build.VERSION.SDK_INT>=26?new Notification.Builder(this,CHANNEL):new Notification.Builder(this);
      Notification notice=builder.setSmallIcon(android.R.drawable.stat_notify_sync).setContentTitle("Closing Infinity")
          .setContentText("Finishing Kodi cleanup").setOngoing(true).setOnlyAlertOnce(true)
          .setContentIntent(PendingIntent.getActivity(this,NOTICE,open,pending)).build();'''
    new_notice = '''      Notification.Builder builder=Build.VERSION.SDK_INT>=26?new Notification.Builder(this,CHANNEL):new Notification.Builder(this);
      if(Build.VERSION.SDK_INT<26)builder.setPriority(Notification.PRIORITY_HIGH);
      Notification notice=builder.setSmallIcon(R.drawable.notif_icon).setContentTitle("Closing Infinity…")
          .setContentText("Saving state and finishing cleanup")
          .setSubText("Saving • Services • Scripts • Cleanup")
          .setProgress(0,0,true).setOngoing(true).setOnlyAlertOnce(true)
          .setCategory(Notification.CATEGORY_PROGRESS).setVisibility(Notification.VISIBILITY_PUBLIC)
          .setColor(0xFF39BEE8)
          .setContentIntent(PendingIntent.getActivity(this,NOTICE,open,pending)).build();'''
    text = once(text, old_notice, new_notice)
    return text

def apply(source: Path, proof: Path, receipt: Path) -> dict:
    parent = json.loads(proof.read_text())
    expected = parent['after']
    require(parent.get('candidate') == PARENT, 'Wrong 2103327 Android proof')
    require(map_digest(expected) == PARENT_MAP, 'Wrong complete 2103327 Android source map')
    before = snapshot(source)
    require(before == expected, 'Android source is not exact passed 2103327')
    require(before.get(TARGET) == PREIMAGE, 'Unexpected CloseGuard preimage')

    target = source / TARGET
    target.write_text(transform(target.read_text()))
    after = snapshot(source)
    changed = {name for name in before.keys() | after.keys()
               if before.get(name) != after.get(name)}
    require(changed == ALLOWED, 'Undeclared Android source delta: ' + repr(sorted(changed)))
    require(before.keys() == after.keys(), 'Android source file set changed')

    result = {
        'candidate': CANDIDATE,
        'parent': PARENT,
        'kind': 'android-closing-ui-polish',
        'before': before,
        'after': after,
        'changed': sorted(changed),
        'native_changed': False,
        'shutdown_algorithm_changed': False,
        'notification_channel': 'infinity_normal_close_v2',
        'physical_device_verified': False,
        'locked': False,
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result

def verify(source: Path, receipt: Path) -> None:
    result = json.loads(receipt.read_text())
    require(result['candidate'] == CANDIDATE and result['changed'] == sorted(ALLOWED),
            'Wrong Closing Infinity receipt')
    require(snapshot(source) == result['after'], 'Android source changed after validation')

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['apply', 'verify'])
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--proof', type=Path)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'apply':
        require(args.proof is not None, 'apply requires --proof')
        apply(args.source, args.proof, args.receipt)
    else:
        verify(args.source, args.receipt)
    print('PASS: exact 2103327 parent; only Closing Infinity Android notification source changed')

if __name__ == '__main__':
    main()
