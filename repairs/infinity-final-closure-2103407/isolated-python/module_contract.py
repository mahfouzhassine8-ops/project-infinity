"""Infinity's original-signer native handshake and exact-source module loader.

No worker, polling, provider scan, persistence writer or Python success receipt.
The immutable native key authenticates a bounded exact-file manifest. Python
imports from the four owned packages compile those verified source bytes and
never execute a .pyc or an unlisted file from those directories.
"""
from __future__ import annotations

import ctypes
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import re
import sys
from types import MappingProxyType

PROTOCOL_API = 1
CC = 'script.infinity.commandcenter'
ADDONS = frozenset((CC, 'script.infinity.watchedbridge', 'script.infinity.uirepair', 'script.infinity.rails'))
_native_library = None
_native_function = None


class ContractRejected(RuntimeError):
    pass


def _native():
    global _native_library, _native_function
    if _native_function is None:
        try:
            library = ctypes.CDLL(None)
            function = library.InfinityCommandCenterIdentityV1
            function.argtypes = (ctypes.c_char_p, ctypes.POINTER(ctypes.c_char), ctypes.c_size_t,
                                 ctypes.POINTER(ctypes.c_char), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint))
            function.restype = ctypes.c_int
        except (OSError, AttributeError) as error:
            raise ContractRejected('The matching Infinity module-trust native engine is unavailable.') from error
        _native_library, _native_function = library, function
    return _native_function


class Identity:
    __slots__ = ('package_version', 'protocol_api', 'manifest_sha256')

    def __init__(self, version, protocol, digest):
        self.package_version, self.protocol_api, self.manifest_sha256 = version, protocol, digest


def installed_identity(command_center_root, expected_package_version):
    root = str(Path(command_center_root).absolute())
    encoded = root.encode('utf-8')
    if len(encoded) > 4096 or b'\0' in encoded or not isinstance(expected_package_version, str):
        raise ContractRejected('The installed Command Center identity is invalid.')
    version, digest, protocol = ctypes.create_string_buffer(49), ctypes.create_string_buffer(65), ctypes.c_uint()
    if _native()(encoded, version, len(version), digest, len(digest), ctypes.byref(protocol)) != 1:
        raise ContractRejected('Command Center modules did not pass native signature and source verification.')
    try:
        actual_version, actual_digest = version.value.decode('ascii'), digest.value.decode('ascii')
    except UnicodeError as error:
        raise ContractRejected('The native module identity is malformed.') from error
    if (len(actual_version) > 48 or not re.fullmatch(r'[0-9]+(?:\.[0-9]+){2,3}', actual_version) or
            actual_version != expected_package_version or protocol.value != PROTOCOL_API or
            not re.fullmatch(r'[a-f0-9]{64}', actual_digest)):
        raise ContractRejected('Installed package, signed modules and checkpoint protocol do not agree.')
    return Identity(actual_version, protocol.value, actual_digest)


def _relative(value):
    if not isinstance(value, str) or len(value) > 240 or not re.fullmatch(r'[A-Za-z0-9_./-]+', value):
        raise ContractRejected('Invalid signed module path.')
    parts = value.split('/')
    if len(parts) < 2 or parts[0] not in ADDONS or any(p in ('', '.', '..') for p in parts) or 'cobra' in value.lower():
        raise ContractRejected('Unowned signed module path.')
    return value


