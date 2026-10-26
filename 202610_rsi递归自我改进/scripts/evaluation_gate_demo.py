"""Offline evaluation lesson: synthetic fixtures, no LLM or self-modifying code.

Demonstrates development-set overfitting, a promotion gate, and final audit.
Fixtures share a source file; this is not a secure hidden-test implementation.
"""
from dataclasses import dataclass
import json
from typing import Callable


@dataclass(frozen=True)
class Task:
    key: str
    gross_cents: int
    refunds: tuple[tuple[int, str], ...]


@dataclass(frozen=True)
class Candidate:
    name: str
    predict: Callable[[Task], int]
    cost_units: int  # Invented selection tie-breaker, not measured tokens/time.
    changes_evaluator: bool = False


DEV = [(Task("d1", 10000, ((3000, "confirmed"),)), 7000),
       (Task("d2", 5000, ()), 5000)]
GATE = [(Task("g1", 8000, ((2000, "pending"),)), 8000),
        (Task("g2", 12000, ((1000, "confirmed"), (4000, "pending"))), 11000)]
AUDIT = [(Task("t1", 10000, ((11000, "confirmed"),)), -1000),
         (Task("t2", 0, ()), 0),
         (Task("t3", 9000, ((2000, "confirmed"), (1000, "pending"))), 7000),
         (Task("t4", 30000, ((3000, "confirmed"),)), 27000)]


def score(candidate, cases):
    return sum(candidate.predict(task) == truth for task, truth in cases) / len(cases)


def main():
    baseline = Candidate("gross_only", lambda task: task.gross_cents, 1)
    memorized = {task.key: truth for task, truth in DEV}
    candidates = [
        Candidate("memorize_dev", lambda task: memorized.get(task.key, 0), 1),
        Candidate("subtract_all_refunds", lambda task: task.gross_cents - sum(x for x, _ in task.refunds), 2),
        Candidate("confirmed_refunds_only", lambda task: task.gross_cents - sum(x for x, state in task.refunds if state == "confirmed"), 3),
        Candidate("alter_evaluator", lambda task: 0, 0, changes_evaluator=True),
    ]
    # Development and synthetic cost ranking do not consult GATE or AUDIT.
    ranked = sorted(candidates, key=lambda c: (-score(c, DEV), c.cost_units, c.name))
    naive = ranked[0]
    assert naive.name == "memorize_dev"
    assert score(naive, DEV) == 1 and score(naive, GATE) == 0
    accepted, rejected = [], []
    for candidate in ranked:
        if candidate.changes_evaluator:
            rejected.append({"name": candidate.name, "reason": "protected_artifact"})
        elif score(candidate, GATE) <= score(baseline, GATE):
            rejected.append({"name": candidate.name, "reason": "no_gate_improvement"})
        else:
            accepted.append(candidate)
    assert [c.name for c in accepted] == ["confirmed_refunds_only"]
    promoted = accepted[0]
    # AUDIT is read only after selection, never by the ranker or promotion gate.
    final_score = score(promoted, AUDIT)
    assert final_score == 1
    assert score(baseline, AUDIT) == 0.25
    result = {
        "scope": "deterministic evaluation demonstration, not an RSI reproduction",
        "naive_winner": {"name": naive.name, "dev": score(naive, DEV), "gate": score(naive, GATE)},
        "promoted": {"name": promoted.name, "dev": score(promoted, DEV), "gate": score(promoted, GATE),
                     "audit": final_score, "baseline_audit": score(baseline, AUDIT)},
        "rejected": rejected,
        "case_counts": {"dev": len(DEV), "gate": len(GATE), "audit": len(AUDIT)},
        "limits": ["Candidates are handwritten", "Cost units are invented", "No model or code rewriting",
                   "Gate reused for selection becomes part of meta-development; retain a fresh final audit",
                   "Tiny fixtures provide no statistical or production guarantee"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
