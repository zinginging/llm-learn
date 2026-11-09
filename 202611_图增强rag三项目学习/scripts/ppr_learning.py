"""Offline, standard-library PPR lesson on a manually curated graph; no engine benchmark."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def personalized_pagerank(graph, seeds, damping=0.5, tolerance=1e-13):
    """Use row-normalized edges and redistribute dangling mass to the reset vector."""
    if not graph or not 0 <= damping < 1:
        raise ValueError("A nonempty graph and 0 <= damping < 1 are required")
    if not seeds or not set(seeds) <= set(graph):
        raise ValueError("Seeds must name graph nodes")
    if any(not math.isfinite(w) or w < 0 for w in seeds.values()):
        raise ValueError("Seed weights must be finite and nonnegative")
    for targets in graph.values():
        if not set(targets) <= set(graph):
            raise ValueError("Every target must be a graph node")
        if any(not math.isfinite(w) or w < 0 for w in targets.values()):
            raise ValueError("Edge weights must be finite and nonnegative")
    total = sum(seeds.values())
    if total <= 0:
        raise ValueError("Positive seed mass is required")
    reset = {node: seeds.get(node, 0) / total for node in graph}
    scores = reset.copy()
    for iteration in range(1, 10001):
        nxt = {n: (1 - damping) * reset[n] for n in graph}
        dangling = 0.0
        for node, targets in graph.items():
            weight = sum(targets.values())
            if weight == 0:
                dangling += damping * scores[node]
            else:
                for target, edge_weight in targets.items():
                    nxt[target] += damping * scores[node] * edge_weight / weight
        for node in graph:
            nxt[node] += dangling * reset[node]
        residual = sum(abs(nxt[n] - scores[n]) for n in graph)
        scores = nxt
        if residual < tolerance:
            return scores, iteration, residual
    raise RuntimeError("PPR did not converge")


def main():
    pair, _, _ = personalized_pagerank({"A": {"B": 1}, "B": {"A": 1}}, {"A": 1})
    assert math.isclose(pair["A"], 2 / 3, abs_tol=1e-12)
    assert math.isclose(pair["B"], 1 / 3, abs_tol=1e-12)
    tie, _, _ = personalized_pagerank({"A": {"B": 1}, "B": {"A": 1}}, {"A": 1, "B": 1})
    assert math.isclose(tie["A"], tie["B"], abs_tol=1e-12)
    dangling, _, _ = personalized_pagerank({"A": {"B": 1}, "B": {}}, {"A": 1})
    assert math.isclose(sum(dangling.values()), 1, abs_tol=1e-12)
    for bad in ({}, {"missing": 1}, {"A": 0}, {"A": -1}):
        try:
            personalized_pagerank({"A": {}}, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid seeds accepted")

    # Deliberately omit time labels: relevance can spread to both old and new facts.
    edges = [
        ("北辰项目", "林悦"), ("林悦", "澄海科技"), ("澄海科技", "杭州"),
        ("北辰项目", "陈舟"), ("陈舟", "远山系统公司"), ("远山系统公司", "深圳"),
    ]
    graph = {}

    def connect(a, b):
        graph.setdefault(a, {})[b] = 1.0
        graph.setdefault(b, {})[a] = 1.0

    for number, (a, b) in enumerate(edges, 1):
        connect(a, b)
        connect(f"d{number}", a)
        connect(f"d{number}", b)
    scores, iterations, residual = personalized_pagerank(graph, {"北辰项目": 1})
    assert math.isclose(sum(scores.values()), 1, abs_tol=1e-12)
    assert scores["d3"] > 0 and scores["d6"] > 0
    assert math.isclose(scores["d3"], scores["d6"], abs_tol=1e-12)
    ranked = sorted(
        ({"source_id": n, "score": score} for n, score in scores.items() if n.startswith("d")),
        key=lambda row: (-row["score"], row["source_id"]),
    )
    result = {
        "kind": "人工图教学演算；未调用 HippoRAG 2 或任何模型",
        "damping": 0.5, "seeds": {"北辰项目": 1},
        "iterations": iterations, "l1_step_difference": residual,
        "all_node_mass": sum(scores.values()), "ranked_passages": ranked,
        "observations": ["旧总部 d3 与新总部 d6 获得相同分数", "图相关性不能替代时间有效性判断"],
        "checks": ["two_node_hand_calculation", "tied_scores", "dangling_node_mass", "invalid_seeds", "temporal_counterexample"],
    }
    target = ROOT / "intermediate/ppr教学结果.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
