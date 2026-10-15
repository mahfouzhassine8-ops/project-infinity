"""Bounded, read-only support bundle builder. No Kodi imports or network I/O."""
from pathlib import Path
import hashlib
import json
import zipfile

MAX_FILE = 4 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_FILES = 2500


def contained_files(root, extensions):
    """Never follow symlink directories or files, including aliases to userdata."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        return
    todo = [root]
    while todo:
        folder = todo.pop()
        for path in sorted(folder.iterdir(), key=lambda p: p.name):
            if path.is_symlink() or path.name.startswith('.'):
                continue
            if path.is_dir():
                if path.name not in ('addon_data', 'userdata', 'cache', 'packages'):
                    todo.append(path)
            elif path.is_file() and path.suffix.lower() in extensions:
                yield path


def make_report(destination, skin_root, skin_id, settings=None, health_root=None,
                native_roots=(), include_native_traces=False, logcat_root=None, logcat_status=None):
    destination = Path(destination)
    skin_root = Path(skin_root)
    if destination.exists():
        raise ValueError('Refusing to overwrite an existing report')
    if not skin_root.is_dir() or not (skin_root / 'addon.xml').is_file():
        raise ValueError('The active skin source directory could not be read')
    if destination.resolve() == skin_root.resolve() or skin_root.resolve() in destination.resolve().parents:
        raise ValueError('Report must be saved outside the skin directory')
    destination.parent.mkdir(parents=True, exist_ok=True)
    receipt = {'schema': 1, 'active_skin_id': skin_id, 'settings': settings or {},
               'settings_scope': 'appearance values only; no account configuration',
               'source_modified': False, 'network_upload': False,
               'crash_cause_confirmed': False, 'logcat': logcat_status or {'status': 'not_requested'},
               'native_traces_opted_in': include_native_traces,
               'included': [], 'omitted': [], 'limits': {'bytes': MAX_TOTAL, 'per_file': MAX_FILE,
                                                        'files': MAX_FILES}}
    total = 0
    seen = set()
    temporary = destination.with_name(destination.name + '.partial')
    if temporary.exists():
        raise ValueError('A partial report already exists')
    try:
        with zipfile.ZipFile(temporary, 'x', zipfile.ZIP_DEFLATED) as archive:
            def add(path, name):
                nonlocal total
                if name in seen:
                    return
                if path.is_symlink():
                    receipt['omitted'].append({'file': name, 'reason': 'symlink'})
                    return
                size = path.stat().st_size
                if size > MAX_FILE or size + total > MAX_TOTAL or len(seen) >= MAX_FILES:
                    receipt['omitted'].append({'file': name, 'reason': 'size_or_count_limit'})
                    return
                # A bounded read also handles files growing after stat().
                with path.open('rb') as handle:
                    data = handle.read(MAX_FILE + 1)
                if len(data) > MAX_FILE or len(data) + total > MAX_TOTAL:
                    receipt['omitted'].append({'file': name, 'reason': 'file_grew'})
                    return
                archive.writestr(name, data)
                seen.add(name)
                total += len(data)
                receipt['included'].append({'file': name, 'bytes': len(data),
                                            'sha256': hashlib.sha256(data).hexdigest()})

            # Skin definitions only: no artwork, texture bundles, font binaries,
            # media files, databases or user addon settings.
            for path in contained_files(skin_root, {'.xml'}):
                add(path, 'active-skin/' + path.relative_to(skin_root).as_posix())
            if health_root is not None:
                health_root = Path(health_root)
                for path in contained_files(health_root, {'.py', '.xml'}):
                    add(path, 'health-center-source/' + path.relative_to(health_root).as_posix())
            for root in native_roots:
                root = Path(root)
                if root.is_symlink() or not root.is_dir():
                    continue
                metadata = root / 'android-exit-info.json'
                if metadata.is_file():
                    # Metadata has a fixed allowlisted collection schema.
                    add(metadata, 'native/android-exit-info.json')
                if include_native_traces:
                    for trace in sorted(root.glob('exit-*.trace'), reverse=True)[:4]:
                        import re
                        if re.fullmatch(r'exit-\d+-\d+-\d+\.trace', trace.name):
                            add(trace, 'native/' + trace.name)
            if include_native_traces and logcat_root is not None:
                logcat = Path(logcat_root) / 'same-uid-crash-logcat.txt'
                if logcat.is_file():
                    add(logcat, 'native/same-uid-crash-logcat.txt')
            receipt['total_input_bytes'] = total
            receipt['native_evidence_present'] = any(n.startswith('native/') for n in seen)
            receipt['complete_within_limits'] = not receipt['omitted']
            archive.writestr('report.json', json.dumps(receipt, indent=2))
            archive.writestr('READ-ME.txt',
                'Infinity support report. This helper did not modify your setup or upload data.\n'
                'The active-skin folder is the installed skin XML, not a replacement skin.\n'
                'Account settings, full Kodi logs, media and font binaries are excluded.\n'
                'Skin XML, add-on source and optional native traces can contain embedded URLs or private data. Review before sharing.\n'
                'Missing native evidence does not exclude an Android/native crash.\n'
                'This report is not a crash fix or an installable player-protection update.\n')
        # Sanity check that what the user receives is a real populated archive.
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None or not receipt['included']:
                raise ValueError('Support archive validation failed')
        temporary.rename(destination)
        return receipt
    finally:
        if temporary.exists():
            temporary.unlink()
