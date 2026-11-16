"""Demo 1: completion-only SFT on arithmetic. Default: real tiny GPT-2 on CPU."""

import argparse
from pathlib import Path

from common import ROOT, SEED, data_splits, evaluate, initialize, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="tiny", help="tiny or a Hugging Face model ID")
    parser.add_argument("--revision", help="Fixed model commit, required for external models")
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--lr", type=float, help="Default: 0.003 for tiny; 0.00002 otherwise")
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "tmp/sft")
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be positive")
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    model, tokenizer = initialize(args.model, args.revision, args.cpu)
    splits = data_splits()
    # The trainer appends EOS to standard prompt-completion records.
    train = Dataset.from_list([
        {"prompt": x["prompt"], "completion": x["answer"]} for x in splits["train"]
    ])
    before = evaluate(model, tokenizer, splits["test"])
    config = SFTConfig(
        output_dir=str(args.output), max_steps=args.steps,
        per_device_train_batch_size=8, learning_rate=args.lr or (0.003 if args.model == "tiny" else 2e-5),
        max_length=32, completion_only_loss=True, packing=False,
        use_cpu=args.cpu or args.model == "tiny", bf16=False, fp16=False,
        gradient_checkpointing=False, report_to="none", save_strategy="no",
        logging_steps=20, seed=SEED, data_seed=SEED, dataloader_num_workers=0,
        optim="adamw_torch",
    )
    trainer = SFTTrainer(model=model, args=config, train_dataset=train, processing_class=tokenizer)
    # Verify actual loss masking, rather than trusting the configuration name.
    batch = trainer.data_collator([trainer.train_dataset[0]])
    prompt_len = len(tokenizer(splits["train"][0]["prompt"])["input_ids"])
    assert (batch["labels"][0, :prompt_len] == -100).all()
    assert (batch["labels"][0, prompt_len:] != -100).any()
    trainer.train()
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    report = {
        "kind": "SFT", "source_model": args.model, "source_revision": args.revision,
        "seed": SEED, "steps": args.steps, "parameters": model.num_parameters(),
        "split_counts": {k: len(v) for k, v in splits.items()},
        "prompt_loss_mask_verified": True,
        "test_before": before, "test_after": evaluate(model, tokenizer, splits["test"]),
        "train_probe_after": evaluate(model, tokenizer, splits["train"]),
        "note": "微型随机初始化语言模型只演示真实训练链路，不能当作大模型效果证据",
    }
    write_json(args.output / "demo_manifest.json", {"source_model": args.model, "source_revision": args.revision, "seed": SEED})
    write_json(args.output / "sft_metrics.json", report)
    print({"checkpoint": str(args.output), "test_before": before["exact_accuracy"], "test_after": report["test_after"]["exact_accuracy"]})


if __name__ == "__main__":
    main()
