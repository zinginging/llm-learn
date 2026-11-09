"""Network/API demo for the pinned HippoRAG 2 source; may incur charges. Not run in research."""

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(with_answer):
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in your shell; do not put keys in this file")
    from hipporag import Chunk, HippoRAG

    corpus = json.loads((ROOT / "input/企业知识样例.json").read_text(encoding="utf-8"))
    chunks = [
        Chunk(content=f'Source ID: {d["id"]}\n{d["text"]}', source_id=d["id"])
        for d in corpus["documents"]
    ]
    queries = [q["query"] for q in corpus["questions"]]
    with HippoRAG(
        save_dir=str(ROOT / "tmp/hipporag-storage"),
        llm_model_name="gpt-4o-mini",
        embedding_model_name="text-embedding-3-small",
        embedding_provider="openai",
    ) as rag:
        rag.index(docs=chunks)
        solutions = rag.retrieve(queries=queries, num_to_retrieve=5)
        for result in solutions:
            print(json.dumps(result.to_dict(), ensure_ascii=False, default=str))
        if with_answer:
            # Passing retrieved QuerySolution objects avoids a second retrieval.
            answers, messages, metadata = rag.rag_qa(queries=solutions)
            for result in answers:
                print(json.dumps(result.to_dict(), ensure_ascii=False, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answer", action="store_true", help="Also run QA on retrieved evidence")
    args = parser.parse_args()
    run(args.answer)
