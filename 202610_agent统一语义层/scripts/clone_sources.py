"""Recreate fixed, shallow upstream checkouts without overwriting existing work."""
import json
import subprocess
from pathlib import Path


def git(*args, cwd=None):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def main():
    topic = Path(__file__).resolve().parents[1]
    snapshots = json.loads((topic / "intermediate/源码快照.json").read_text(encoding="utf-8"))
    root = topic / "tmp/upstream"
    root.mkdir(parents=True, exist_ok=True)
    for snapshot in snapshots["projects"]:
        directory = root / snapshot["name"]
        if directory.exists():
            if git("rev-parse", "HEAD", cwd=directory) != snapshot["commit"]:
                raise RuntimeError(f"Existing checkout has a different HEAD: {directory}")
            print(f"Already at pinned commit: {snapshot['name']}")
            continue
        directory.mkdir()
        git("init", cwd=directory)
        git("remote", "add", "origin", snapshot["url"], cwd=directory)
        git("fetch", "--depth", "1", "origin", snapshot["commit"], cwd=directory)
        git("checkout", "--detach", "FETCH_HEAD", cwd=directory)
        assert git("rev-parse", "HEAD", cwd=directory) == snapshot["commit"]
        print(f"Cloned pinned commit: {snapshot['name']}")


if __name__ == "__main__":
    main()
