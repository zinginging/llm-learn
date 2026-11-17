"""Read-only delivery gate: local changes, required files and live remote branch SHA.

Default checks the repository and this topic's delivery manifest. --verify-remote
needs network. Does not add, commit, fetch, push, reset or delete anything.
Exit 0 = remotely verified; 1 = local/remote mismatch; 2 = not remotely verified.
"""
import argparse
import json
import subprocess
from pathlib import Path

TOPIC = Path(__file__).resolve().parents[1]


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, timeout=25)


def inspect(root, manifest, verify_remote=False, remote='origin', branch=None):
    report = {'durable': False, 'status': 'UNVERIFIED'}
    status = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    if status.returncode:
        return {**report, 'status': 'GIT_CHECK_FAILED'}, 1
    if status.stdout:
        return {**report, 'status': 'LOCAL_CHANGES', 'detail': '存在未提交或未跟踪内容'}, 1
    head = git(root, 'rev-parse', 'HEAD')
    if head.returncode:
        return {**report, 'status': 'NO_COMMIT'}, 1
    sha = head.stdout.decode().strip()
    report['local_commit'] = sha
    required = json.loads(manifest.read_text())['required_files']
    if not required:
        return {**report, 'status': 'EMPTY_MANIFEST'}, 1
    missing = []
    for name in required:
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            return {**report, 'status': 'INVALID_MANIFEST_PATH'}, 1
        exists = git(root, 'cat-file', '-e', f'{sha}:{name}')
        if exists.returncode or not (root / relative).is_file():
            missing.append(name)
    if missing:
        return {**report, 'status': 'MISSING_DELIVERABLES', 'paths': missing}, 1
    report['required_files'] = len(required)
    if not verify_remote:
        return {**report, 'status': 'LOCAL_ONLY', 'detail': '尚未在线核验远端'}, 2
    configured = git(root, 'remote')
    if remote not in configured.stdout.decode().splitlines():
        return {**report, 'status': 'REMOTE_NOT_CONFIGURED'}, 2
    if branch is None:
        current = git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD')
        if current.returncode:
            return {**report, 'status': 'BRANCH_REQUIRED'}, 2
        branch = current.stdout.decode().strip()
    advertised = git(root, 'ls-remote', '--exit-code', remote, f'refs/heads/{branch}')
    if advertised.returncode:
        return {**report, 'status': 'REMOTE_UNAVAILABLE', 'remote_exit_code': advertised.returncode}, 2
    lines = advertised.stdout.decode().splitlines()
    if len(lines) != 1:
        return {**report, 'status': 'REMOTE_REF_AMBIGUOUS'}, 2
    remote_sha = lines[0].split()[0]
    report.update(remote=remote, branch=branch, remote_commit=remote_sha)
    if remote_sha != sha:
        return {**report, 'status': 'REMOTE_DIFFERS', 'detail': '可能未推送、远端领先或分叉；不执行强推'}, 1
    return {**report, 'durable': True, 'status': 'REMOTE_VERIFIED'}, 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=TOPIC / 'input/交付文件清单.json')
    parser.add_argument('--verify-remote', action='store_true')
    parser.add_argument('--remote', default='origin')
    parser.add_argument('--branch')
    args = parser.parse_args()
    located = git(TOPIC, 'rev-parse', '--show-toplevel')
    if located.returncode:
        raise SystemExit('Not a Git repository')
    root = Path(located.stdout.decode().strip())
    try:
        report, code = inspect(root, args.manifest, args.verify_remote, args.remote, args.branch)
    except (subprocess.TimeoutExpired, OSError, ValueError, KeyError) as error:
        report, code = {'durable': False, 'status': 'CHECK_FAILED', 'error_type': type(error).__name__}, 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(code)


if __name__ == '__main__':
    main()
