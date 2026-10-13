# SPDX-License-Identifier: GPL-2.0-or-later
"""One-shot, local-only installed-code evidence. Never imports the inspected add-on.

Exports original file hashes plus a privacy-filtered AST, NOT byte-exact source.
No source strings, comments, unknown identifiers, frame locals, URLs, settings,
playlist contents, database contents or exception messages leave this collector.
This module is diagnostic only; it has no checkpoint or task-removal authority.
"""
import ast
import hashlib
import io
import json
import os
import stat
import sys
import time
import tokenize
import zipfile
from xml.etree import ElementTree

ADDON_ID = 'plugin.video.playlistbrowser'
SOURCE_NAMES = ('addon.xml', 'main.py', 'service.py')
MAX_FILE_BYTES = 524288
MAX_AST_NODES = 16000
MAX_FRAMES = 128
MAX_DEPTH = 80
MAX_OUTPUT_BYTES = 4000000

# Only fixed library names and operation names can be exported verbatim.
SAFE_SYMBOLS = frozenset(('xbmc xbmcvfs xbmcaddon xbmcgui requests urllib '
    'request parse os path time threading json socket pathlib sqlite3 builtins '
    'contextlib re io codecs ssl sys File open read readBytes readinto readline '
    'readlines write writelines close flush fsync seek tell exists getsize stat '
    'copy rename delete mkdir mkdirs rmdir listdir translatePath Monitor '
    'abortRequested waitForAbort sleep get post head Session urlopen Request '
    'urlsplit urlparse join isfile isdir basename dirname normpath realpath '
    'Lock RLock Thread start run join Event wait is_set set clear connect '
    'commit rollback execute executemany cursor Addon getAddonInfo getSetting '
    'getSettingBool getSettingInt setSetting setSettingBool setSettingInt '
    'loads dumps load dump split splitlines strip replace lower upper append '
    'extend update items keys values get len range enumerate str bytes int '
    'float bool list tuple dict set Exception BaseException OSError IOError '
    'RuntimeError ValueError TypeError TimeoutError finally timeout self '
    '__init__ __enter__ __exit__ __name__').split())
SAFE_IMPORTS = frozenset(('xbmc xbmcvfs xbmcaddon xbmcgui requests urllib '
    'urllib.request urllib.parse os os.path time threading json socket pathlib '
    'sqlite3 builtins contextlib re io codecs ssl sys').split())
SAFE_POINTS = frozenset(('xbmc.service', 'xbmc.python.pluginsource',
                         'xbmc.python.script', 'xbmc.addon.metadata'))
SAFE_DEPENDENCIES = frozenset(('xbmc.python', 'xbmc.addon', 'xbmc.gui', ADDON_ID))


class ProbeError(Exception):
    """Contains a fixed error code only, never source data or a filesystem path."""


def _safe_local_root(path):
    if not isinstance(path, str) or not os.path.isabs(path) or '\x00' in path:
        raise ProbeError('local_absolute_directory_required')
    absolute = os.path.abspath(path)
    if os.path.realpath(absolute) != absolute:
        raise ProbeError('linked_directory_refused')
    if not os.path.isdir(absolute):
        raise ProbeError('directory_unavailable')
    return absolute


def _open_local_directory(path):
    """Pin every path component without following links, including ancestors."""
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise ProbeError('safe_open_unavailable')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, 'O_CLOEXEC', 0)
    current = os.open(os.sep, flags)
    try:
        for component in path.split(os.sep):
            if not component:
                continue
            child = os.open(component, flags, dir_fd=current)
            os.close(current)
            current = child
        return current
    except BaseException:
        os.close(current)
        raise


def read_source(root, name):
    """Allowlist and O_NOFOLLOW: never follow an installed file into userdata."""
    root = _safe_local_root(root)
    if name not in SOURCE_NAMES:
        raise ProbeError('source_name_not_allowed')
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise ProbeError('safe_open_unavailable')
    directory = _open_local_directory(root)
    fd = None
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ProbeError('nonregular_source_refused')
        if before.st_nlink != 1:
            raise ProbeError('hardlinked_source_refused')
        if before.st_size > MAX_FILE_BYTES:
            raise ProbeError('source_size_bound')
        chunks = []
        length = 0
        while True:
            block = os.read(fd, min(65536, MAX_FILE_BYTES + 1 - length))
            if not block:
                break
            chunks.append(block)
            length += len(block)
            if length > MAX_FILE_BYTES:
                raise ProbeError('source_size_bound')
        after = os.fstat(fd)
        if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ProbeError('source_changed_during_read')
        return b''.join(chunks)
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)


