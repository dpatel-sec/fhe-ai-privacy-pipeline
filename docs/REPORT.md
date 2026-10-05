# Fully Homomorphic Encryption in AI and Large Language Models

## 1. Introduction

Fully Homomorphic Encryption (FHE) allows computation to be performed directly on encrypted data. Unlike conventional encryption, where data must be decrypted before useful processing can happen, FHE preserves confidentiality during computation itself. This property is attractive for AI because it addresses a common tension: organizations want to use cloud-hosted models, but the prompts, features, and training signals they send to those models may contain sensitive personal, financial, medical, or proprietary information.

For this assignment, I studied OpenFHE, implemented a small OpenFHE-based benchmark in Python, and built a hybrid AI pipeline in which encrypted feature vectors are processed before a small Hugging Face language model is used for the final explanation step.

## 2. What FHE Is and How It Differs from Traditional Encryption

Traditional symmetric or public-key encryption protects stored or transmitted data, but once computation is needed, the system normally has to decrypt the data first. That decryption step creates a privacy exposure point because the server, memory, or application logic can now see the plaintext.

FHE removes that requirement. A client encrypts data, sends ciphertext to a server, and the server evaluates supported operations over the ciphertext. When the result is returned and decrypted by the key holder, it matches the result that would have been obtained from the original plaintext computation. In practice, FHE supports arithmetic circuits and, depending on the scheme, either exact integer arithmetic or approximate real-number arithmetic.

The main advantage is privacy during outsourced computation. The main disadvantages are higher latency, larger ciphertexts, more memory use, and a restricted set of efficient operations compared with ordinary plaintext machine learning.

## 3. OpenFHE: Capabilities, Tools, and Limitations

OpenFHE is an open-source FHE library that supports multiple schemes, including BFV and BGV for exact integer arithmetic and CKKS for approximate real-number arithmetic. The library also includes Boolean-circuit functionality through TFHE/FHEW-style components. OpenFHE provides C++ and Python interfaces, example programs, and benchmarking tools.

For this project, OpenFHE was useful because it already exposes the core operations needed for a small AI-style workflow: key generation, packing vectors into plaintext slots, encryption, homomorphic addition, homomorphic multiplication, and encrypted inner products. These are enough to build toy encrypted feature pipelines and privacy-preserving retrieval experiments.

The library also has practical limitations. The official `openfhe-python` package is easiest to install on supported Ubuntu versions, so on this macOS/arm64 machine I built OpenFHE and `openfhe-python` from source. More importantly, OpenFHE does not make full transformer inference cheap. Deep matrix multiplications, nonlinear activations, normalization steps, and long-context attention all amplify FHE costs. Therefore OpenFHE is currently more realistic for narrow encrypted preprocessing, scoring, aggregation, or private retrieval than for full GPT-scale inference.

## 4. Practical Implementation

### 4.1 Setup

I built OpenFHE natively from source, compiled the `openfhe-python` wrapper against that local install, and ran the final scripts from a Python virtual environment. For the AI integration step, I used the small Hugging Face model `distilgpt2`, which can be downloaded and cached locally on the first run.

### 4.2 Encrypted Arithmetic Demo

I used the BFV scheme because it is well suited to exact integer arithmetic. Two packed integer vectors were encrypted and processed with homomorphic addition and homomorphic multiplication. The decrypted outputs matched the plaintext outputs exactly.

| Operation | Plaintext Result | Encrypted Result |
| --- | --- | --- |
| Addition | `[9, 9, 9, 9, 9, 9, 9, 9]` | `[9, 9, 9, 9, 9, 9, 9, 9]` |
| Multiplication | `[8, 14, 18, 20, 20, 18, 14, 8]` | `[8, 14, 18, 20, 20, 18, 14, 8]` |

### 4.3 Performance Overhead

The benchmark clearly shows the expected cost of privacy-preserving computation.

| Metric | Measured Time |
| --- | --- |
| Plaintext addition average | `0.000236 ms` |
| Plaintext multiplication average | `0.000218 ms` |
| Ciphertext encryption | `4.983 ms` |
| Homomorphic addition | `0.062 ms` |
| Homomorphic multiplication | `4.019 ms` |
| Ciphertext decryption | `0.754 ms` |

