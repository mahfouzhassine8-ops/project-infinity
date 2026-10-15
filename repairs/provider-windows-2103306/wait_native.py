#!/usr/bin/env python3
"""Wait inside CI for an explicitly pinned native validation run, fail closed."""
import argparse
import json
import os
import time
from urllib.request import Request, urlopen


def validate_run(run, run_id, commit, repo):
    """Authenticate the run before its conclusion can authorize packaging."""
    if (run.get('id') != run_id or run.get('head_sha') != commit or
        run.get('head_repository', {}).get('full_name') != repo or
        run.get('path') != '.github/workflows/infinity-2103306-provider-native-validation.yml'):
        raise ValueError('Native run provenance differs from explicit pin')
    if run.get('status') == 'completed':
        if run.get('conclusion') != 'success':
            raise ValueError('Native validation did not succeed; no APK will be packaged')
        return True
    if run.get('status') not in ('queued', 'in_progress', 'waiting', 'pending', 'requested'):
        raise ValueError('Unexpected native validation status; no APK will be packaged')
    return False


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=int, required=True)
    p.add_argument('--commit', required=True)
    args = p.parse_args()
    repo = os.environ['GITHUB_REPOSITORY']
    token = os.environ['GH_TOKEN']
    url = f'https://api.github.com/repos/{repo}/actions/runs/{args.run}'
    for _ in range(390):
        request = Request(url, headers={'Authorization': 'Bearer ' + token,
            'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
        with urlopen(request, timeout=30) as response:
            run = json.load(response)
        if validate_run(run, args.run, args.commit, repo):
            print('PASS exact native validation completed successfully:', args.run)
            return
        print('Waiting for pinned native validation:', args.run, run['status'], flush=True)
        time.sleep(60)
    raise TimeoutError('Native validation not completed within bounded CI wait')


if __name__ == '__main__':
    main()
