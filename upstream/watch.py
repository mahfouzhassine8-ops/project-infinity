#!/usr/bin/env python3
"""Stable Kodi source-tag watcher. Notification is separate from code/build authority.

Uses only the official upstream tags. Draft/prerelease releases are never eligible.
A missing GitHub Release is reported as 'source tag; publication unconfirmed', NOT
as a downloadable Android release. Failures are errors, never 'up to date'.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
TAG = re.compile(r'^(\d+)\.(\d+)(?:\.(\d+))?-([A-Za-z][A-Za-z0-9]*)$')
SHA = re.compile(r'^[0-9a-f]{40}$')
REPO = 'mahfouzhassine8-ops/project-infinity'
UPSTREAM = 'xbmc/xbmc'


def require(ok, why):
    if not ok:
        raise RuntimeError(why)


def stable_version(tag):
    match = TAG.fullmatch(tag)
    if not match:
        return None
    # Never infer stable from a suffix that says alpha/beta/rc/nightly.
    if re.search(r'alpha|beta|nightly|preview|snapshot|^rc\d*$', match[4], re.I):
        return None
    return int(match[1]), int(match[2]), int(match[3] or 0)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError('GitHub API redirect refused; credentials must not be forwarded')


class API:
    def __init__(self, token=''):
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, path, method='GET', body=None, allow_404=False):
        require(path.startswith('/repos/'), 'Only repository endpoints are allowed')
        if method != 'GET':
            require(path.startswith('/repos/' + REPO + '/issues'), 'Writes limited to Infinity issues')
        url = 'https://api.github.com' + path
        headers = {'Accept': 'application/vnd.github+json',
                   'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'Infinity-Upstream-Watcher/1'}
        if body is not None:
            headers['Content-Type'] = 'application/json'
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404 and allow_404:
                return None
            raise RuntimeError('GitHub API %s failed: HTTP %s' % (method, error.code)) from None

    def pages(self, path):
        # Exhaustive pagination; reaching the limit is an error, never a partial result.
        rows = []
        sep = '&' if '?' in path else '?'
        for page in range(1, 101):
            batch = self.request(path + sep + 'per_page=100&page=' + str(page))
            require(isinstance(batch, list), 'Unexpected paginated API response')
            rows.extend(batch)
            if len(batch) < 100:
                return rows
        raise RuntimeError('Pagination exceeded 10,000 records; refuse an incomplete check')


def read_official_tags():
    proc = subprocess.run(['git', 'ls-remote', '--tags', 'https://github.com/' + UPSTREAM + '.git'],
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=120)
    tags, peeled = {}, {}
    for line in proc.stdout.splitlines():
        sha, ref = line.split('\t', 1)
        require(SHA.fullmatch(sha), 'Malformed upstream tag hash')
        if not ref.startswith('refs/tags/'):
            continue
        name = ref[len('refs/tags/'):]
        if name.endswith('^{}'):
            peeled[name[:-3]] = sha
        else:
            tags[name] = sha
    tags.update(peeled)  # Resolve annotated tags to their commit, not the tag object.
    require(tags, 'Upstream returned no tags')
    return tags


def detect(tags, baseline, release_lookup):
    pinned = baseline['upstream']
    require(tags.get(pinned['tag']) == pinned['commit'],
            'Pinned Kodi tag moved or disappeared; manual investigation required')
    current = stable_version(pinned['tag'])
    require(current is not None, 'Baseline must be a stable source tag')
    candidates = []
    skipped = []
    for tag, sha in tags.items():
        version = stable_version(tag)
        if version is not None and version > current:
            require(SHA.fullmatch(sha), 'Invalid target hash')
            release = release_lookup(tag)
            if release is not None and (release.get('draft') or release.get('prerelease')):
                skipped.append(tag)
                continue
            candidates.append({'tag': tag, 'commit': sha,
                               'publication': 'published_release' if release else 'source_tag_only',
                               'release_url': release.get('html_url') if release else None})
    candidates.sort(key=lambda row: (stable_version(row['tag']), row['tag']))
    return {'schema': 1, 'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'status': 'updates_detected' if candidates else 'no_new_stable_source_tag',
            'baseline': pinned, 'candidates': candidates, 'excluded_prerelease_tags': skipped,
            'latest_candidate': candidates[-1] if candidates else None,
            'build_started': False, 'installed_app_modified': False}


def notification_body(row, baseline, run_url):
    return (f"<!-- infinity-upstream-tag:{row['tag']}:{row['commit']} -->\n"
            f"@{baseline['notification_recipient']} — new official Kodi stable-shaped source tag detected.\n\n"
            f"Current engine: **{baseline['upstream']['tag']}**. Target: **{row['tag']}**.\n"
            f"Exact target commit: `{row['commit']}`.\n\n"
            f"Publication evidence: **{row['publication']}**. A source tag is not proof that Android binaries are released.\n\n"
            "**Your installed Infinity has NOT changed. No APK build, release, merge or install was authorized.**\n\n"
            "The source-only analysis checks upstream changes against the pinned Infinity recipe. "
            "A clean patch replay is NOT runtime compatibility or device acceptance.\n\n"
            f"Check/artifact run: {run_url}\n"
            "Manual analysis: Actions → Infinity | Kodi Port Analysis → Run workflow.\n")


def notify(report, baseline, api, run_url):
    require(baseline['repository'] == REPO, 'Unexpected notification repository')
    require(re.fullmatch(r'[A-Za-z0-9-]+', baseline['notification_recipient']), 'Unsafe recipient')
    issues = api.pages('/repos/' + REPO + '/issues?state=all&creator=github-actions%5Bbot%5D')
    fresh = []
    for row in report['candidates']:
        require(stable_version(row['tag']) is not None and SHA.fullmatch(row['commit']), 'Invalid notification target')
        exact = '<!-- infinity-upstream-tag:%s:%s -->' % (row['tag'], row['commit'])
        prefix = '<!-- infinity-upstream-tag:%s:' % row['tag']
        same_tag = [i for i in issues if not i.get('pull_request') and prefix in (i.get('body') or '')]
        # Closed/dismissed issues count as acknowledged; never spam/reopen them.
        if any(exact in (i.get('body') or '') for i in same_tag):
            continue
        moved = bool(same_tag)
        body = notification_body(row, baseline, run_url)
        if moved:
            body += '\n**WARNING: this tag was previously observed at a different commit. Do not migrate before review.**\n'
        issue = api.request('/repos/' + REPO + '/issues', 'POST',
                            {'title': ('[Kodi tag changed] ' if moved else '[Kodi update] ') + row['tag'],
                             'body': body, 'assignees': [baseline['notification_recipient']]})
        issues.append(issue)
        if not moved:
            fresh.append(row)
    return fresh


def write_outputs(values):
    path = os.environ.get('GITHUB_OUTPUT')
    if path:
        with open(path, 'a', encoding='utf-8') as handle:
            for key, value in values.items():
                require('\n' not in str(value), 'Multiline output refused')
                handle.write('%s=%s\n' % (key, value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('check', 'notify'))
    parser.add_argument('--report', type=Path, default=Path('watch-output/watch.json'))
    args = parser.parse_args()
    baseline = json.loads((ROOT/'baseline.json').read_text())
    api = API(os.environ.get('GH_TOKEN', ''))
    if args.command == 'check':
        tags = read_official_tags()
        report = detect(tags, baseline, lambda tag: api.request(
            '/repos/' + UPSTREAM + '/releases/tags/' + urllib.parse.quote(tag, safe=''), allow_404=True))
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
        row = report['latest_candidate'] or {}
        write_outputs({'has_update': str(bool(row)).lower(), 'tag': row.get('tag', ''),
                       'target_sha': row.get('commit', '')})
        message = ('Kodi watcher: ' + report['status'] + '. No app changes; no build.\n')
        print(message)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            Path(os.environ['GITHUB_STEP_SUMMARY']).write_text(message)
    else:
        # Notification writes occur only in the trusted default-branch watcher.
        require(os.environ.get('GITHUB_REPOSITORY') == REPO, 'Wrong repository')
        require(os.environ.get('GITHUB_REF') == 'refs/heads/main', 'Notify only from main')
        require(os.environ.get('GITHUB_EVENT_NAME') in ('schedule', 'workflow_dispatch'), 'Unexpected event')
        require(api.token, 'Notification token unavailable')
        report = json.loads(args.report.read_text())
        require(report['baseline'] == baseline['upstream'], 'Stale baseline in check artifact')
        fresh = notify(report, baseline, api,
                       'https://github.com/' + REPO + '/actions/runs/' + os.environ['GITHUB_RUN_ID'])
        row = max(fresh, key=lambda r: stable_version(r['tag'])) if fresh else {}
        write_outputs({'new_alert': str(bool(row)).lower(), 'tag': row.get('tag', ''),
                       'target_sha': row.get('commit', '')})
        print('New stable-tag alerts:', len(fresh))


if __name__ == '__main__':
    main()
