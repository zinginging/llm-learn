"""Validate question provenance, coverage, local links, syntax, and optional raw-source hashes."""

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest_path = ROOT / "input/问题清单.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frozen = json.loads((ROOT / "intermediate/问题冻结记录.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == frozen["sha256"], "Frozen question list changed"
    assert len(manifest["questions"]) == 60
    ids = [q["id"] for q in manifest["questions"]]
    assert ids == [f"Q{i:02}" for i in range(1, 61)]
    assert sum(q["origin_type"] == "公开问题归纳" for q in manifest["questions"]) == 55
    assert sum(q["origin_type"] == "研究扩展题" for q in manifest["questions"]) == 5

    actual_ids = []
    for module in manifest["modules"]:
        path = ROOT / "output" / f"{module['id']}_{module['title']}.md"
        text = path.read_text(encoding="utf-8")
        headings = re.findall(r"^## (Q\d{2})\b", text, flags=re.MULTILINE)
        expected = [q["id"] for q in manifest["questions"] if q["module"] == module["id"]]
        assert headings == expected, (path.name, headings, expected)
        for qid in headings:
            assert f'<a id="{qid.lower()}"></a>' in text
        actual_ids.extend(headings)
    assert actual_ids == ids
    assert all(set(q["source_ids"]) <= set(manifest["sources"]) for q in manifest["questions"])

    retained = [p for p in ROOT.rglob("*") if p.is_file() and "tmp" not in p.relative_to(ROOT).parts
                and "__pycache__" not in p.parts and p.name != "产物校验.json"]
    link_count = 0
    for path in retained:
        text = path.read_text(encoding="utf-8")
        assert all(line.rstrip() == line for line in text.splitlines()), f"Whitespace: {path}"
        if path.suffix == ".py":
            ast.parse(text, filename=str(path))
        elif path.suffix == ".json":
            json.loads(text)
        elif path.suffix == ".md":
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in link or link.startswith("#"):
                    continue
                relative, _, fragment = link.partition("#")
                target = (path.parent / relative).resolve()
                assert target.exists(), (path.name, link)
                if re.fullmatch(r"q\d{2}", fragment):
                    assert f'<a id="{fragment}"></a>' in target.read_text(encoding="utf-8"), (path.name, fragment)
                link_count += 1

    technical = json.loads((ROOT / "intermediate/答案技术来源快照.json").read_text(encoding="utf-8"))
    assert len(technical) == 39 and len({s["id"] for s in technical}) == 39
    checked, missing = 0, []
    for source in technical:
        assert source["status"] == "fetched", source["id"]
        assert datetime.fromisoformat(source["checked_at_utc"]) > datetime.fromisoformat(frozen["frozen_at_utc"])
        local = ROOT / source["local_file"]
        if local.exists():
            assert hashlib.sha256(local.read_bytes()).hexdigest() == source["sha256"], source["id"]
            checked += 1
        else:
            missing.append(source["id"])
    result = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(), "status": "passed",
        "question_count": len(ids), "modules": len(manifest["modules"]),
        "collected_questions": 55, "research_extensions": 5,
        "question_manifest_unchanged": True, "technical_sources_acquired_after_question_freeze": True,
        "technical_sources": len(technical), "raw_hashes_verified": checked,
        "raw_hashes_skipped_missing_tmp": missing, "local_links_checked": link_count,
        "retained_files_checked_excluding_this_report": len(retained),
        "scope": "文档、题目映射、JSON/Python语法与资料快照校验；不是模型/服务运行测试",
    }
    target = ROOT / "intermediate/产物校验.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
