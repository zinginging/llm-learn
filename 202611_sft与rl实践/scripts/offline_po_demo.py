"""CPU preference-training demos: DPO, IPO, SimPO, ORPO, KTO. All branch from the same SFT model."""

import argparse
import copy
import json
from pathlib import Path

from common import ROOT, SEED, data_splits, evaluate, write_json


def preference_records(rows):
    return [
        {"prompt": r["prompt"], "chosen": r["answer"], "rejected": str((int(r["answer"]) + 1) % 11)}
        for r in rows
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=["dpo", "ipo", "simpo", "orpo", "kto"], default="dpo")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "tmp/sft")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--steps", type=int, default=40)
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be positive")
    metadata = json.loads((args.checkpoint / "demo_manifest.json").read_text())
    if metadata["source_model"] != "tiny":
        raise SystemExit("This verified CPU example supports the local tiny model only")

    import torch
    from datasets import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    set_seed(SEED)
    torch.set_num_threads(2)
    model = AutoModelForCausalLM.from_pretrained(str(args.checkpoint))
    tokenizer = AutoTokenizer.from_pretrained(str(args.checkpoint), padding_side="right")
    initial = {k: v.detach().clone() for k, v in model.state_dict().items()}
    splits = data_splits()
    pairs = preference_records(splits["train"])
    assert all(p["chosen"] != p["rejected"] for p in pairs)
    output = args.output or ROOT / "tmp" / args.method
    common = dict(
        output_dir=str(output), max_steps=args.steps, per_device_train_batch_size=8,
        learning_rate=1e-4, max_length=32,
        use_cpu=True, bf16=False, fp16=False, gradient_checkpointing=False,
        report_to="none", save_strategy="no", logging_steps=20,
        seed=SEED, data_seed=SEED, dataloader_num_workers=0, optim="adamw_torch",
    )
    train = Dataset.from_list(pairs)
    if args.method in ("dpo", "ipo"):
        from trl import DPOConfig, DPOTrainer

        config = DPOConfig(**common, beta=0.1, loss_type=["sigmoid" if args.method == "dpo" else "ipo"])
        trainer = DPOTrainer(
            model=model, ref_model=copy.deepcopy(model), args=config,
            processing_class=tokenizer, train_dataset=train,
        )
    elif args.method == "simpo":
        from trl.experimental.cpo import CPOConfig, CPOTrainer

        # Disable the CPO NLL term: leaving cpo_alpha=1 would change the objective.
        config = CPOConfig(**common, loss_type="simpo", beta=2.0, simpo_gamma=1.0, cpo_alpha=0.0)
        trainer = CPOTrainer(model=model, args=config, processing_class=tokenizer, train_dataset=train)
    elif args.method == "orpo":
        from trl.experimental.orpo import ORPOConfig, ORPOTrainer

        config = ORPOConfig(**common, beta=0.1)
        trainer = ORPOTrainer(model=model, args=config, processing_class=tokenizer, train_dataset=train)
    else:
        from trl.experimental.kto import KTOConfig, KTOTrainer

        unpaired = []
        for pair in pairs:
            unpaired.extend([
                {"prompt": pair["prompt"], "completion": pair["chosen"], "label": True},
                {"prompt": pair["prompt"], "completion": pair["rejected"], "label": False},
            ])
        train = Dataset.from_list(unpaired)
        config = KTOConfig(**common, beta=0.1, desirable_weight=1.0, undesirable_weight=1.0)
        trainer = KTOTrainer(
            model=model, ref_model=copy.deepcopy(model), args=config,
            processing_class=tokenizer, train_dataset=train,
        )
    before = evaluate(model, tokenizer, splits["test"])
    trainer.train()
    trainer.save_model(str(output))
    tokenizer.save_pretrained(str(output))
    changed = sum(not torch.equal(v.detach(), initial[k]) for k, v in model.state_dict().items())
    assert changed > 0, "No policy parameters changed"
    report = {
        "method": args.method, "initial_checkpoint": "tmp/sft", "steps": args.steps,
        "seed": SEED, "training_rows": len(train), "policy_tensors_changed": changed,
        "test_before": before, "test_after": evaluate(model, tokenizer, splits["test"]),
        "train_probe_after": evaluate(model, tokenizer, splits["train"]),
        "training_logs": trainer.state.log_history,
        "scope": "固定SFT起点的微型语言模型训练；人工偏好标签来自算术程序，不是人类偏好评测",
    }
    write_json(output / "po_metrics.json", report)
    write_json(ROOT / "intermediate" / f"{args.method}训练结果.json", report)
    print({"method": args.method, "policy_tensors_changed": changed, "test_after": report["test_after"]["exact_accuracy"]})


if __name__ == "__main__":
    main()
