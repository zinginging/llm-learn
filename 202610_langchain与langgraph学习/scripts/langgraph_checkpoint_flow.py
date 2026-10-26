"""Offline SQLite checkpoint, interrupt, fan-out/fan-in and bounded retry demo.

No model API, external database, credentials, or production writes. Each worker
runs in a separate process; the parent asserts persistence across worker exit.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, interrupt


class State(TypedDict, total=False):
    month: str
    approved: bool
    sales_cents: int
    refunds_cents: int
    net_cents: int
    status: str


def build(saver, counters):
    def validate(state):
        if state["month"] != "2026-09":
            raise ValueError("The teaching fixture only covers 2026-09")
        return {"status": "validated"}

    def approve(state):
        counters["approval_entries"] += 1
        answer = interrupt({"action": "approve_fixture_query", "month": state["month"]})
        if type(answer) is not bool:
            raise ValueError("Approval must be a boolean")
        return {"approved": answer}

    def sales(state):
        counters["sales_attempts"] += 1
        if counters["sales_attempts"] == 1:
            raise TimeoutError("Synthetic transient failure; no network request")
        return {"sales_cents": 30000}

    def refunds(state):
        counters["refund_calls"] += 1
        return {"refunds_cents": 3000}

    def combine(state):
        return {"net_cents": state["sales_cents"] - state["refunds_cents"],
                "status": "completed"}

    builder = StateGraph(State)
    builder.add_node("validate", validate)
    builder.add_node("approve", approve)
    builder.add_node("sales", sales, retry_policy=RetryPolicy(
        max_attempts=2, initial_interval=0.01, jitter=False, retry_on=TimeoutError))
    builder.add_node("refunds", refunds)
    builder.add_node("combine", combine)
    builder.add_node("denied", lambda state: {"status": "denied"})
    builder.add_edge(START, "validate")
    builder.add_edge("validate", "approve")
    builder.add_conditional_edges("approve", lambda state: "yes" if state["approved"] else "no",
                                  {"yes": "fetch", "no": "denied"})
    builder.add_node("fetch", lambda state: {})
    builder.add_edge("fetch", "sales")
    builder.add_edge("fetch", "refunds")
    builder.add_edge(["sales", "refunds"], "combine")
    builder.add_edge("combine", END)
    builder.add_edge("denied", END)
    return builder.compile(checkpointer=saver)


def worker(database, phase, thread, decision):
    counters = {"approval_entries": 0, "sales_attempts": 0, "refund_calls": 0}
    with SqliteSaver.from_conn_string(database) as saver:
        graph = build(saver, counters)
        config = {"configurable": {"thread_id": thread}, "recursion_limit": 20}
        value = {"month": "2026-09"} if phase == "pause" else Command(resume=decision == "yes")
        result = graph.invoke(value, config=config)
        if phase == "pause":
            assert result["__interrupt__"]
            assert counters == {"approval_entries": 1, "sales_attempts": 0, "refund_calls": 0}
            output = {"phase": phase, "status": "paused", "counters": counters}
        else:
            expected = "completed" if decision == "yes" else "denied"
            assert result["status"] == expected
            assert counters["approval_entries"] == 1  # interrupt node re-enters in this new process.
            if decision == "yes":
                assert result["net_cents"] == 27000
                assert counters["sales_attempts"] == 2 and counters["refund_calls"] == 1
            else:
                assert counters["sales_attempts"] == counters["refund_calls"] == 0
            output = {"phase": phase, "status": expected, "net_cents": result.get("net_cents"),
                      "counters": counters}
        print(json.dumps(output))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--db")
    parser.add_argument("--phase", choices=["pause", "resume"])
    parser.add_argument("--thread")
    parser.add_argument("--decision", choices=["yes", "no"], default="yes")
    args = parser.parse_args()
    if args.worker:
        worker(args.db, args.phase, args.thread, args.decision)
        return
    records = []
    with TemporaryDirectory() as directory:
        database = str(Path(directory) / "checkpoints.sqlite")
        for decision in ["yes", "no"]:
            for phase in ["pause", "resume"]:
                command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--db", database,
                           "--phase", phase, "--thread", f"teaching-{decision}", "--decision", decision]
                result = subprocess.run(command, check=True, text=True, capture_output=True)
                records.append({"decision": decision, **json.loads(result.stdout)})
    print(json.dumps({"separate_process_workers": True, "runs": records}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
