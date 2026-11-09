"""Export the shared fictional corpus into an isolated, git-ignored CLI workspace."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    corpus = json.loads((ROOT / "input/企业知识样例.json").read_text(encoding="utf-8"))
    target = ROOT / "tmp/graphrag-work/input"
    target.mkdir(parents=True, exist_ok=True)
    for document in corpus["documents"]:
        (target / f'{document["id"]}.txt').write_text(
            f'Source ID: {document["id"]}\n{document["text"]}\n', encoding="utf-8"
        )
    print(f"Exported {len(corpus['documents'])} fictional documents to {target}")


if __name__ == "__main__":
    main()
