        # Stepping/finalizing a cursor, rolling back, context exit and connection
        # cleanup can call the native VFS after execute() has returned. Keep the
        # invocation owner through the actual call, including GIL-released I/O.
        # This coordination lease has no persistent target and grants no write
        # permission: every actual VFS path retains its native admission/drain
        # checks. Return values and exceptions come from the original method.
        def owned_sqlite_call(original, operation):
            def owned(handle, *args, **kwargs):
                with observer.operation(operation, (NONPERSISTENT_TARGET,)):
                    return original(handle, *args, **kwargs)
            return owned

        for klass, names in (
                (Cursor, ('fetchone', 'fetchmany', 'fetchall', '__next__', 'close')),
                (Connection, ('rollback', '__exit__', 'close', 'backup', 'blobopen',
                              'serialize', 'deserialize'))):
            for name in names:
                original = getattr(klass, name, None)
                if original is not None:
                    setattr(klass, name, owned_sqlite_call(original, 'sqlite.'+name))
