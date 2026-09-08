from pathlib import Path

# Infinity 8.0 native movie resume wording pass.
# Kodi already owns resume bookmarks and the actual resume/start-over decision path.
# This patch keeps that native behavior and standardizes the user-facing wording
# so movies clearly offer Continue or Start Over when a resume point exists.

root = Path('/tmp/xbmc')
search_roots = [
    root / 'addons',
    root / 'xbmc',
]

replacements = [
    ('Start from beginning', 'Start Over'),
    ('Start from Beginning', 'Start Over'),
    ('Start from the beginning', 'Start Over'),
    ('Play from beginning', 'Start Over'),
    ('Play from Beginning', 'Start Over'),
    ('Resume from', 'Continue from'),
    ('Resume', 'Continue'),
]

changed = []
for base in search_roots:
    if not base.exists():
        continue
    for p in base.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'.xml', '.po', '.cpp', '.h'}:
            continue
        try:
            s = p.read_text(encoding='utf-8')
        except Exception:
            continue
        old = s
        for a, b in replacements:
            s = s.replace(a, b)
        if s != old:
            p.write_text(s, encoding='utf-8')
            changed.append(str(p.relative_to(root)))

print('Infinity 8.0 native resume wording patch complete')
print('Changed files:', len(changed))
for p in changed[:100]:
    print(p)