def _source_bytes(addons_root, relative, limit=4*1024*1024):
    parts = _relative(relative).split('/')
    try:
        directory = os.open(str(addons_root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as error:
        raise ContractRejected('The signed module root is unavailable.') from error
    try:
        for component in parts[:-1]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        source = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(source, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if before.st_mode & 0o170000 != 0o100000 or before.st_size > limit:
                raise ContractRejected('Signed module exceeds its read limit.')
            raw = stream.read(limit+1)
            after = os.fstat(stream.fileno())
            stamp = lambda s:(s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            if len(raw) > limit or len(raw) != before.st_size or stamp(before) != stamp(after):
                raise ContractRejected('Signed module changed during loading.')
            return raw
    except OSError as error:
        raise ContractRejected('The signed module cannot be read safely.') from error
    finally:
        os.close(directory)


class Contract:
    __slots__ = ('root', 'identity', 'files', 'entries', 'capabilities')

    def __init__(self, root, identity, files, entries, capabilities):
        self.root, self.identity = root, identity
        self.files, self.entries = MappingProxyType(files), MappingProxyType(entries)
        self.capabilities = frozenset(capabilities)

    def current(self):
        raw = _source_bytes(self.root, CC+'/INFINITY-MODULES.v1', 128*1024)
        if hashlib.sha256(raw).hexdigest() != self.identity.manifest_sha256:
            raise ContractRejected('Command Center changed; this older invocation cannot write or import new code.')

    def relative_origin(self, origin):
        if not isinstance(origin, str) or not os.path.isabs(origin):
            return None
        path = os.path.abspath(origin)
        prefix = str(self.root)+os.sep
        if not path.startswith(prefix):
            return None
        relative = path[len(prefix):].replace(os.sep, '/')
        return relative if relative.split('/',1)[0] in ADDONS else None

    def source(self, relative):
        self.current()
        relative = _relative(relative)
        if relative not in self.files or not relative.endswith('.py'):
            raise ContractRejected('An unlisted or compiled first-party module was rejected.')
        raw = _source_bytes(self.root, relative)
        if hashlib.sha256(raw).hexdigest() != self.files[relative]:
            raise ContractRejected('First-party module code differs from its authenticated source.')
        return raw


def load_contract(command_center_root, expected_package_version):
    root = Path(command_center_root).absolute()
    identity = installed_identity(root, expected_package_version)
    addons = root.parent
    raw = _source_bytes(addons, CC+'/INFINITY-MODULES.v1', 128*1024)
    if hashlib.sha256(raw).hexdigest() != identity.manifest_sha256:
        raise ContractRejected('The module manifest changed after native verification.')
    files, entries, capabilities = {}, {}, set()
    try:
        lines = raw.decode('ascii').splitlines()
        if lines[:3] != ['INFINITY-MODULES/1', 'package\t'+identity.package_version, 'protocol\t1']:
            raise ValueError('wrong header')
        for line in lines[3:]:
            fields = line.split('\t')
            if len(fields) == 3 and fields[0] == 'file':
                name = _relative(fields[2])
                if name in files or not re.fullmatch(r'[a-f0-9]{64}', fields[1]):
                    raise ValueError('wrong file record')
                files[name] = fields[1]
            elif len(fields) == 3 and fields[0] == 'entry':
                name = _relative(fields[2])
                if name in entries or name not in files or fields[1] not in ('command_center','command_center_client'):
                    raise ValueError('wrong entry')
                entries[name] = fields[1]
            elif len(fields) == 2 and fields[0] == 'capability':
                capabilities.add(fields[1])
            else:
                raise ValueError('wrong record')
        if len(files) > 256 or len(entries) > 16:
            raise ValueError('over budget')
    except (UnicodeError, ValueError, IndexError) as error:
        raise ContractRejected('Native-authenticated module metadata is malformed.') from error
    return Contract(addons, identity, files, entries, capabilities)


class _SourceLoader(importlib.abc.Loader):
    def __init__(self, contract, origin, verified_bytes):
        self.contract, self.origin, self.raw = contract, origin, verified_bytes

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        self.contract.current()
        if self.raw is None:
            raise ContractRejected('Verified source bytes were already consumed.')
        try:
            module.__file__, module.__cached__ = self.origin, None
            exec(compile(self.raw, self.origin, 'exec', dont_inherit=True), module.__dict__)
        finally:
            self.raw = None


class ImportGuard(importlib.abc.MetaPathFinder):
    def __init__(self, contract):
        self.contract = contract

    def find_spec(self, fullname, path=None, target=None):
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        relative = self.contract.relative_origin(spec.origin) if spec is not None else None
        if relative is None:
            return spec  # Same PathFinder result; unrelated imports are unchanged.
        # Reject unknown/compiled owned modules before the ordinary loader can
        # execute them. Known source uses our loader, bypassing any stale .pyc.
        verified_bytes = self.contract.source(relative)
        spec.loader = _SourceLoader(self.contract, spec.origin, verified_bytes)
        spec.cached = None
        return spec


def install_import_guard(contract):
    for name, module in list(sys.modules.items()):
        relative = contract.relative_origin(getattr(module, '__file__', None))
        if relative is not None:
            contract.source(relative)
            loader = getattr(module, '__loader__', None)
            bootstrap = module is sys.modules.get(__name__)
            entry = name == '__main__' and relative in contract.entries
            verified = isinstance(loader, _SourceLoader) and \
                loader.contract.identity.manifest_sha256 == contract.identity.manifest_sha256
            if not (bootstrap or entry or verified):
                raise ContractRejected('First-party code was loaded before verified source ownership was established.')
    guards = [item for item in sys.meta_path if isinstance(item, ImportGuard)]
    if guards:
        if len(guards) != 1 or guards[0].contract.identity.manifest_sha256 != contract.identity.manifest_sha256:
            raise ContractRejected('A conflicting first-party module generation is already loaded.')
        return guards[0]
    guard = ImportGuard(contract)
    try:
        position = sys.meta_path.index(importlib.machinery.PathFinder)
    except ValueError as error:
        raise ContractRejected('The expected Python source-loading boundary is unavailable.') from error
    sys.meta_path[position] = guard
    return guard


def active_contract(command_center_root, expected_package_version):
    root = Path(command_center_root).absolute()
    for guard in sys.meta_path:
        if isinstance(guard, ImportGuard):
            contract = guard.contract
            if contract.root != root.parent or contract.identity.package_version != expected_package_version:
                raise ContractRejected('A conflicting Command Center package is active.')
            contract.current()
            return contract
    contract = load_contract(root, expected_package_version)
    install_import_guard(contract)
    return contract


def require_current():
    guards = [guard for guard in sys.meta_path if isinstance(guard, ImportGuard)]
    if len(guards) != 1:
        raise ContractRejected('No unique authenticated first-party generation owns this operation.')
    guards[0].contract.current()


def source_module(contract, name, relative):
    """For existing explicit module loads that bypass PathFinder, use the same bytes."""
    origin = str(contract.root / _relative(relative))
    loader = _SourceLoader(contract, origin, contract.source(relative))
    spec = importlib.machinery.ModuleSpec(name, loader, origin=origin)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
