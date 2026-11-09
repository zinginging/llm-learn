"""Standard-library lesson with invented token timestamps, NOT a model benchmark.

Every timestamp represents one output token, not an SSE chunk. All times are ms.
No network, model, GPU, credentials or paid API is used.
"""
import json
import math
from statistics import mean


def percentile(values, q):
    """Nearest-rank percentile; empty input is undefined, represented as None."""
    if not 0 < q <= 1:
        raise ValueError("q must be in (0, 1]")
    return sorted(values)[math.ceil(q * len(values)) - 1] if values else None


def summarize(records, ttft_slo=200, tpot_slo=100, e2e_slo=800):
    if not records:
        raise ValueError("No measurement records")
    ids = [row["id"] for row in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate request IDs")
    completed, qualified, tokens = [], 0, 0
    for row in records:
        if row["finish_ms"] < row["submit_ms"]:
            raise ValueError("Finish precedes submission")
        if not row["success"]:
            continue
        ts = row["token_ms"]
        if not ts or ts != sorted(ts) or ts[0] < row["submit_ms"] or ts[-1] > row["finish_ms"]:
            raise ValueError("Invalid per-token timestamps")
        ttft = ts[0] - row["submit_ms"]
        e2e = row["finish_ms"] - row["submit_ms"]
        tpot = (ts[-1] - ts[0]) / (len(ts) - 1) if len(ts) > 1 else None
        completed.append((ttft, tpot, e2e))
        tokens += len(ts)
        qualified += ttft <= ttft_slo and e2e <= e2e_slo and (tpot is None or tpot <= tpot_slo)
    seconds = (max(x["finish_ms"] for x in records) - min(x["submit_ms"] for x in records)) / 1000
    if seconds <= 0:
        raise ValueError("Measurement interval must be positive")
    tpots = [x[1] for x in completed if x[1] is not None]
    return {"submitted": len(records), "completed": len(completed), "output_tokens": tokens,
            "elapsed_s": seconds, "output_tokens_per_s": tokens / seconds,
            "ttft_p95_ms": percentile([x[0] for x in completed], .95),
            "mean_request_tpot_ms": mean(tpots) if tpots else None,
            "e2e_p95_ms": percentile([x[2] for x in completed], .95),
            "slo_qualified": qualified, "goodput_requests_per_s": qualified / seconds,
            "slo_attainment_over_submitted": qualified / len(records),
            "tpot_not_applicable": len(completed) - len(tpots)}


def fixture(first_times, token_interval):
    rows = []
    for index, first in enumerate(first_times):
        ts = [first + step * token_interval for step in range(4)]
        rows.append({"id": str(index), "submit_ms": 0, "token_ms": ts,
                     "finish_ms": ts[-1], "success": True})
    return rows


def main():
    low = summarize(fixture([50, 100, 150, 200], 100))
    high = summarize(fixture([250, 260, 270, 280], 20))
    assert low["output_tokens_per_s"] == 32 and low["slo_qualified"] == 4
    assert high["output_tokens_per_s"] > low["output_tokens_per_s"] and high["slo_qualified"] == 0
    assert percentile([], .95) is None and percentile([1, 2, 3, 4], .95) == 4
    single = summarize([{"id": "one", "submit_ms": 0, "token_ms": [100], "finish_ms": 100, "success": True}])
    assert single["mean_request_tpot_ms"] is None and single["tpot_not_applicable"] == 1
    failed = summarize([{"id": "failed", "submit_ms": 0, "token_ms": [], "finish_ms": 100, "success": False}])
    assert failed["completed"] == failed["slo_qualified"] == 0 and failed["ttft_p95_ms"] is None
    try:
        summarize([{"id": "bad", "submit_ms": 0, "token_ms": [100, 50], "finish_ms": 200, "success": True}])
    except ValueError:
        pass
    else:
        raise AssertionError("Nonmonotonic timestamps should fail")
    kv_bytes = 2 * 32 * 8 * 128 * 2 * 4096
    assert kv_bytes == 512 * 1024**2
    print(json.dumps({"scope": "synthetic arithmetic only, not observed engine performance",
                      "slo_ms": {"ttft": 200, "request_average_tpot": 100, "e2e": 800},
                      "latency_oriented_fixture": low, "throughput_oriented_fixture": high,
                      "conventional_gqa_kv_example_mib": kv_bytes / 1024**2,
                      "edge_checks": ["empty percentile", "single token TPOT undefined", "failed request counted", "invalid timestamps rejected"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
