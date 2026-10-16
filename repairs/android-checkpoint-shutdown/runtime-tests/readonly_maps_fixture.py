"""Disposable-emulator add-on only; never packaged into a Fold APK.

Exercise the exact ordinary Python read/flush/close that failed on TEST2.
All receipts below are observations, never checkpoint/termination authority.
"""
import json
import os
import stat
import xbmcaddon
import xbmcvfs

result = {"addon": xbmcaddon.Addon().getAddonInfo("id"), "pid": os.getpid()}
with open('/proc/self/maps', encoding='utf-8') as maps:
    descriptor = maps.fileno()
    identity = os.fstat(descriptor)
    # Observe kernel flags without issuing a descriptor-control audit event.
    # The production guard deliberately treats unclassified fcntl calls as
    # unknown effects; diagnostic instrumentation must not add one itself.
    with open('/proc/self/fdinfo/' + str(descriptor), encoding='utf-8') as info:
        fields = dict(line.rstrip().split(':', 1) for line in info if ':' in line)
    assert int(fields['ino']) == identity.st_ino
    result.update(descriptor=descriptor, flags=int(fields['flags'], 8),
                  flags_source='proc_fdinfo', fdinfo_inode=int(fields['ino']),
                  mode=maps.mode, writable=maps.writable(),
                  descriptor_target=os.readlink('/proc/self/fd/' + str(descriptor)),
                  device=identity.st_dev, inode=identity.st_ino, stat_mode=identity.st_mode,
                  regular_file=stat.S_ISREG(identity.st_mode), read_succeeded=bool(maps.readline()))
    maps.flush()
result['read_flush_close_completed'] = True
with open('/proc/mounts', encoding='utf-8') as mounts:
    result['proc_mount_types'] = [line.split()[2] for line in mounts
                                 if len(line.split()) >= 3 and line.split()[1] == '/proc']
profile = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
os.makedirs(profile, exist_ok=True)
with open(os.path.join(profile, 'observed-readonly-maps.json'), 'w', encoding='utf-8') as output:
    json.dump(result, output, sort_keys=True)
