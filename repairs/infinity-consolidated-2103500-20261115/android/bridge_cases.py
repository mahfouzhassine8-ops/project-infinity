"""Disposable Android inputs; executed by the engine's own CPython observer."""
SETUP = """import io, os, sqlite3, types
handle=open(root+'/profile/value','wb')
observer=handle.observer
assert observer.host_probe is False
assert isinstance(observer.fail, types.BuiltinFunctionType)
assert isinstance(observer.protect, types.BuiltinFunctionType)
handle.write(b'preserved')
handle.close()
"""
CASES = {
    'closed_binary': SETUP + """try: handle.flush()
except ValueError: pass
else: raise AssertionError('closed flush exception suppressed')
assert open(root+'/profile/value','rb').read()==b'preserved'
""",
    'closed_text': SETUP + """handle=open(root+'/profile/value','w')
handle.write('preserved')
handle.close()
try: handle.flush()
except ValueError: pass
else: raise AssertionError('closed flush exception suppressed')
""",
    'closed_layered': SETUP + """handle=io.TextIOWrapper(io.BufferedWriter(io.FileIO(root+'/profile/value','w')))
handle.write('preserved')
handle.close()
try: handle.flush()
except ValueError: pass
else: raise AssertionError('layered closed flush exception suppressed')
""",
    'flush_error': SETUP + """raw=handle._infinity_handle
def broken_flush(): raise ValueError('fixture actual flush failure')
raw.flush=broken_flush
try: handle.flush()
except ValueError: pass
else: raise AssertionError('real failure suppressed')
""",
    'dirty_buffer': SETUP + """raw=io.FileIO(root+'/profile/value','wb')
original_write=raw.write
def broken_write(value): raise OSError('fixture actual write failure')
raw.write=broken_write
handle=io.BufferedWriter(raw)
handle.write(b'pending')
""",
    'sqlite_pending': SETUP + """connection=sqlite3.connect(root+'/profile/test.db')
connection.execute('CREATE TABLE progress(position)')
connection.commit()
connection.execute('INSERT INTO progress VALUES(231)')
assert connection.in_transaction
""",
    'durability_denied': SETUP,
    'late_write': SETUP,
}
