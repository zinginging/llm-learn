"""Demo 2: online GRPO from the SFT checkpoint, with programmatically verifiable reward."""

import argparse
import json
from pathlib import Path

from common import ROOT, SEED, correctness_reward, data_splits, evaluate, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "tmp/sft")
    parser.add_argument("--output", type=Path, default=ROOT / "tmp/grpo")
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--lr", type=float)
    parser.add_argument("--cpu", action="store_true")
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be positive")
    import torch
    from datasets import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from trl import GRPOConfig, GRPOTrainer

    if not (args.checkpoint / "demo_manifest.json").exists():
        raise SystemExit("Run sft_demo.py first and pass its checkpoint directory")
    metadata = json.loads((args.checkpoint / "demo_manifest.json").read_text())
    tiny = metadata["source_model"] == "tiny"
    set_seed(SEED)
    torch.set_num_threads(2)
    model = AutoModelForCausalLM.from_pretrained(str(args.checkpoint))
    tokenizer = AutoTokenizer.from_pretrained(str(args.checkpoint), padding_side="left")
    splits = data_splits()
    # No completion labels: answer is only provided to the reward callback.
    train = Dataset.from_list(splits["train"])
    before = evaluate(model, tokenizer, splits["test"])
    config = GRPOConfig(
        output_dir=str(args.output), max_steps=args.steps,
        per_device_train_batch_size=4, gradient_accumulation_steps=4,
        num_generations=4, generation_batch_size=16,
        max_completion_length=4, temperature=1.0,
        learning_rate=args.lr or (5e-4 if tiny else 5e-6),
        beta=0.02, loss_type="grpo", scale_rewards="group",
        use_cpu=args.cpu or tiny, bf16=False, fp16=False,
        gradient_checkpointing=False, report_to="none", save_strategy="no",
        logging_steps=20, seed=SEED, data_seed=SEED, dataloader_num_workers=0,
        remove_unused_columns=False, optim="adamw_torch", use_vllm=False,
    )
    trainer = GRPOTrainer(
        model=model, args=config, train_dataset=train,
        reward_funcs=correctness_reward, processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    report = {
        "kind": "online GRPO", "initial_checkpoint": str(args.checkpoint),
        "seed": SEED, "steps": args.steps, "num_generations": 4, "beta": 0.02,
        "test_before": before, "test_after": evaluate(model, tokenizer, splits["test"]),
        "train_probe_after": evaluate(model, tokenizer, splits["train"]),
        "training_logs": trainer.state.log_history,
        "note": "在线采样和更新已执行；奖励来自训练题的程序判定，不消费测试答案",
    }
    write_json(args.output / "rl_metrics.json", report)
    print({"checkpoint": str(args.output), "test_before": before["exact_accuracy"], "test_after": report["test_after"]["exact_accuracy"]})


if __name__ == "__main__":
    main()
