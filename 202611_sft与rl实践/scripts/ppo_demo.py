"""Real TRL experimental PPO on CPU, with a trainable critic and an exact-rule reward adapter."""

import argparse
import copy
import json
import os
from pathlib import Path

from common import ROOT, SEED, data_splits, evaluate, is_correct, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "tmp/sft")
    parser.add_argument("--output", type=Path, default=ROOT / "tmp/ppo")
    parser.add_argument("--episodes", type=int, default=256)
    args = parser.parse_args()
    if args.episodes < 8:
        parser.error("Use at least 8 episodes")
    metadata = json.loads((args.checkpoint / "demo_manifest.json").read_text())
    if metadata["source_model"] != "tiny":
        raise SystemExit("The rule adapter and verified CPU setup support the tiny tokenizer only")
    os.environ.setdefault("ACCELERATE_USE_CPU", "true")

    import torch
    from torch import nn
    from types import SimpleNamespace
    from datasets import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, GPT2ForSequenceClassification, set_seed
    from trl.experimental.ppo import PPOConfig, PPOTrainer

    set_seed(SEED)
    torch.set_num_threads(2)
    policy = AutoModelForCausalLM.from_pretrained(str(args.checkpoint))
    tokenizer = AutoTokenizer.from_pretrained(str(args.checkpoint), padding_side="left")
    initial = {k: v.detach().clone() for k, v in policy.state_dict().items()}
    value_config = copy.deepcopy(policy.config)
    value_config.num_labels = 1
    critic = GPT2ForSequenceClassification(value_config)
    critic.transformer.load_state_dict(policy.transformer.state_dict())
    critic_initial = {k: v.detach().clone() for k, v in critic.state_dict().items()}

    class ArithmeticBackbone(nn.Module):
        def forward(self, input_ids, **kwargs):
            # PPO's get_reward expects per-position hidden features and a score head.
            # This is a rule verifier wrapped in that interface, NOT a learned reward model.
            import re

            scores = []
            for ids in input_ids:
                text = tokenizer.decode(ids, skip_special_tokens=True)
                match = re.fullmatch(r"([0-5])\+([0-5])=(.*)", text, flags=re.DOTALL)
                scores.append(float(bool(match) and is_correct(match[3], int(match[1]) + int(match[2]))))
            values = torch.tensor(scores, device=input_ids.device, dtype=torch.float32)
            hidden = values[:, None, None].expand(-1, input_ids.shape[1], 1)
            return SimpleNamespace(hidden_states=(hidden,))

    class RuleReward(nn.Module):
        base_model_prefix = "backbone"

        def __init__(self):
            super().__init__()
            self.backbone = ArithmeticBackbone()
            self.score = nn.Identity()

    reward = RuleReward()
    # Positive and negative examples exercise the actual PPO get_reward interface.
    from trl.experimental.utils import get_reward

    token_batch = tokenizer(["2+3=5", "2+3=6"], return_tensors="pt", padding=True)
    _, scores, _ = get_reward(reward, token_batch.input_ids, tokenizer.pad_token_id, 4)
    assert scores.tolist() == [1.0, 0.0]
    splits = data_splits()

    def queries(rows):
        return Dataset.from_list([{"input_ids": tokenizer(r["prompt"])["input_ids"]} for r in rows])

    config = PPOConfig(
        output_dir=str(args.output), total_episodes=args.episodes,
        per_device_train_batch_size=8, per_device_eval_batch_size=1,
        gradient_accumulation_steps=1, num_mini_batches=1, num_ppo_epochs=4,
        local_rollout_forward_batch_size=8, response_length=4,
        temperature=1.0, stop_token="eos", kl_coef=0.02, gamma=1.0, lam=0.95,
        learning_rate=5e-4, use_cpu=True, bf16=False, fp16=False,
        gradient_checkpointing=False, whiten_rewards=False,
        report_to="none", save_strategy="no", num_sample_generations=0,
        seed=SEED, data_seed=SEED, dataloader_num_workers=0,
    )
    before = evaluate(policy, tokenizer, splits["test"])
    trainer = PPOTrainer(
        args=config, processing_class=tokenizer, model=policy, ref_model=copy.deepcopy(policy),
        reward_model=reward, value_model=critic,
        train_dataset=queries(splits["train"]), eval_dataset=queries(splits["validation"]),
    )
    trainer.train()
    policy.save_pretrained(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    critic.save_pretrained(str(args.output / "critic"))
    changed = sum(not torch.equal(v.detach(), initial[k]) for k, v in policy.state_dict().items())
    value_changed = sum(not torch.equal(v.detach(), critic_initial[k]) for k, v in critic.state_dict().items())
    assert changed > 0 and value_changed > 0
    report = {
        "method": "PPO", "implementation": "trl.experimental.ppo 0.28.0", "initial_checkpoint": "tmp/sft",
        "episodes_requested": args.episodes, "seed": SEED, "ppo_epochs_per_batch": 4,
        "policy_tensors_changed": changed, "critic_tensors_changed": value_changed,
        "reward_adapter_positive_negative_check": True,
        "test_before": before, "test_after": evaluate(policy, tokenizer, splits["test"]),
        "train_probe_after": evaluate(policy, tokenizer, splits["train"]),
        "training_logs": trainer.state.log_history,
        "scope": "在线PPO微型训练；奖励为程序规则，critic确实训练，未训练人类偏好奖励模型",
    }
    write_json(args.output / "ppo_metrics.json", report)
    write_json(ROOT / "intermediate/ppo训练结果.json", report)
    print({"method": "PPO", "policy_tensors_changed": changed, "critic_tensors_changed": value_changed, "test_after": report["test_after"]["exact_accuracy"]})


if __name__ == "__main__":
    main()
