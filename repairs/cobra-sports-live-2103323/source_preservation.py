"""Require unchanged Java tokens outside explicitly reviewed Sports data methods."""
import json
import re
from pathlib import Path

EXISTING = ('cobraProSportsUiGame', 'cobraProSportsProgram', 'scoreboard', 'cobraSportsDay',
    'cobraSportsJsonOnce', 'cobraSportsMeta', 'cobraSportsScoreLine', 'cobraSportsRenderHub',
    'cobraSportsRefresh', 'cobraSportsScheduleNext', 'cobraSportsRefreshMultiOverlays',
    'showCobraSportsDiagnostics', 'cobraRefreshScoreTicker')
ADDED = ('cobraSportsCollectDays', 'cobraSportsShiftDay', 'cobraSportsFetchDays',
    'cobraSportsActiveSoon', 'cobraSportsDayTtl', 'cobraSportsFeedFresh', 'cobraSportsDelayed',
    'cobraSportsScorePair', 'cobraSportsParseFeed', 'cobraSportsActiveLeagues', 'cobraSportsRefreshInterval')
TOKENS = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\w+|[^\s]', re.M)


def tokens(text):
    return [m[0] for m in TOKENS.finditer(text) if not m[0].startswith(('//', '/*'))]


def remove_body(text, name, new=False, is_class=False):
    prefix = r'private static final class\s+' if is_class else r'(?:private|public)\s+(?:static\s+)?(?:[\w.<>]+)\s+'
    pattern = re.compile(prefix + re.escape(name) + (r'\s*\{' if is_class else r'\([^;{]*\)(?:throws [^{;]+)?\s*\{'))
    matches = list(pattern.finditer(text))
    assert len(matches) == 1, (name, len(matches))
    m = matches[0]; start = text.index('{', m.start()); depth = 0; end = None
    for token in TOKENS.finditer(text, start):
        if token[0] == '{': depth += 1
        elif token[0] == '}':
            depth -= 1
            if depth == 0:
                end = token.end(); break
    assert end is not None, name
    return text[:m.start()] + ('' if new else 'SPORTS_SCOPE_' + name) + text[end:]


def verify(before, after, out):
    for name in EXISTING:
        before = remove_body(before, name)
        after = remove_body(after, name)
    for name in ADDED:
        after = remove_body(after, name, new=True)
    after = remove_body(after, 'CobraSportsBoardResult', new=True, is_class=True)
    after = after.replace('mCobraSportsLastRefresh=0L,mCobraSportsLastFullRefresh=0L', 'mCobraSportsLastRefresh=0L')
    after = after.replace('long feedUpdatedAtMs=System.currentTimeMillis();boolean feedAvailable=true;', '')
    after = after.replace('CobraSportsBoardResult scoreboard(', 'ArrayList<CobraSportsGame> scoreboard(')
    assert tokens(before) == tokens(after), 'Changes outside the explicitly reviewed Sports data scope'
    Path(out).write_text(json.dumps({'protected_java_tokens_identical': True,
        'changed_methods': list(EXISTING), 'added_methods': list(ADDED),
        'added_state': ['per-event feed receipt and availability', 'independent full-sweep timestamp', 'partial date-result container'],
        'CobraProUi_source_unchanged': True}, indent=2) + '\n')
