"""Evidence-only assessment of Android ARM translation's /proc/self/maps descriptor.

This analysis NEVER authorizes Close or treats an emulator failure as a pass.
The OS/guest identity mismatch must be treated as an unresolved validation
blocker pending direct ARM64 qualification. No runtime or native policy edits.
"""
import os

GUEST_MAPS = '/memfd:[guest /proc/self/maps] (deleted)'
BLOCKER = 'native_admission: protected_durability_failed:' + GUEST_MAPS


def _flags(raw):
    for line in str(raw).splitlines():
        if line.startswith('flags:'):
            try:
                return int(line.split(':', 1)[1].strip(), 8)
            except ValueError:
                return None
    return None


def _kernel_stat(raw):
    try:
        dev, ino, mode, nlink = str(raw).strip().split(':')
        return int(dev), int(ino), int(mode, 16), int(nlink)
    except (ValueError, TypeError):
        return None


def assess(evidence, receipt):
    """Describe this one captured descriptor; never certify save durability.

    Returns a structured, non-authoritative, fail-closed explanation. The only
    positive state means a *translation mismatch was observed*, not that a
    user-data write can safely be ignored or a Close accepted.
    """
    outcome = {'classification': 'insufficient_evidence',
               'durable_close_verified': False,
               'can_override_native_protection': False,
               'fold_accepted': False}
    if not isinstance(evidence, dict) or not isinstance(receipt, dict):
        return outcome
    if receipt.get('phase') != 'CHECKPOINT_FAILED' or receipt.get('error') != BLOCKER:
        return outcome
    if not all(evidence.get(k) is True for k in ('captured', 'terminal_confirmed', 'same_live_owner_after')):
        return outcome
    pre, post, kernel = (evidence.get(k) for k in ('pre', 'post', 'kernel'))
    if not all(isinstance(v, dict) for v in (pre, post, kernel)):
        return outcome
    if (pre.get('android') is not True or pre.get('mode') != 'r' or
            pre.get('writable') is not False or pre.get('read_succeeded') is not True or
            pre.get('stream_type') != {'module': '_io', 'name': 'TextIOWrapper'} or
            pre.get('errors') != [] or post.get('errors') != [] or
            post.get('read_flush_close_completed') is not True or
            post.get('closed') is not True or post.get('held') is not False or
            post.get('release_received') is not True or
            post.get('identity_stable_while_held') is not True):
        return outcome
    if any(pre.get(k) != post.get(k) for k in ('owner', 'nonce', 'pid', 'uid', 'descriptor')):
        return outcome
    before, after = pre.get('before'), post.get('after_hold')
    if not isinstance(before, dict) or not isinstance(after, dict) or before != after:
        return outcome
    if before.get('readlink') != GUEST_MAPS or before.get('regular_file') is not True:
        return outcome
    labels = ('readlink_before', 'readlink_after', 'stat', 'fdinfo')
    if any(not isinstance(kernel.get(k), dict) or kernel[k].get('returncode') != 0 for k in labels):
        return outcome
    if any(kernel[k].get('stdout', '').strip() != GUEST_MAPS for k in labels[:2]):
        return outcome
    info = _kernel_stat(kernel['stat'].get('stdout'))
    guest_flags, kernel_flags = _flags(before.get('fdinfo')), _flags(kernel['fdinfo'].get('stdout'))
    if info is None or guest_flags is None or kernel_flags is None:
        return outcome
    dev, ino, mode, links = info
    if (guest_flags & os.O_ACCMODE) != os.O_RDWR or (kernel_flags & os.O_ACCMODE) != os.O_RDWR:
        return outcome
    if ((dev, ino) == (before.get('dev'), before.get('ino')) or
            not isinstance(before.get('dev'), int) or not isinstance(before.get('ino'), int) or
            links != 0 or (mode & 0o170000) != 0o100000):
        return outcome
    outcome.update(classification='emulator_translated_descriptor_mismatch_observed',
                   guest_stream_readonly=True, kernel_descriptor_readwrite=True,
                   guest_kernel_object_identity_differs=True,
                   identity_stable_during_observation=True,
                   required_next_gate='direct_arm64_android17_and_physical_fold_close',
                   explanation='Correlated metadata mismatch, NOT authorization to ignore this path or to pass shutdown')
    return outcome
