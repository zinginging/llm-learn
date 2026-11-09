"""Standard-library interview lessons. Synthetic data only; no LLM, network, GPU, or cluster."""

import hashlib
import json
import math
import platform
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def jaccard(a, b):
    if not a or not b:
        raise ValueError("Empty documents must be handled separately")
    return len(a & b) / len(a | b)


def minhash(values, size=256):
    if not values:
        raise ValueError("Empty documents have no signature in this lesson")
    return [
        min(int.from_bytes(hashlib.sha256(f"{seed}:{v}".encode()).digest()[:8], "big") for v in values)
        for seed in range(size)
    ]


def candidate_probability(similarity, bands, rows):
    if not 0 <= similarity <= 1 or bands < 1 or rows < 1:
        raise ValueError("Invalid LSH parameters")
    return 1 - (1 - similarity**rows)**bands


def ir_metrics(gold, retrieved, k):
    if k < 1:
        raise ValueError("k must be positive")
    if not gold:
        return None  # Unanswerable queries are evaluated separately.
    ranked = list(dict.fromkeys(retrieved))[:k]
    rel = [int(doc in gold) for doc in ranked]
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rel))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(len(gold), k)))
    return {
        "recall": len(gold.intersection(ranked)) / len(gold),
        "reciprocal_rank": next((1 / (i + 1) for i, r in enumerate(rel) if r), 0),
        "ndcg_binary": dcg / ideal,
        "all_evidence": gold.issubset(ranked),
    }


def masked_loss(probabilities, mask):
    if len(probabilities) != len(mask) or any(m not in (0, 1) for m in mask):
        raise ValueError("Probability and binary mask lengths must agree")
    if sum(mask) == 0:
        raise ValueError("No supervised tokens")
    if any(not 0 < p <= 1 for p in probabilities):
        raise ValueError("Probabilities must be in (0, 1]")
    return -sum(m * math.log(p) for p, m in zip(probabilities, mask)) / sum(mask)


def sql_examples():
    db = sqlite3.connect(":memory:")
    try:
        db.executescript("""
        CREATE TABLE scores(person_id TEXT, score INTEGER);
        INSERT INTO scores VALUES ('a',100),('b',100),('c',90),('d',NULL);
        CREATE TABLE orders(order_id TEXT, customer_id TEXT, amount INTEGER);
        INSERT INTO orders VALUES ('o1','c1',100);
        CREATE TABLE customers(customer_id TEXT, label TEXT);
        INSERT INTO customers VALUES ('c1','x'),('c1','duplicate');
        CREATE TABLE payments(day INTEGER, amount INTEGER);
        INSERT INTO payments VALUES (1,10),(1,20),(2,5);
        CREATE TABLE state(entity_id TEXT PRIMARY KEY, source_version INTEGER,
                           payload TEXT, deleted INTEGER);
        """)
        ranked = db.execute("""
        SELECT person_id, ROW_NUMBER() OVER (ORDER BY score DESC, person_id),
               RANK() OVER (ORDER BY score DESC),
               DENSE_RANK() OVER (ORDER BY score DESC)
        FROM scores WHERE score IS NOT NULL ORDER BY score DESC, person_id
        """).fetchall()
        assert ranked == [("a", 1, 1, 1), ("b", 2, 1, 1), ("c", 3, 3, 2)]
        inflated = db.execute("""
        SELECT SUM(o.amount) FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        """).fetchone()[0]
        assert inflated == 200
        frames = db.execute("""
        SELECT day, amount,
          SUM(amount) OVER (ORDER BY day, amount ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
          SUM(amount) OVER (ORDER BY day RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        FROM payments ORDER BY day, amount
        """).fetchall()
        assert frames == [(1, 10, 10, 30), (1, 20, 30, 30), (2, 5, 35, 35)]

        def apply(event):
            key, version, payload, deleted = event
            previous = db.execute("SELECT source_version,payload,deleted FROM state WHERE entity_id=?", (key,)).fetchone()
            if previous and previous[0] == version and previous[1:] != (payload, deleted):
                raise ValueError("Conflicting payloads for the same current version")
            db.execute("""
            INSERT INTO state VALUES (?,?,?,?)
            ON CONFLICT(entity_id) DO UPDATE SET
              source_version=excluded.source_version,
              payload=excluded.payload, deleted=excluded.deleted
            WHERE excluded.source_version > state.source_version
            """, event)

        # Teaching assumption: a single authoritative source has monotonic versions per key.
        events = [("doc1", 1, "old", 0), ("doc1", 3, "new", 0), ("doc1", 2, "late", 0)]
        for event in events + events:
            apply(event)
        assert db.execute("SELECT payload FROM state").fetchone()[0] == "new"
        apply(("doc1", 4, "", 1))
        apply(("doc1", 1, "old", 0))
        tombstone = db.execute("SELECT source_version,deleted FROM state").fetchone()
        assert tombstone == (4, 1)
        try:
            apply(("doc1", 4, "conflict", 0))
        except ValueError:
            pass
        else:
            raise AssertionError("A version conflict was silently accepted")
        return {"ranking": ranked, "join_amount_expected": 100, "join_amount_actual": inflated,
                "rows_vs_range": frames, "cdc_final_version_and_tombstone": tombstone}
    finally:
        db.close()


