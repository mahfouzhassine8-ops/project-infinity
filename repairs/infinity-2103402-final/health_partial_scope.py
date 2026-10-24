"""Correction 9: preserve partial exports when an optional collector fails.

Archive writes and final validation remain outside collector exception handlers.
The original diagnostic observer, attribution rules and durability stay intact.
"""
from hashlib import sha256

PREIMAGE_SHA256 = '5c7e698e2b1865cee96639f252dfdcab2c7a595a27b9e6e55d942fef8fec618a'
PATH = 'script.kodihealthcenter/khc_diagnostics.py'

CHANGES = [
    ('''        from infinity_runtime_identity import collect as runtime_identity
        bundle.json('runtime-component-identity.json', runtime_identity(), 'actual_resolved_kodi_addons')
        from khc_causal import collect as causal_collect
        causal_roots = [entry[1] for entry in native_dirs]
        causal_roots += [Path(entry[1]).parent for entry in native_dirs]
        bundle.json('causal-tree.json', causal_collect(causal_roots, environment), 'bounded_causal_diagnostic_tree')''',
     '''        try:
            from infinity_runtime_identity import collect as runtime_identity
            identity = runtime_identity()
        except Exception as error:
            identity = {'status': 'unavailable', 'available': False,
                        'error_type': type(error).__name__, 'runtime_resolved': False}
        bundle.json('runtime-component-identity.json', identity, 'actual_resolved_kodi_addons')
        try:
            from khc_causal import collect as causal_collect
            causal_roots = [entry[1] for entry in native_dirs]
            causal_roots += [Path(entry[1]).parent for entry in native_dirs]
            causal = causal_collect(causal_roots, environment)
        except Exception as error:
            causal = {'status': 'unavailable', 'available': False,
                      'error_type': type(error).__name__, 'root_cause_confirmed': False}
        bundle.json('causal-tree.json', causal, 'bounded_causal_diagnostic_tree')'''),
    ('''            if folder.is_symlink() or not folder.is_dir():
                continue
            for p in sorted(folder.iterdir()):''',
     '''            try:
                if folder.is_symlink() or not folder.is_dir():
                    bundle.omitted.append({'file': 'android-optional/' + prefix,
                                           'reason': 'directory_missing_or_unverified'})
                    continue
                candidates = sorted(folder.iterdir())
            except OSError as error:
                bundle.omitted.append({'file': 'android-optional/' + prefix,
                                       'reason': 'directory_unavailable',
                                       'error_type': type(error).__name__})
                continue
            for p in candidates:'''),
    ('''        correlation = correlate_native_incident(native_dirs, active_baseline, selected, environment)
        session_exit=correlation.get('session_exit',{})''',
     '''        try:
            correlation = correlate_native_incident(native_dirs, active_baseline, selected, environment)
            if not isinstance(correlation, dict) or not isinstance(correlation.get('session_exit', {}), dict):
                raise ValueError('Invalid native correlation result')
        except Exception as error:
            correlation = {'status': 'unavailable', 'available': False,
                           'error_type': type(error).__name__,
                           'temporal_scope': 'unverified',
                           'attributable_to_selected_session': False,
                           'session_exit': {'status': 'UNVERIFIED',
                               'summary': 'Session exit evidence unavailable; no crash or clean-exit conclusion.'}}
        session_exit=correlation.get('session_exit',{})'''),
    ('''                text, info = read_tail(path, MAX_FILE)
                ok = self.add(name, text, role, scrub)''',
     '''                text, info = read_tail(path, MAX_FILE)
                if not text:
                    self.omitted.append({'file': name, 'reason': 'empty_source', 'available': False})
                    return False
                ok = self.add(name, text, role, scrub)'''),
    ('''                data = handle.read(MAX_FILE + 1)
            return self.add(name, data, role, scrub)''',
     '''                data = handle.read(MAX_FILE + 1)
            if not data:
                self.omitted.append({'file': name, 'reason': 'empty_source', 'available': False})
                return False
            return self.add(name, data, role, scrub)'''),
]


def transform(original):
    if sha256(original).hexdigest() != PREIMAGE_SHA256:
        raise ValueError('Exact signed Health Center 2.5.26 source required')
    output = original
    for before, after in CHANGES:
        before, after = before.encode(), after.encode()
        if output.count(before) != 1:
            raise ValueError('Missing or ambiguous Health export boundary')
        output = output.replace(before, after, 1)
    restored = output
    for before, after in reversed(CHANGES):
        restored = restored.replace(after.encode(), before.encode(), 1)
    if restored != original:
        raise ValueError('Unowned Health source change')
    compile(output, PATH, 'exec')
    return output
