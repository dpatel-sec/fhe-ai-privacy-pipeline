from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"

from openfhe_runtime import CCParamsBFVRNS, GenCryptoContext, PKESchemeFeature


FEATURE_VOCAB = [
    "privacy",
    "prompt",
    "federated",
    "learning",
    "updates",
    "bootstrapping",
    "latency",
    "memory",
]

REFERENCE_TEXTS = [
    "Encrypted prompt processing lets a cloud service run useful computations "
    "without ever seeing the user prompt in plaintext.",
    "Secure federated learning can combine private model updates from multiple "
    "organizations while reducing raw data exposure.",
    "The largest obstacles for FHE in large language models are bootstrapping "
    "latency, ciphertext expansion, and memory pressure.",
]

QUERY_TEXT = (
    "How does FHE help with privacy-preserving prompt processing for AI systems?"
)

MODEL_LABEL = "distilgpt2"


def encode_keywords(text: str) -> list[int]:
    tokens = re.findall(r"[a-z]+", text.lower())
    return [tokens.count(keyword) for keyword in FEATURE_VOCAB]


def build_context():
    parameters = CCParamsBFVRNS()
    parameters.SetPlaintextModulus(65537)
    parameters.SetMultiplicativeDepth(2)

    crypto_context = GenCryptoContext(parameters)
    crypto_context.Enable(PKESchemeFeature.PKE)
    crypto_context.Enable(PKESchemeFeature.KEYSWITCH)
    crypto_context.Enable(PKESchemeFeature.LEVELEDSHE)
    crypto_context.Enable(PKESchemeFeature.ADVANCEDSHE)

    key_pair = crypto_context.KeyGen()
    crypto_context.EvalMultKeyGen(key_pair.secretKey)
    crypto_context.EvalSumKeyGen(key_pair.secretKey)
    return crypto_context, key_pair


def decrypt_int_vector(crypto_context, secret_key, ciphertext, expected_length: int) -> list[int]:
    plaintext = crypto_context.Decrypt(ciphertext, secret_key)
    plaintext.SetLength(expected_length)
    return list(plaintext.GetPackedValue())[:expected_length]


def benchmark_plaintext_and_fhe() -> dict:
    crypto_context, key_pair = build_context()

    vector_a = [1, 2, 3, 4, 5, 6, 7, 8]
    vector_b = [8, 7, 6, 5, 4, 3, 2, 1]

    arr_a = np.array(vector_a, dtype=np.int64)
    arr_b = np.array(vector_b, dtype=np.int64)

    plaintext_loops = 10_000

    start = time.perf_counter()
    for _ in range(plaintext_loops):
        plain_add = arr_a + arr_b
    plaintext_add_ms = ((time.perf_counter() - start) / plaintext_loops) * 1000

    start = time.perf_counter()
    for _ in range(plaintext_loops):
        plain_mul = arr_a * arr_b
    plaintext_mul_ms = ((time.perf_counter() - start) / plaintext_loops) * 1000

    plaintext_a = crypto_context.MakePackedPlaintext(vector_a)
    plaintext_b = crypto_context.MakePackedPlaintext(vector_b)

    start = time.perf_counter()
    ciphertext_a = crypto_context.Encrypt(key_pair.publicKey, plaintext_a)
    ciphertext_b = crypto_context.Encrypt(key_pair.publicKey, plaintext_b)
    encryption_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    ciphertext_add = crypto_context.EvalAdd(ciphertext_a, ciphertext_b)
    fhe_add_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    ciphertext_mul = crypto_context.EvalMult(ciphertext_a, ciphertext_b)
    fhe_mul_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    decrypted_add = decrypt_int_vector(
        crypto_context, key_pair.secretKey, ciphertext_add, len(vector_a)
    )
    decrypted_mul = decrypt_int_vector(
        crypto_context, key_pair.secretKey, ciphertext_mul, len(vector_a)
    )
    decryption_ms = (time.perf_counter() - start) * 1000

    return {
        "plaintext": {
            "vector_a": vector_a,
            "vector_b": vector_b,
            "add_result": plain_add.tolist(),
            "mul_result": plain_mul.tolist(),
            "avg_add_ms": round(plaintext_add_ms, 6),
            "avg_mul_ms": round(plaintext_mul_ms, 6),
        },
        "fhe": {
            "encrypted_add_result": decrypted_add,
            "encrypted_mul_result": decrypted_mul,
            "encryption_ms": round(encryption_ms, 3),
            "eval_add_ms": round(fhe_add_ms, 3),
            "eval_mul_ms": round(fhe_mul_ms, 3),
            "decryption_ms": round(decryption_ms, 3),
            "add_overhead_x": round(fhe_add_ms / plaintext_add_ms, 2),
            "mul_overhead_x": round(fhe_mul_ms / plaintext_mul_ms, 2),
        },
    }


