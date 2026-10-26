"""Register exact signed407 CC through native package/protocol authentication.

Nothing in PREPARE, FINALIZE, stores, writer fencing or durable receipts changes.
"""
import ast
import hashlib

BASELINE_SHA = '58f3b801e69176a3e91ccca5c1fcb6ebce81bbf8f7e768e07148f531b66190d6'
OLD_CONSTANT = 'ADDON_VERSION = "0.3.5.38"\n'
REGISTER = '''    def register(self):
        if self.store is not None:
            return True
        from module_contract import ContractRejected, installed_identity
        try:
            identity = installed_identity(Path(__file__).parent, self.api["version"]())
        except ContractRejected as error:
            raise PersistenceError(str(error)) from error
        if identity.protocol_api != API:
            raise PersistenceError("unsupported native Command Center checkpoint protocol")
        store = store_for(self.profile)
        if store is None:
            return False
        self.store = store
        durable_json(self.control / "active.json", dict(self._identity(), status="ACTIVE",
            addon_version=identity.package_version, participant_api=identity.protocol_api,
            module_manifest_sha256=identity.manifest_sha256,
            required_files=sorted(FILES)))
        return True
'''


def patch(raw):
    if hashlib.sha256(raw).hexdigest() != BASELINE_SHA:
        raise ValueError('Exact signed407 checkpoint source required')
    text = raw.decode()
    if text.count(OLD_CONSTANT) != 1:
        raise ValueError('Unexpected package pin')
    tree = ast.parse(text)
    resident = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ResidentCheckpoint')
    node = next(n for n in resident.body if isinstance(n, ast.FunctionDef) and n.name == 'register')
    lines = text.splitlines(keepends=True)
    old = ''.join(lines[node.lineno-1:node.end_lineno])
    result = (''.join(lines[:node.lineno-1]) + REGISTER + ''.join(lines[node.end_lineno:])).replace(OLD_CONSTANT, '', 1)
    if result.replace(REGISTER, old, 1).replace('API = 1\n', 'API = 1\n'+OLD_CONSTANT, 1) != text:
        raise ValueError('Unrelated checkpoint source changed')
    compile(result, 'checkpoint_runtime.py', 'exec')
    return result.encode()
