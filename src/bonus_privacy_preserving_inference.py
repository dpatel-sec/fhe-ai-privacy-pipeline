from __future__ import annotations

import json
import re
import time

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

MODEL_CLASSES = {
    "private_prompt_processing": [3, 4, 0, 0, 0, 0, 0, 0],
    "secure_federated_learning": [1, 0, 4, 4, 3, 0, 0, 0],
    "llm_scalability_limits": [0, 0, 0, 0, 0, 4, 4, 4],
}

QUERY_TEXT = (
    "How can FHE protect a user's private prompt while an external AI service "
    "still processes it?"
)


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


def decrypt_scalar(crypto_context, secret_key, ciphertext) -> int:
    plaintext = crypto_context.Decrypt(ciphertext, secret_key)
    plaintext.SetLength(1)
    return int(plaintext.GetPackedValue()[0])


def server_side_inference(crypto_context, encrypted_input):
    encrypted_outputs = {}
    runtime_ms = {}

    for class_name, weights in MODEL_CLASSES.items():
        weights_plaintext = crypto_context.MakePackedPlaintext(weights)
        start = time.perf_counter()
        encrypted_score = crypto_context.EvalInnerProduct(
            encrypted_input, weights_plaintext, len(weights)
        )
        runtime_ms[class_name] = round((time.perf_counter() - start) * 1000, 3)
        encrypted_outputs[class_name] = encrypted_score

    return encrypted_outputs, runtime_ms


def main() -> None:
    crypto_context, key_pair = build_context()

    client_feature_vector = encode_keywords(QUERY_TEXT)
    client_plaintext = crypto_context.MakePackedPlaintext(client_feature_vector)

    client_encrypt_start = time.perf_counter()
    encrypted_input = crypto_context.Encrypt(key_pair.publicKey, client_plaintext)
    client_encrypt_ms = round((time.perf_counter() - client_encrypt_start) * 1000, 3)

    encrypted_outputs, runtime_ms = server_side_inference(crypto_context, encrypted_input)

    client_decrypt_start = time.perf_counter()
    decrypted_scores = {
        class_name: decrypt_scalar(crypto_context, key_pair.secretKey, ciphertext)
        for class_name, ciphertext in encrypted_outputs.items()
    }
    client_decrypt_ms = round((time.perf_counter() - client_decrypt_start) * 1000, 3)

    predicted_label = max(decrypted_scores, key=decrypted_scores.get)

    result = {
        "pipeline": "client encrypts input -> server runs encrypted inference -> client decrypts encrypted output",
        "query_text": QUERY_TEXT,
        "feature_vocab": FEATURE_VOCAB,
        "client_feature_vector": client_feature_vector,
        "model_weights": MODEL_CLASSES,
        "server_runtime_ms": runtime_ms,
        "client_encryption_ms": client_encrypt_ms,
        "client_decryption_ms": client_decrypt_ms,
        "decrypted_scores": decrypted_scores,
        "predicted_label": predicted_label,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
