"""Network/API demo for the pinned LightRAG source; may incur charges. Not run in research."""

import argparse
import asyncio
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


async def run(with_answer):
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in your shell; do not put keys in this file")
    from lightrag import LightRAG, QueryParam
    from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed

    corpus = json.loads((ROOT / "input/企业知识样例.json").read_text(encoding="utf-8"))
    rag = LightRAG(
        working_dir=str(ROOT / "tmp/lightrag-storage"),
        llm_model_func=gpt_4o_mini_complete,
        embedding_func=openai_embed,
    )
    await rag.initialize_storages()
    try:
        await rag.ainsert(
            [f'Source ID: {d["id"]}\n{d["text"]}' for d in corpus["documents"]],
            ids=[d["id"] for d in corpus["documents"]],
            file_paths=[f'{d["id"]}.txt' for d in corpus["documents"]],
        )
        # The context path can still call an LLM to extract keywords.
        question = corpus["questions"][2]["query"]
        for mode in ("naive", "local", "global", "hybrid", "mix"):
            context = await rag.aquery(
                question,
                param=QueryParam(mode=mode, only_need_context=True, enable_rerank=False),
            )
            print(f"\n--- {mode}: retrieved context ---\n{context}")
        if with_answer:
            answer = await rag.aquery(
                question, param=QueryParam(mode="mix", enable_rerank=False)
            )
            print(f"\n--- generated answer ---\n{answer}")
    finally:
        await rag.finalize_storages()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answer", action="store_true", help="Also generate a final answer")
    args = parser.parse_args()
    asyncio.run(run(args.answer))