class StructureFilter(ast.NodeTransformer):
    """Pseudonymize ALL identifiers except fixed API vocabulary; remove literals."""
    def __init__(self):
        self.symbols = {}
        self.imports = set()

    def symbol(self, value):
        if value in SAFE_SYMBOLS:
            return value
        if value not in self.symbols:
            self.symbols[value] = 'symbol_%d' % (len(self.symbols) + 1)
        return self.symbols[value]

    def generic_visit(self, node):
        if isinstance(node, ast.Constant):
            # Boolean/None preserve control-flow structure. All other values vanish.
            value = node.value if node.value is None or type(node.value) is bool else '[REDACTED]'
            return ast.copy_location(ast.Constant(value=value), node)
        for field, value in list(ast.iter_fields(node)):
            if isinstance(value, ast.AST):
                setattr(node, field, self.visit(value))
            elif isinstance(value, list):
                setattr(node, field, [self.visit(x) if isinstance(x, ast.AST)
                    else self.symbol(x) if isinstance(x, str) else x for x in value])
            elif isinstance(value, str):
                if isinstance(node, ast.alias) and field == 'name' and value in SAFE_IMPORTS:
                    self.imports.add(value)
                elif isinstance(node, ast.ImportFrom) and field == 'module' and value in SAFE_IMPORTS:
                    self.imports.add(value)
                else:
                    setattr(node, field, self.symbol(value))
        return node


def python_structure(raw):
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
        tree = ast.parse(raw.decode(encoding), filename='<installed-code>', type_comments=False)
        if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
            raise ProbeError('ast_node_bound')
        scrubber = StructureFilter()
        filtered = scrubber.visit(tree)
        calls = []
        for node in ast.walk(filtered):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr in SAFE_SYMBOLS:
                    calls.append({'line': node.lineno, 'operation': func.attr})
                elif isinstance(func, ast.Name) and func.id in SAFE_SYMBOLS:
                    calls.append({'line': node.lineno, 'operation': func.id})
        # dump retains original source line numbers, but no source text/literals.
        structure = ast.dump(filtered, annotate_fields=True, include_attributes=True)
        return {'status': 'filtered_structure', 'known_imports': sorted(scrubber.imports),
                'known_calls': calls, 'structure': structure,
                'notice': 'Pseudonymized AST, not executable or byte-exact source; aliases may obscure API attribution.'}
    except ProbeError as error:
        return {'status': str(error)}
    except (SyntaxError, UnicodeError, LookupError, ValueError, RecursionError):
        return {'status': 'parse_unavailable_no_source_exported'}


def manifest_structure(raw):
    try:
        # Reject DTDs before XML parsing, including UTF-16/32 encoded declarations.
        decl = raw.replace(b'\x00', b'').upper()
        if b'<!DOCTYPE' in decl or b'<!ENTITY' in decl:
            raise ProbeError('xml_declarations_refused')
        tree = ElementTree.fromstring(raw)
        if tree.tag != 'addon' or tree.get('id') != ADDON_ID:
            raise ProbeError('manifest_identity_mismatch')
        version = tree.get('version', '')
        # Record no vendor/free-form metadata. A nonnumeric version is withheld.
        numeric_version = version if version and len(version) <= 32 and all(c in '0123456789.' for c in version) else 'withheld'
        extensions = []
        for node in tree.findall('extension')[:32]:
            point = node.get('point', '')
            library = node.get('library', '')
            extensions.append({'point': point if point in SAFE_POINTS else 'other_extension',
                'library': library if library in ('main.py', 'service.py') else 'other_library',
                'start': node.get('start') if node.get('start') in ('startup', 'login') else 'unspecified'})
        requirements = []
        for node in tree.findall('./requires/import')[:128]:
            dependency = node.get('addon', '')
            requirements.append({'addon': dependency if dependency in SAFE_DEPENDENCIES else 'other_dependency',
                                 'optional': node.get('optional') == 'true'})
        return {'status': 'filtered_manifest', 'addon_id': ADDON_ID, 'version': numeric_version,
                'extensions': extensions, 'requirements': requirements,
                'service_declaration_is_not_proof_of_enabled_or_running_state': True}
    except ProbeError as error:
        return {'status': str(error)}
    except (ElementTree.ParseError, ValueError, RecursionError):
        return {'status': 'parse_unavailable_no_manifest_exported'}