def run_encrypted_retrieval() -> dict:
    crypto_context, key_pair = build_context()

    reference_vectors = [encode_keywords(text) for text in REFERENCE_TEXTS]
    query_vector = encode_keywords(QUERY_TEXT)
    plaintext_scores = [
        int(np.dot(np.array(reference), np.array(query_vector)))
        for reference in reference_vectors
    ]

    query_plaintext = crypto_context.MakePackedPlaintext(query_vector)
    query_ciphertext = crypto_context.Encrypt(key_pair.publicKey, query_plaintext)

    encrypted_scores = []
    encrypted_eval_times_ms = []

    for reference in reference_vectors:
        reference_plaintext = crypto_context.MakePackedPlaintext(reference)
        reference_ciphertext = crypto_context.Encrypt(key_pair.publicKey, reference_plaintext)

        start = time.perf_counter()
        score_ciphertext = crypto_context.EvalInnerProduct(
            reference_ciphertext, query_ciphertext, len(query_vector)
        )
        encrypted_eval_times_ms.append((time.perf_counter() - start) * 1000)

        score_plaintext = crypto_context.Decrypt(score_ciphertext, key_pair.secretKey)
        score_plaintext.SetLength(1)
        encrypted_scores.append(int(score_plaintext.GetPackedValue()[0]))

    best_index = int(np.argmax(encrypted_scores))

    return {
        "feature_vocab": FEATURE_VOCAB,
        "query_text": QUERY_TEXT,
        "query_vector": query_vector,
        "reference_vectors": reference_vectors,
        "plaintext_scores": plaintext_scores,
        "encrypted_scores": encrypted_scores,
        "avg_encrypted_eval_ms": round(float(np.mean(encrypted_eval_times_ms)), 3),
        "selected_reference_index": best_index,
        "selected_reference_text": REFERENCE_TEXTS[best_index],
    }


def run_hugging_face_demo(selected_reference_text: str) -> dict:
    helper_script = Path(__file__).with_name("generate_llm_response.py")
    completed = subprocess.run(
        [sys.executable, str(helper_script), selected_reference_text],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout.strip().splitlines()[-1])


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    arithmetic_results = benchmark_plaintext_and_fhe()
    retrieval_results = run_encrypted_retrieval()
    llm_results = run_hugging_face_demo(retrieval_results["selected_reference_text"])

    combined = {
        "arithmetic_benchmark": arithmetic_results,
        "encrypted_retrieval": retrieval_results,
        "llm_demo": llm_results,
    }

    results_path = RESULTS_DIR / "results.json"
    summary_path = RESULTS_DIR / "summary.txt"

    results_path.write_text(json.dumps(combined, indent=2), encoding="utf-8")

    summary_lines = [
        "FHE benchmark summary",
        f"Plaintext add avg (ms): {arithmetic_results['plaintext']['avg_add_ms']}",
        f"Plaintext mul avg (ms): {arithmetic_results['plaintext']['avg_mul_ms']}",
        f"Encrypted add (ms): {arithmetic_results['fhe']['eval_add_ms']}",
        f"Encrypted mul (ms): {arithmetic_results['fhe']['eval_mul_ms']}",
        f"Selected encrypted reference index: {retrieval_results['selected_reference_index']}",
        f"Selected encrypted reference text: {retrieval_results['selected_reference_text']}",
        f"HF model: {llm_results['model_id']}",
        f"HF output: {llm_results['generated_text']}",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(json.dumps(combined, indent=2))


if __name__ == "__main__":
    main()
