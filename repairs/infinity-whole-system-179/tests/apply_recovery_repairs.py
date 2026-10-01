from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'candidate/script.infinity.commandcenter/common.py';s=p.read_text()
s=s.replace("wanted = ('16x9','20x9','6x5','portrait','5x6')","wanted = ('16x9','20x9','6x5','portrait','5x6','fallback')")
a=s.index('def _skin_version(');b=s.index('\ndef _health_contract',a)
s=s[:a]+'''def _skin_version(root: Path | None = None) -> str:
    if root is not None:
        # A stale integration JSON must never authorize an older UI restore.
        import xml.etree.ElementTree as ET
        try:
            record = ET.parse(root / 'addon.xml').getroot()
            version = str(record.get('version', '')).strip()
            metadata = _skin_manifest(root)
            protected = read_json(root / 'Infinity-Protected-Manifest.json', {})
            if (record.get('id') != 'skin.infinity.diggz' or not version or
                    metadata.get('skin_version') != version or
                    protected.get('skin_version') != version):
                return ''
            return version
        except Exception:
            return ''
    try:
        return str(xbmcaddon.Addon('skin.infinity.diggz').getAddonInfo('version') or '').strip()
    except Exception:
        return ''


def _skin_identity(root: Path) -> str:
    if not _skin_version(root):
        return ''
    try:
        digest = hashlib.sha256()
        for name in ('addon.xml', 'infinity-skin.json', 'Infinity-Protected-Manifest.json'):
            path = root / name
            if path.is_symlink():
                return ''
            value = path.read_bytes()
            digest.update(name.encode('utf-8') + b'\\0' + str(len(value)).encode('ascii') + b'\\0' + value)
        return digest.hexdigest()
    except Exception:
        return ''

''' + s[b:]
needle="    result['skin_version'] = _skin_version(root)"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n    if not result['skin_version']:\n        result['healthy'] = False\n        result['issues'].append('Skin identity metadata disagrees or is unavailable; automatic restore is blocked.')")
a=s.index('def backup_ui_if_healthy(');b=s.index('\ndef self_heal_ui',a)
s=s[:a]+'''def backup_ui_if_healthy(force=False):
    state = ui_health()
    root = _skin_root()
    identity = _skin_identity(root) if root is not None else ''
    if not state.get('healthy') or not identity:
        return False, state
    profile = addon_profile()
    profile.mkdir(parents=True, exist_ok=True)
    target = profile / UI_BACKUP_DIR
    stage = None
    previous = None
    lock = None
    try:
        # Android/Linux: serialize independent service and explicit tool calls.
        # An unavailable lock never grants permission to replace a backup.
        import fcntl
        lock = (profile / (UI_BACKUP_DIR + '.lock')).open('a')
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        if target.is_symlink():
            raise OSError('Unsafe backup target')
        current_version = _skin_version(root)
        old = read_json(target / 'manifest.json', {})
        old_hashes = old.get('sha256', {})
        if (not force and old.get('identity') == identity and
                old.get('skin_version') == current_version and
                isinstance(old_hashes, dict) and old_hashes and
                all(not Path(rel).is_absolute() and '..' not in Path(rel).parts and
                    not (target / rel).is_symlink() and _file_sha256(target / rel) == value
                    for rel, value in old_hashes.items())):
            return True, state
        stage = Path(tempfile.mkdtemp(prefix=UI_BACKUP_DIR+'.stage-', dir=str(profile)))
        critical, _required, schema, _manifest = _health_contract(root)
        hashes = {}
        for folder in _skin_resolution_dirs(root):
            if folder.is_symlink():
                raise OSError('Unsafe skin folder')
            for name in critical:
                source = folder / name
                if not source.is_file():
                    continue
                if source.is_symlink():
                    raise OSError('Unsafe skin source')
                rel = folder.name + '/' + name
                expected = _file_sha256(source)
                dest = stage / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                if not expected or _file_sha256(dest) != expected or _file_sha256(source) != expected:
                    raise OSError('UI changed during backup')
                hashes[rel] = expected
        if not hashes or _skin_identity(root) != identity:
            raise OSError('UI identity changed during backup')
        atomic_json(stage / 'manifest.json', {
            'schema': 3, 'skin': 'skin.infinity.diggz', 'skin_version': current_version,
            'identity': identity, 'health_contract_schema': schema, 'created': int(time.time()),
            'checked': state.get('checked', []), 'files': list(hashes), 'sha256': hashes,
        })
        if target.exists():
            import uuid
            previous = profile / (UI_BACKUP_DIR + '.previous-' + uuid.uuid4().hex)
            os.replace(target, previous)
        try:
            os.replace(stage, target)
            stage = None
        except Exception:
            if previous is not None and not target.exists():
                os.replace(previous, target)
            raise
        # Keep the previous verified backup; never delete it before replacement.
        log('UI known-good backup refreshed for skin version ' + current_version)
        return True, state
    except Exception as error:
        state = dict(state)
        state['backup_error'] = type(error).__name__
        log('UI backup not replaced: ' + type(error).__name__, xbmc.LOGWARNING)
        return False, state
    finally:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)
        if lock is not None:
            lock.close()

''' + s[b:]
s=s.replace('''def self_heal_ui():
    current = ui_health()''','''def self_heal_ui():
    try:
        if xbmc.Player().isPlaying():
            return False, 'Stop playback before repairing UI files. No files were changed.'
    except Exception:
        return False, 'Playback state is unavailable; no UI files were changed.'
    current = ui_health()''')
s=s.replace('''        backup_ui_if_healthy(force=False)
        return True, 'Critical Infinity UI files are healthy. Known-good UI backup matches the current skin version.' ''','''        ok, _state = backup_ui_if_healthy(force=False)
        return ok, ('Critical Infinity UI files are healthy. Known-good UI backup matches the current skin identity.'
                    if ok else 'Critical UI is healthy, but its backup could not be verified or refreshed.') ''') if False else s
old="""        backup_ui_if_healthy(force=False)
        return True, 'Critical Infinity UI files are healthy. Known-good UI backup matches the current skin version.'"""
new="""        ok, _state = backup_ui_if_healthy(force=False)
        return ok, ('Critical Infinity UI files are healthy. Known-good UI backup matches the current skin identity.'
                    if ok else 'Critical UI is healthy, but its backup could not be verified or refreshed.')"""
assert s.count(old)==1;s=s.replace(old,new)
old="    if not current_version or not backup_version or backup_version != current_version:"
new="    identity = _skin_identity(root)\n    if (not current_version or not backup_version or backup_version != current_version or\n            not identity or manifest.get('identity') != identity):"
assert s.count(old)==1;s=s.replace(old,new)
old="""        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1"""
new="""        if (source.is_symlink() or source.parent.is_symlink() or target.is_symlink() or
                target.parent.is_symlink() or _skin_identity(root) != identity or xbmc.Player().isPlaying()):
            unavailable.append(rel_text)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix='.infinity-ui-restore-', dir=str(target.parent))
        os.close(fd)
        try:
            shutil.copy2(source, temp_name)
            if _file_sha256(Path(temp_name)) != expected:
                unavailable.append(rel_text)
                continue
            os.replace(temp_name, target)
            copied += 1
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)"""
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s)
