"""Offline AST checks of cloned source; verifies interfaces, not runtime behavior."""

import ast
import json
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "tmp/upstream"


def parse(repo, relative):
    return ast.parse((UPSTREAM / repo / relative).read_text(encoding="utf-8"))


def find(tree, name, kind):
    return next(n for n in ast.walk(tree) if isinstance(n, kind) and n.name == name)


def signature(repo, relative, name, expected):
    tree = parse(repo, relative)
    node = find(tree, name, (ast.FunctionDef, ast.AsyncFunctionDef))
    arguments = [a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
    assert set(expected) <= set(arguments), (repo, name, arguments)
    return {"path": relative, "name": name, "line": node.lineno, "arguments": arguments}


def main():
    snapshots = json.loads((ROOT / "intermediate/仓库快照.json").read_text(encoding="utf-8"))
    records = []
    for snapshot in snapshots:
        name = snapshot["name"]
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=UPSTREAM / name, text=True
        ).strip()
        assert revision == snapshot["commit"]
        project = tomllib.loads((UPSTREAM / name / "pyproject.toml").read_text())["project"]
        if name == "graphrag":
            project = tomllib.loads((UPSTREAM / name / "packages/graphrag/pyproject.toml").read_text())["project"]
        version = project.get("version")
        if name == "lightrag":
            tree = parse(name, "lightrag/_version.py")
            version = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__version__" for t in n.targets))
        records.append({"repository": snapshot["repository"], "commit": revision,
                        "package": project["name"], "package_version": version,
                        "requires_python": project["requires-python"]})

    checks = [
        signature("graphrag", "packages/graphrag/graphrag/cli/main.py", "_initialize_cli", ["root", "model", "embedding_model"]),
        signature("graphrag", "packages/graphrag/graphrag/cli/main.py", "_query_cli", ["query", "root", "method"]),
        signature("lightrag", "lightrag/lightrag.py", "ainsert", ["input", "ids", "file_paths"]),
        signature("lightrag", "lightrag/lightrag.py", "aquery", ["query", "param"]),
        signature("hipporag", "src/hipporag/HippoRAG.py", "__init__", ["save_dir", "embedding_provider", "llm_model_name", "embedding_model_name"]),
        signature("hipporag", "src/hipporag/HippoRAG.py", "index", ["docs"]),
        signature("hipporag", "src/hipporag/HippoRAG.py", "retrieve", ["queries", "num_to_retrieve"]),
        signature("hipporag", "src/hipporag/HippoRAG.py", "rag_qa", ["queries"]),
    ]
    query_param = find(parse("lightrag", "lightrag/base.py"), "QueryParam", ast.ClassDef)
    mode = next(n for n in query_param.body if isinstance(n, ast.AnnAssign) and n.target.id == "mode")
    assert ast.literal_eval(mode.value) == "mix"
    allowed = list(ast.literal_eval(mode.annotation.slice))
    assert set(allowed) == {"local", "global", "hybrid", "mix", "naive", "bypass"}
    init = (UPSTREAM / "graphrag/packages/graphrag/graphrag/config/init_content.py").read_text()
    assert "completion_models:" in init and "embedding_models:" in init
    result = {"checked_at": "2026-11-09", "scope": "提交身份、包元数据、AST 参数及配置模板静态核对；不包含安装、导入和模型调用", "versions": records, "interfaces": checks,
              "lightrag_query_default": "mix", "lightrag_modes": allowed,
              "graphrag_generated_model_sections": ["completion_models", "embedding_models"]}
    (ROOT / "intermediate/源码核对.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(records)} repository revisions and {len(checks)} callable signatures")


if __name__ == "__main__":
    main()
