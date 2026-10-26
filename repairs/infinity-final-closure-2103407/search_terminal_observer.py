"""Classify real provider headings, without manufacturing content successes."""
import re

NAMES={'plugin.video.pov':'POV','plugin.video.umbrella':'Umbrella','plugin.video.seren':'Seren'}


def classify(rows,required):
    if not rows or len(rows)>200 or not required or not set(required)<=set(NAMES):
        raise ValueError('Bounded nonempty actual provider listing required')
    observed={}
    for row in rows:
        provider=row.get('provider','')
        if not provider:continue  # Native ListItemAbsolute boundary sentinel.
        if provider not in required:raise ValueError('Unexpected actual provider attribution')
        label=row.get('label','');prefix=NAMES[provider]+' — '
        if not isinstance(label,str):raise ValueError('Invalid actual native label')
        if not label.startswith(prefix):continue
        if provider in observed:raise ValueError('Duplicate actual provider heading')
        status=label[len(prefix):]
        count=re.fullmatch(r'(0|[1-9][0-9]*) results',status)
        if count and int(count[1])<=40:
            observed[provider]=dict(status='completed',reported_result_count=int(count[1]),
                content_success=int(count[1])>0,actual_label=label)
        elif status in ('timeout','unavailable'):
            observed[provider]=dict(status=status,content_success=False,actual_label=label)
        else:raise ValueError('Unaccepted actual provider terminal: '+status)
    if set(observed)!=set(required):return None
    return dict(providers=observed,content_success=all(row['content_success'] for row in observed.values()),
        graceful_provider_failures=[dict(provider=provider,**row) for provider,row in observed.items() if not row['content_success']])
