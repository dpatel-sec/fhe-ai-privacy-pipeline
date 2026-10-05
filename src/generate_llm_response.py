from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
HF_CACHE = Path(os.environ.get("FHE_AI_HF_CACHE", ROOT / ".hf_cache"))
MODEL_LABEL = "distilgpt2"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("expected selected reference text")

    selected_reference_text = sys.argv[1]
    HF_CACHE.mkdir(exist_ok=True)
    os.environ.setdefault("HF_HOME", str(HF_CACHE))
    os.environ.setdefault("OMP_NUM_THREADS", "1")

    torch.set_num_threads(1)
    torch.set_grad_enabled(False)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_LABEL, cache_dir=HF_CACHE)
    model = AutoModelForCausalLM.from_pretrained(MODEL_LABEL, cache_dir=HF_CACHE)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    prompt = (
        "Context: "
        f"{selected_reference_text}\n"
        "Question: Explain in one short sentence how this supports privacy-preserving AI.\n"
        "Answer:"
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    output = model.generate(
        **inputs,
        max_new_tokens=20,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    generated_tokens = output[0][inputs["input_ids"].shape[1] :]
    generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

    print(
        json.dumps(
            {
                "model_id": MODEL_LABEL,
                "prompt": prompt,
                "generated_text": generated_text,
            }
        )
    )


if __name__ == "__main__":
    main()
