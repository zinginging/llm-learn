"""Shared data, a real tiny autoregressive Transformer, and an exact arithmetic verifier."""

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SEED = 17


def data_splits():
    """Group a+b and b+a together; never expose validation/test targets to training."""
    splits = {"train": [], "validation": [], "test": []}
    for a in range(6):
        for b in range(6):
            key = f"{min(a, b)}:{max(a, b)}"
            bucket = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % 7
            split = "test" if bucket == 0 else "validation" if bucket == 1 else "train"
            splits[split].append({"prompt": f"{a}+{b}=", "answer": str(a + b)})
    assert all(splits.values())
    return splits


def is_correct(text, answer):
    """Only one canonical integer is accepted, never a number buried in prose."""
    text = text.strip()
    return bool(re.fullmatch(r"(?:0|[1-9][0-9]{0,2})", text)) and text == str(answer)


def correctness_reward(completions, answer, **kwargs):
    """TRL passes answer as metadata, not as part of the model's prompt."""
    if len(completions) != len(answer):
        raise ValueError("Completion and answer counts differ")
    return [float(is_correct(text, gold)) for text, gold in zip(completions, answer)]


def tiny_model():
    """Random GPT-2 architecture with a local character tokenizer; no downloads."""
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers
    from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast

    vocab = {s: i for i, s in enumerate(["<pad>", "<eos>", "<unk>"] + list("0123456789+="))}
    backend = Tokenizer(models.WordLevel(vocab, unk_token="<unk>"))
    backend.pre_tokenizer = pre_tokenizers.Split(pattern="", behavior="isolated")
    backend.decoder = decoders.Fuse()
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=backend, eos_token="<eos>", pad_token="<pad>",
        unk_token="<unk>", model_max_length=32,
    )
    config = GPT2Config(
        vocab_size=len(vocab), n_positions=32, n_ctx=32, n_embd=32,
        n_layer=2, n_head=2, resid_pdrop=0, embd_pdrop=0, attn_pdrop=0,
        bos_token_id=None, eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )
    model = GPT2LMHeadModel(config)
    return model, tokenizer


def initialize(model_id, revision=None, cpu=False):
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    import torch

    set_seed(SEED)
    torch.set_num_threads(2)
    if model_id == "tiny":
        return tiny_model()
    if not revision:
        raise ValueError("Pass --revision with a fixed model commit for external models")
    model = AutoModelForCausalLM.from_pretrained(
        model_id, revision=revision, torch_dtype=torch.float32, trust_remote_code=False,
        attn_implementation="eager",
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, trust_remote_code=False)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer


def evaluate(model, tokenizer, rows):
    import torch

    model.eval()
    output = []
    with torch.no_grad():
        for row in rows:
            inputs = tokenizer(row["prompt"], return_tensors="pt").to(model.device)
            generated = model.generate(
                **inputs, max_new_tokens=4, do_sample=False,
                eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id,
            )
            text = tokenizer.decode(generated[0, inputs.input_ids.shape[1]:], skip_special_tokens=True)
            output.append({**row, "generated": text, "correct": is_correct(text, row["answer"])})
    return {"count": len(rows), "exact_accuracy": sum(x["correct"] for x in output) / len(rows), "examples": output}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