The encrypted addition was about `261x` slower than plaintext addition, while encrypted multiplication was about `18,426x` slower than plaintext multiplication. This gap is the central engineering challenge of FHE in AI: privacy is preserved, but arithmetic becomes much more expensive.

## 5. Integration with AI

### 5.1 Encrypted Reference Processing

To connect FHE with a language-model workflow, I built a small encrypted retrieval stage. I defined three short reference sentences related to:

- encrypted prompt processing
- secure federated learning
- FHE scalability bottlenecks

Each reference was converted into a compact integer feature vector using a small keyword vocabulary:

`[privacy, prompt, federated, learning, updates, bootstrapping, latency, memory]`

The query:

`"How does FHE help with privacy-preserving prompt processing for AI systems?"`

was encoded into the vector `[1, 1, 0, 0, 0, 0, 0, 0]`.

Using OpenFHE BFV, I computed encrypted inner products between the encrypted query and each encrypted reference vector. The plaintext scores were `[2, 0, 0]`, and the encrypted scores matched exactly as `[2, 0, 0]`. The average encrypted inner-product time was `5.855 ms`, and the selected reference was the prompt-processing sentence.

This demonstrates a realistic hybrid design: encrypted data can be used for private scoring or retrieval first, and only the selected downstream context is exposed for later model use.

### 5.2 Small Hugging Face Model Demo

After the encrypted retrieval step selected the best reference, I passed that reference to a small Hugging Face model (`distilgpt2`) to show how an AI component can be attached to the privacy-preserving front end. The generated continuation was:

`"Encrypted prompt processing lets a cloud service run useful computations without ever seeing the user prompt in plain"`

This is not a polished final answer, but it is enough to show the integration pattern: FHE can protect the earlier data-processing stage, while a lightweight language model handles the user-facing response. In practice, a stronger small model or a task-specific summarizer would improve output quality.

## 6. Feasibility for Large Language Models

End-to-end FHE inference for GPT-like models is still difficult. The reasons are:

- transformers perform many chained matrix multiplications and nonlinear steps
- bootstrapping is expensive when multiplicative depth becomes large
- ciphertexts are far larger than plaintext tensors
- attention over long contexts increases both latency and memory pressure
- approximate schemes such as CKKS introduce numerical noise that must be carefully managed

Because of these issues, applying FHE to every layer of a large language model is not yet practical for mainstream deployment. A more feasible near-term strategy is selective protection: use FHE for private retrieval, scoring, statistics, or small linear layers, and combine it with trusted execution environments, secure enclaves, or conventional encryption for the rest of the system.

## 7. Critical Analysis and Optimizations

The main trade-off is security versus computational cost. FHE gives strong privacy guarantees because computation happens without exposing plaintext, but those guarantees come with substantial runtime and resource overhead. My benchmark already shows this gap on tiny vectors, and the problem becomes much larger for full LLM pipelines.

Several optimizations or alternatives are reasonable:

- use hybrid systems where only the sensitive preprocessing stage is encrypted
- use smaller feature representations or dimensionality reduction before FHE
- choose BFV/BGV for exact integer workloads and CKKS only when approximate real arithmetic is truly needed
- combine FHE with secure enclaves for parts of the pipeline where pure FHE is too slow
- use federated learning or secure aggregation when the goal is collaborative model updates rather than encrypted full-model inference

## 8. Conclusion

This assignment shows that OpenFHE can successfully support privacy-preserving arithmetic and encrypted feature scoring in a Python workflow. The homomorphic results matched the plaintext results exactly, and the encrypted retrieval stage selected the same reference as the plaintext version. However, the measured overhead confirms that full FHE-based LLM inference is still limited by performance and scalability. Today, the most practical path is a hybrid architecture in which FHE protects sensitive sub-computations while smaller conventional AI components handle the final user interaction.

## References

1. OpenFHE documentation: <https://openfhe-development.readthedocs.io/>
2. OpenFHE Python wrapper: <https://github.com/openfheorg/openfhe-python>
3. OpenFHE Python API docs: <https://openfheorg.github.io/openfhe-python/html/index.html>
