# FHE-AI Privacy Pipeline

**Repository description:** A Python demonstration of fully homomorphic encryption for encrypted feature processing, privacy-preserving inference, and hybrid Hugging Face LLM integration using OpenFHE.

This course project explores how Fully Homomorphic Encryption (FHE) can protect data while a server performs useful AI-related computation. It uses OpenFHE's BFV scheme for exact encrypted arithmetic and a small Hugging Face language model for the hybrid LLM demonstration.

## What This Project Demonstrates

- Encryption of packed numeric feature vectors with OpenFHE.
- Homomorphic addition and multiplication with results verified after decryption.
- A plaintext-versus-FHE performance comparison.
- Encrypted reference scoring before a small Hugging Face model creates a response.
- A bonus privacy-preserving inference pipeline: the client encrypts input, the server evaluates an encrypted classifier, and only the client decrypts the prediction.

## Repository Layout

```text
src/
  main_demo.py                         # Benchmark, encrypted retrieval, and HF demo
  bonus_privacy_preserving_inference.py # Client-server encrypted inference demo
  generate_llm_response.py             # Isolated Hugging Face inference helper
  openfhe_runtime.py                   # OpenFHE import helper
examples/
  openfhe_simple_integers.py            # OpenFHE arithmetic example
docs/
  REPORT.md                             # Full written report
  REPORT.docx                           # Word version of the report
  INSTALL_OPENFHE.md                    # Linux and macOS installation notes
  GITHUB_UPLOAD_STEPS.md                # How to publish this repository
results/                                # Saved terminal outputs and JSON results
screenshots/                            # Project output screenshots
```

## Quick Start

OpenFHE installation is platform-specific. Follow [the installation guide](docs/INSTALL_OPENFHE.md) first, then run:

```bash
python -m pip install -r requirements.txt
python src/main_demo.py
python src/bonus_privacy_preserving_inference.py
```

The Hugging Face model is downloaded and cached in `.hf_cache/` on the first main-demo run. It is intentionally ignored by Git because it is large and can be reproduced from the public `distilgpt2` model.

## Expected Results

The main demo writes fresh data to `results/results.json` and `results/summary.txt`. In the recorded run, encrypted and plaintext arithmetic results matched exactly, while homomorphic operations were significantly slower than plaintext operations. The encrypted reference-selection stage also selected the same best reference as plaintext scoring.

The bonus demo prints a pipeline where the server receives encrypted features, calculates encrypted class scores, and returns ciphertext. The client alone decrypts the scores and chooses the label.

## Important Scope Note

The Hugging Face part is a hybrid pipeline: encrypted retrieval happens first, then the selected reference is supplied to the language model in plaintext. The bonus pipeline is the end-to-end encrypted inference demonstration, using a small linear classifier. Fully encrypted inference for GPT-scale transformer models is still impractical for typical hardware because of computational cost, ciphertext growth, and deep nonlinear computation.

## References

- [OpenFHE documentation](https://openfhe-development.readthedocs.io/)
- [OpenFHE Python wrapper](https://github.com/openfheorg/openfhe-python)
- [OpenFHE Python API documentation](https://openfheorg.github.io/openfhe-python/html/index.html)
