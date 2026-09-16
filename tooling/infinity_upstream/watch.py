#!/usr/bin/env python3
"""Official stable Kodi release watcher. Detection never updates the working app."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
API = 'https://api.github.com'
UPSTREAM = 'xbmc/xbmc'
REPOSITORY = 'mahfouzhassine8-ops/project-infinity'
STABLE = re.compile(r'^v?([1-9][0-9]*)\.([0-9]+)(?:\.([0-9]+))?-([A-Za-z][A-Za-z0-9]*)$')
TAG = re.compile(r'^v?([1-9][0-9]*)\.([0-9]+)(?:\.([0-9]+))?((?:a|b|rc)[0-9]+)?-([A-Za-z][A-Za-z0-9]*)$')
SHA = re.compile(r'^[0-9a-f]{40}$')


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def api(path, payload=None):
    require(path.startswith('/repos/'+UPSTREAM+'/') or path.startswith('/repos/'+REPOSITORY+'/'),
            'API path outside approved repositories')
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Infinity-Upstream-Watcher/1',
               'X-GitHub-Api-Version': '2022-11-28'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer '+token
    data = None if payload is None else json.dumps(payload).encode()
    for attempt in range(3):
        try:
            with urlopen(Request(API+path, data=data, headers=headers), timeout=45) as response:
                # Reject redirection to an unexpected API origin/repository.
                require(response.url.startswith(API+'/repos/'), 'Unexpected API redirect')
                return json.load(response)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError('GitHub API unavailable (HTTP %d). No update decision made.' % error.code) from error
        except URLError as error:
            if attempt == 2:
                raise RuntimeError('GitHub API unreachable; not equivalent to no updates.') from error
        time.sleep(2 ** attempt)
    raise RuntimeError('GitHub API retry exhausted')


def pages(path, maximum=30):
    result = []
    for page in range(1, maximum+1):
        separator = '&' if '?' in path else '?'
        part = api(path+separator+'per_page=100&page='+str(page))
        require(isinstance(part, list), 'Unexpected paginated API response')
        result.extend(part)
        if len(part) < 100:
            return result
    raise RuntimeError('Pagination safety limit reached; refusing an incomplete no-update result')


def version(tag):
    match = STABLE.fullmatch(tag)
    return tuple(int(x or 0) for x in match.groups()[:3]) if match else None


def stable_releases(rows, base_version):
    selected = {}
    for row in rows:
        tag = row.get('tag_name', '')
        parsed = version(tag)
        if (row.get('draft') is not False or row.get('prerelease') is not False or
                not row.get('published_at') or parsed is None or parsed <= tuple(base_version)):
            continue
        require(type(row.get('id')) is int, 'Release missing numeric identity')
        # Malformed flags / beta tags are never promoted even when GitHub marks them stable.
        selected[tag] = row
    return sorted(selected.values(), key=lambda r: version(r['tag_name']))


def tag_commit(tag):
    require(TAG.fullmatch(tag) is not None, 'Invalid or unsupported Kodi release tag')
    obj = api('/repos/'+UPSTREAM+'/git/ref/tags/'+quote(tag, safe=''))['object']
    for _ in range(6):
        require(SHA.fullmatch(obj.get('sha', '')) is not None, 'Invalid upstream SHA')
        if obj.get('type') == 'commit':
            return obj['sha']
        require(obj.get('type') == 'tag', 'Tag does not resolve to a commit')
        obj = api('/repos/'+UPSTREAM+'/git/tags/'+obj['sha'])['object']
    raise RuntimeError('Nested annotated tag limit exceeded')


def resolve_target(tag, allow_prerelease=False):
    require(TAG.fullmatch(tag) is not None, 'Invalid release tag (branches/nightlies are not allowed)')
    row = api('/repos/'+UPSTREAM+'/releases/tags/'+quote(tag, safe=''))
    require(row.get('tag_name') == tag and row.get('draft') is False and row.get('published_at'),
            'Not a published official Kodi release')
    is_prerelease = row.get('prerelease') is True or version(tag) is None
    require(type(row.get('prerelease')) is bool, 'Missing release classification')
    require(not is_prerelease or allow_prerelease, 'Prerelease requires explicit analysis-only opt-in')
    return {'tag': tag, 'commit': tag_commit(tag), 'release_id': row['id'],
            'published_at': row['published_at'], 'prerelease': is_prerelease,
            'url': 'https://github.com/'+UPSTREAM+'/releases/tag/'+quote(tag, safe='')}


def marker(tag):
    return '<!-- infinity-kodi-release:'+tag+' -->'


def existing_issue(rows, target):
    marked = [r for r in rows if not r.get('pull_request') and marker(target['tag']) in (r.get('body') or '')]
    for row in marked:
        # Same release tag at different SHA: never silently accept a moved tag.
        old = re.search(r'<!-- upstream-commit:([0-9a-f]{40}) -->', row.get('body') or '')
        require(old is not None and old.group(1) == target['commit'],
                'An already-notified upstream tag changed or its receipt is missing: '+target['tag'])
    return marked[0] if marked else None


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')


def discover(baseline, out):
    require(baseline['repository'] == REPOSITORY and baseline['upstream']['repository'] == UPSTREAM,
            'Unexpected repository lock')
    require(tag_commit(baseline['upstream']['tag']) == baseline['upstream']['commit'],
            'PINNED KODI BASE TAG MOVED. Stop and investigate.')
    releases = pages('/repos/'+UPSTREAM+'/releases')
    issues = pages('/repos/'+REPOSITORY+'/issues?state=all')
    updates, already = [], []
    for row in stable_releases(releases, baseline['upstream']['version']):
        target = resolve_target(row['tag_name'])
        old = existing_issue(issues, target)
        if old:
            already.append({'tag': target['tag'], 'issue': old['number']})
        else:
            updates.append(target)
    require(len(updates) <= 8, 'More than 8 unreviewed releases: run manual triage instead of unlimited jobs')
    stable = [r for r in releases if version(r.get('tag_name','')) and r.get('prerelease') is False
              and r.get('draft') is False and r.get('published_at')]
    latest = max(stable, key=lambda r: version(r['tag_name']))['tag_name'] if stable else None
    require(latest is not None, 'No recognizable official stable release; check failed, not no updates')
    receipt = {'schema':1, 'checked_at':datetime.now(timezone.utc).isoformat(),
               'baseline_id':baseline['id'], 'pinned_tag':baseline['upstream']['tag'],
               'latest_stable':latest, 'new_stable_updates':updates, 'already_notified':already,
               'ignored_prerelease_count':sum(r.get('prerelease') is True for r in releases),
               'automatic_install':False, 'automatic_build':False}
    save(out/'watch.json', receipt)
    for target in updates:
        save(out/(target['tag']+'.target.json'), target)
    (out/'SUMMARY.md').write_text('# Kodi release watch\n\nChecked: '+receipt['checked_at']+
        '\n\nPinned engine: **'+baseline['upstream']['tag']+'**\n\nLatest official stable: **'+latest+
        '**\n\nNew stable releases awaiting analysis: **'+str(len(updates))+
        '**\n\nAlpha/beta/RC releases ignored. No APK built, changed or installed.\n')
    return receipt


def notify(baseline, out):
    # Write permission is needed ONLY for this explicit step, not source reconstruction.
    require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY and os.environ.get('GITHUB_REF') == 'refs/heads/main',
            'Notifications may only be sent from this repository default branch')
    watch = json.loads((out/'watch.json').read_text())
    require(watch['baseline_id'] == baseline['id'], 'Stale watch receipt')
    issues = pages('/repos/'+REPOSITORY+'/issues?state=all')
    sent = []
    for target in watch['new_stable_updates']:
        fresh = resolve_target(target['tag'])
        require(fresh['commit'] == target['commit'], 'Upstream moved before notification')
        if existing_issue(issues, target):
            continue
        folder = out/target['tag']
        report_path = folder/'impact.json'
        if report_path.exists():
            report = json.loads(report_path.read_text())
            require(report['target']['commit'] == target['commit'], 'Wrong impact report target')
            summary = ('Upstream changed files: %s. Direct Infinity overlaps: %s.\n\nPatch replay: **%s**.' %
                       (report['upstream_changed_count'], len(report['direct_overlap']), report['replay']['result']))
        else:
            summary = '**Analysis did not complete.** See the failing job; do not treat this release as compatible.'
        run_id = os.environ.get('GITHUB_RUN_ID','')
        require(run_id.isdigit(), 'Missing workflow run identity')
        body = (marker(target['tag'])+'\n<!-- upstream-commit:'+target['commit']+' -->\n\n'
                '@mahfouzhassine8-ops A new **stable Kodi '+target['tag']+'** is available for review.\n\n'
                'Current Infinity engine: **'+baseline['upstream']['tag']+'**.\n\n'+summary+
                '\n\n[Official release]('+target['url']+') | [Analysis and artifacts](https://github.com/'+
                REPOSITORY+'/actions/runs/'+run_id+')\n\n'
                '**Working Infinity is unchanged. No APK was built or installed.**\n\n'
                'Next: review overlap, toolchain/API/skin/binary-add-on compatibility and database migration. '
                'A maintainer must approve a release-specific candidate builder before any cook. '
                'A textual patch pass alone never authorizes installation or promotion.\n\n'
                'Protected stack: skin 1.0.5.141 + Health Center 2.5.6 + exact shipped RC3 (2103138).')
        created = api('/repos/'+REPOSITORY+'/issues', {'title':'Kodi '+target['tag']+' available — Infinity review',
                      'body':body, 'assignees':['mahfouzhassine8-ops']})
        issues.append(created); sent.append(created['html_url'])
    save(out/'notification-receipt.json', {'created':sent})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['discover','resolve','notify'])
    p.add_argument('--baseline', type=Path, default=HERE/'baseline.json')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--tag')
    p.add_argument('--allow-prerelease', action='store_true')
    a = p.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    baseline = json.loads(a.baseline.read_text())
    if a.mode == 'discover':
        receipt = discover(baseline, a.out)
        path = os.environ.get('GITHUB_OUTPUT')
        if path:
            with open(path,'a') as f: f.write('has_updates='+str(bool(receipt['new_stable_updates'])).lower()+'\n')
    elif a.mode == 'resolve':
        require(bool(a.tag), '--tag is required')
        save(a.out/'target.json', resolve_target(a.tag, a.allow_prerelease))
    else:
        notify(baseline, a.out)


if __name__ == '__main__':
    main()