def main():
    a, b = {"a", "b", "c"}, {"b", "c", "d"}
    sa, sb = minhash(a), minhash(b)
    exact = jaccard(a, b)
    assert exact == 0.5 and sa == minhash(a)
    assert jaccard(a, b) == jaccard(b, a)
    assert candidate_probability(0.5, 2, 1) == 0.75
    assert candidate_probability(0, 2, 1) == 0
    assert candidate_probability(1, 2, 1) == 1
    for function in (lambda: jaccard(set(), a), lambda: minhash(set()), lambda: masked_loss([0.5], [0])):
        try:
            function()
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid boundary was accepted")
    loss = masked_loss([0.1, 0.8, 0.5], [0, 1, 1])
    assert math.isclose(loss, -math.log(0.4) / 2)
    assert math.isclose(masked_loss([0.8, 0.5], [1, 1]), loss)
    metrics = ir_metrics({"A", "B"}, ["A", "C", "B"], 3)
    assert metrics["recall"] == 1 and metrics["reciprocal_rank"] == 1
    assert math.isclose(metrics["ndcg_binary"], 0.9197207891481876)
    assert ir_metrics(set(), ["A"], 3) is None
    assert ir_metrics({"A"}, [], 3)["recall"] == 0
    assert ir_metrics({"A", "B"}, ["A", "A", "C", "B"], 3) == metrics
    probabilities = [math.sqrt(9) / (math.sqrt(9) + math.sqrt(1)), 1 / 4]
    assert sum(probabilities) == 1 and probabilities == [0.75, 0.25]
    result = {
        "scope": "人工数据的SQL及算术实验；未运行真实LLM、Spark、Ray、Flink、Kafka或GPU",
        "python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
        "sql": sql_examples(),
        "dedup": {"jaccard": exact, "minhash_estimate_256": sum(x == y for x, y in zip(sa, sb)) / 256,
                  "lsh_ideal_probability": candidate_probability(0.5, 2, 1),
                  "note": "hash家族用于教学，未证明独立随机排列假设；不据此评估实际去重准确率"},
        "token_mixture_alpha_0_5": probabilities,
        "masked_sft_loss": loss, "dpo_loss_beta_1_delta_1": math.log1p(math.exp(-1)),
        "retrieval_metrics": metrics,
        "capacity_example": {"tokens": 100_000_000 * 500, "minutes_at_5m_tpm": 100_000_000 * 500 / 5_000_000,
                             "raw_vector_bytes": 100_000_000 * 1536 * 4},
        "checks": ["ties_and_nulls", "join_fanout", "rows_range_peers", "cdc_replay_and_tombstone",
                   "version_conflict", "empty_documents", "lsh_boundaries", "all_labels_masked",
                   "metric_empty_gold", "metric_empty_results", "duplicate_results", "sampling_normalization"],
    }
    (ROOT / "intermediate/离线演算结果.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
