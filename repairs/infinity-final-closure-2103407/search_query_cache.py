def _query_cache_entries(raw, now):
    """A few recent responses, within the original per-provider byte/age caps."""
    import math
    if not isinstance(raw, str) or not raw or len(raw) >= 300000 or not raw.isascii():
        return []
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return []
    if not isinstance(value, dict):
        return []
    if value.get('schema') == 2:
        rows = value.get('entries')
        if not isinstance(rows, list) or len(rows) > 4:
            return []
    elif 'schema' not in value:
        rows = [value]  # Read the already valid previous one-query format.
    else:
        return []
    result = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            return []
        signature, stamp, answer = row.get('signature'), row.get('at'), row.get('answer')
        if (not isinstance(signature, str) or len(signature) != 64 or
                any(ch not in '0123456789abcdef' for ch in signature) or signature in seen or
                type(stamp) not in (int, float) or not math.isfinite(stamp) or
                not isinstance(answer, dict) or 'error' in answer):
            return []
        seen.add(signature)
        if 0 <= now - stamp < 300:
            result.append(dict(signature=signature, at=stamp, answer=answer))
    return result


def _remember_query_answer(home, key, entries, signature, answer, now):
    """No persistent cache, extra memory budget, or renewed TTL on cache hits."""
    fresh = dict(signature=signature, at=now, answer=answer)
    rows = [fresh] + [row for row in entries if row['signature'] != signature]
    rows = rows[:4]
    while rows:
        raw = json.dumps(dict(schema=2, entries=rows), separators=(',', ':'))
        if len(raw) < 300000:
            home.setProperty(key, raw)
            return True
        rows.pop()
    # An oversized new response must not destroy other usable cached queries.
    return False


