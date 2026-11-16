"""CPU online demos: GRPO, RLOO, Dr.GRPO, GSPO objective, and explicitly partial DAPO components."""

import argparse
import json
from pathlib import Path

from common import ROOT, SEED, correctness_reward, data_splits, evaluate, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=["grpo", "rloo", "dr_grpo", "gspo", "dapo-components"], default="grpo")
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
    tokenizer = AutoTokenizer.from_pretrained(str(args.checkpoint), padding_side="left")
    initial = {k: v.detach().clone() for k, v in model.state_dict().items()}
    splits = data_splits()
    output = args.output or ROOT / "tmp" / f"po-{args.method}"
    config_args = dict(
        output_dir=str(output), max_steps=args.steps,
        per_device_train_batch_size=4, gradient_accumulation_steps=4,
        num_generations=4, generation_batch_size=16, num_iterations=2,
        max_completion_length=4, temperature=1.0, learning_rate=5e-4,
        use_cpu=True, bf16=False, fp16=False, gradient_checkpointing=False,
        report_to="none", save_strategy="no", logging_steps=20,
        seed=SEED, data_seed=SEED, dataloader_num_workers=0,
        remove_unused_columns=False, optim="adamw_torch", use_vllm=False,
    )
    if args.method == "rloo":
        from trl import RLOOConfig, RLOOTrainer

        config = RLOOConfig(**config_args, beta=0.02)
        trainer_type = RLOOTrainer
    else:
        from trl import GRPOConfig, GRPOTrainer

        objective = {"beta": 0.02, "loss_type": "grpo", "scale_rewards": "group"}
        if args.method == "dr_grpo":
            objective.update(beta=0.0, loss_type="dr_grpo", scale_rewards="none")
        elif args.method == "gspo":
            objective.update(beta=0.0, importance_sampling_level="sequence", epsilon=3e-4, epsilon_high=4e-4)
        elif args.method == "dapo-components":
            # Not full DAPO: no online dynamic filtering/resampling or overlong reward shaping.
            objective.update(beta=0.0, loss_type="dapo", epsilon=0.2, epsilon_high=0.28)
        config = GRPOConfig(**config_args, **objective)
        trainer_type = GRPOTrainer
    before = evaluate(model, tokenizer, splits["test"])
    trainer = trainer_type(
        model=model, args=config, train_dataset=Dataset.from_list(splits["train"]),
        reward_funcs=correctness_reward, processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(output))
    tokenizer.save_pretrained(str(output))
    changed = sum(not torch.equal(v.detach(), initial[k]) for k, v in model.state_dict().items())
    assert changed > 0
    report = {
        "method": args.method, "initial_checkpoint": "tmp/sft", "steps": args.steps, "seed": SEED,
        "policy_tensors_changed": changed, "num_generations": 4, "num_iterations": 2,
        "full_dapo": False if args.method == "dapo-components" else None,
        "test_before": before, "test_after": evaluate(model, tokenizer, splits["test"]),
        "train_probe_after": evaluate(model, tokenizer, splits["train"]),
        "training_logs": trainer.state.log_history,
        "scope": "微型在线训练/目标函数验证；不是论文规模复现，也不是算法效果排名",
    }
    write_json(output / "po_metrics.json", report)
    write_json(ROOT / "intermediate" / f"{args.method}_po训练结果.json", report)
    print({"method": args.method, "policy_tensors_changed": changed, "test_after": report["test_after"]["exact_accuracy"]})


if __name__ == "__main__":
    main()
