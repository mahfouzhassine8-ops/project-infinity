# 2103349 CPython bytecode-cache classification

Parent: green 2103348 source commit `d866de112e9a4e40447a791c76a5547f78b3fc58`.

## Physical Fold evidence

`Infinity-Diagnostics-20261009-052613.zip` moved the prior AutoWidget/Pillow native-extension blocker. The current first failure is:

`python_writer:file_open_bypassed_checked_buffer_observer`

Writer: `script.artistslideshow:default.py`.

Failure path:

`/data/user/0/com.projectinfinity.kodi/cache/apk/assets/python3.11/lib/python3.11/importlib/__pycache__/__init__.cpython-311.opt-1.pyc.12970367414572004272`

The captured stack is CPython importlib's `_write_atomic -> set_data -> _cache_bytecode -> get_code`. This is a regenerable bytecode-cache temp file, not user state.

## Narrow contract

2103349 does not exempt Artist Slideshow, AutoWidget, add-on writers, arbitrary `.pyc` files, or arbitrary cache files.

A Python write is treated as nonpersistent bytecode cache only when all of these are true:

- the path is absolute and syntactically traversal-free;
- it is below Infinity's private Android cache root for package `com.projectinfinity.kodi`;
- on Android, the existing parent directory resolves canonically back into that same private cache root;
- it is directly inside an exact `__pycache__` directory;
- the file ends in `.pyc` or CPython's atomic temporary form `.pyc.<digits>`.

Exact `__pycache__` directory creation/removal under that private cache tree is likewise nonpersistent. A rename crossing between this cache class and any other path fails closed with `python_bytecode_cache_boundary_rename`.

Userdata, add-on settings, favourites, Resume Hub state, databases, profiles, skin settings, provider state, and files under `.kodi/userdata` remain tracked and fail-closed.

## Preservation

No skin, provider, Command Center, Resume Hub, Cobra, playback UI, account data, signer, Force Close, or shutdown ownership behavior is redesigned by this pass. The 2103348 Pillow native allowlist remains unchanged and pinned.

This is a test candidate. Device acceptance requires the same Fold test: settle Home/widgets, create real playback/resume dirtiness, Normal Close, then export diagnostics whether the checkpoint passes or fails.