def stack_snapshot(root, frames=None):
    """Read code locations only. Never inspect locals/globals, thread names or values.

    This is a single best-effort snapshot. Other subinterpreters may not be visible;
    an empty result is NOT evidence that a service is stopped or safely retired.
    """
    allowed = {os.path.join(root, name): name for name in ('main.py', 'service.py')}
    result = []
    try:
        current = sys._current_frames() if frames is None else frames
        for frame in list(current.values())[:MAX_FRAMES]:
            depth = 0
            matches = []
            while frame is not None and depth < MAX_DEPTH:
                name = allowed.get(frame.f_code.co_filename)
                if name is not None:
                    matches.append({'source': name, 'line': int(frame.f_lineno)})
                frame = frame.f_back
                depth += 1
            if matches:
                result.append({'sample_thread': len(result) + 1, 'frames': matches})
        return {'status': 'snapshot_only', 'matches': result,
                'other_interpreter_visibility': 'not_guaranteed',
                'native_backend': 'unverified_not_observable_from_python_frames',
                'empty_snapshot_proves_retirement': False}
    except Exception:
        return {'status': 'snapshot_unavailable', 'native_backend': 'unverified'}
    finally:
        # No frame references survive this function.
        frame = None
        current = None


def collect(root):
    root = _safe_local_root(root)
    rows = []
    for name in SOURCE_NAMES:
        item = {'name': name}
        try:
            raw = read_source(root, name)
            item.update({'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                         'analysis': manifest_structure(raw) if name == 'addon.xml' else python_structure(raw)})
            del raw
        except ProbeError as error:
            item['error'] = str(error)
        except OSError:
            item['error'] = 'local_source_unavailable'
        rows.append(item)
    report = {'schema': 1, 'collector': 'Infinity one-shot shutdown probe 0.1.0',
        'captured_epoch_ms': int(time.time() * 1000),
        'source_files': rows, 'python_frames': stack_snapshot(root),
        'scope': {'read_only_target': ADDON_ID, 'source_bytes_exported': False,
            'source_hashes_are_from_installed_bytes': True,
            'multi_file_snapshot_atomic': False,
            'private_urls_credentials_userdata_exported': False,
            'service_imported_started_disabled_or_modified': False,
            'resident_service_or_shutdown_hook_installed': False,
            'cancellation_or_retirement_verified': False,
            'shutdown_repair_verified': False}}
    encoded = json.dumps(report, sort_keys=True, ensure_ascii=True).encode('utf-8')
    if len(encoded) > MAX_OUTPUT_BYTES:
        for item in report['source_files']:
            analysis = item.get('analysis', {})
            if 'structure' in analysis:
                del analysis['structure']
                analysis['structure_omitted'] = 'total_output_bound'
    return report


def export_zip(report, destination):
    """Create a NEW local ZIP exclusively. Never overwrite any file or follow links."""
    destination = _safe_local_root(destination)
    encoded = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=True).encode('utf-8')
    if len(encoded) > MAX_OUTPUT_BYTES:
        raise ProbeError('output_size_bound')
    name = 'Infinity-Playlist-Probe-%s-%s.zip' % (time.strftime('%Y%m%d-%H%M%S'), os.urandom(4).hex())
    directory = _open_local_directory(destination)
    fd = None
    created = False
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        created = True
        with os.fdopen(fd, 'wb') as output:
            fd = None
            with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('playlist-probe.json', encoded)
                archive.writestr('SCOPE.txt', 'One-shot diagnostic evidence, not a shutdown repair.\n'
                    'Original source is hashed but NOT exported. All strings/comments and non-allowlisted identifiers are withheld.\n'
                    'No settings, playlist data, URLs, credentials, frame locals or raw logs are included.\n'
                    'Native backend, cancellation/retirement and replacement-engine safety remain unverified.\n')
            output.flush()
            os.fsync(output.fileno())
        os.fsync(directory)
        return os.path.join(destination, name)
    except Exception:
        if created:
            try:
                os.unlink(name, dir_fd=directory)
            except OSError:
                pass
        raise
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)
