"""Exercise the delivery gate with disposable Git repositories and a local bare remote."""
import json
import subprocess
import tempfile
from pathlib import Path

from persistence_check import TOPIC, inspect


def run(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True)


def main():
    (TOPIC / 'tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='persistence-gate-', dir=TOPIC / 'tmp') as temp:
        base = Path(temp)
        repo, remote = base / 'repo', base / 'remote.git'
        repo.mkdir()
        run(repo, 'init', '-b', 'work')
        run(repo, 'config', 'user.name', 'Persistence Test Fixture')
        run(repo, 'config', 'user.email', 'fixture@example.invalid')
        report = repo / 'report.md'
        report.write_text('fixture report\n')
        manifest = repo / 'manifest.json'
        manifest.write_text(json.dumps({'required_files': ['report.md', 'manifest.json']}))
        run(repo, 'add', '--', 'report.md', 'manifest.json')
        run(repo, 'commit', '-m', 'fixture initial')
        result, code = inspect(repo, manifest)
        assert code == 2 and not result['durable'] and result['status'] == 'LOCAL_ONLY'
        new = repo / 'untracked-topic'
        new.mkdir()
        (new / 'lost.md').write_text('not committed\n')
        assert inspect(repo, manifest)[0]['status'] == 'LOCAL_CHANGES'
        (new / 'lost.md').unlink()
        new.rmdir()
        report.write_text('modified but not committed\n')
        assert inspect(repo, manifest)[0]['status'] == 'LOCAL_CHANGES'
        run(repo, 'add', '--', 'report.md')
        assert inspect(repo, manifest)[0]['status'] == 'LOCAL_CHANGES'
        run(repo, 'commit', '-m', 'fixture modified')
        remote.mkdir()
        run(remote, 'init', '--bare')
        run(repo, 'remote', 'add', 'origin', str(remote))
        assert inspect(repo, manifest, True)[0]['status'] == 'REMOTE_UNAVAILABLE'
        run(repo, 'push', 'origin', 'work')
        result, code = inspect(repo, manifest, True)
        assert code == 0 and result['durable'] and result['status'] == 'REMOTE_VERIFIED'
        assert inspect(repo, manifest, True, remote='absent')[1] == 2
        report.write_text('committed locally only\n')
        run(repo, 'add', '--', 'report.md')
        run(repo, 'commit', '-m', 'fixture not yet pushed')
        result, code = inspect(repo, manifest, True)
        assert code == 1 and not result['durable'] and result['status'] == 'REMOTE_DIFFERS'
        run(repo, 'push', 'origin', 'work')
        run(repo, 'rm', '--', 'report.md')
        run(repo, 'commit', '-m', 'fixture missing required report')
        run(repo, 'push', 'origin', 'work')
        result, code = inspect(repo, manifest, True)
        assert code == 1 and result['status'] == 'MISSING_DELIVERABLES'
    print('PASS: untracked, modified, staged, local-only, unpushed, unavailable remote, missing file and verified remote states')


if __name__ == '__main__':
    main()
