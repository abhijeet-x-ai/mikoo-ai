# Mikoo AI feasibility calculations

All parameter-footprint values are theoretical. INT4-group and mixed-precision rows include representative metadata assumptions and must be replaced by actual converted-file measurements.

| Parameters | FP32 MB | FP16 MB | INT8 MB | INT4 ideal MB | INT4 group est. MB | Mixed est. MB |
|---:|---:|---:|---:|---:|---:|---:|
| 10M | 40.0 | 20.0 | 10.0 | 5.0 | 5.6 | 8.8 |
| 20M | 80.0 | 40.0 | 20.0 | 10.0 | 11.2 | 17.5 |
| 30M | 120.0 | 60.0 | 30.0 | 15.0 | 16.9 | 26.2 |
| 50M | 200.0 | 100.0 | 50.0 | 25.0 | 28.1 | 43.8 |
| 75M | 300.0 | 150.0 | 75.0 | 37.5 | 42.2 | 65.6 |
| 100M | 400.0 | 200.0 | 100.0 | 50.0 | 56.2 | 87.5 |
| 150M | 600.0 | 300.0 | 150.0 | 75.0 | 84.4 | 131.2 |

## Recommended architecture

- Vocabulary: 24,576; layers: 24; hidden size: 1152; attention heads: 18; KV heads: 2; head dimension: 64; SwiGLU intermediate: 3072; tied embeddings; no bias.
- Exact calculated parameter count: **353,950,848 (353.951M)**.
- Default context target: 512 tokens; 1024-token mode is the controlled upper option; 2048 tokens is a stress test only.

| Context | KV cache FP16 MB | KV cache INT8 MB |
|---:|---:|---:|
| 256 | 3.146 | 1.573 |
| 512 | 6.291 | 3.146 |
| 1024 | 12.583 | 6.291 |
| 2048 | 25.166 | 12.583 |

## Estimated app envelope (not measured)

| Quantization | Context | Estimated peak app MB |
|---|---:|---:|
| INT8 | 512 | 680.2 |
| INT8 | 1024 | 686.5 |
| INT8 | 2048 | 699.1 |
| INT4-group | 512 | 525.4 |
| INT4-group | 1024 | 531.7 |
| INT4-group | 2048 | 544.3 |
| Mixed | 512 | 636.0 |
| Mixed | 1024 | 642.3 |
| Mixed | 2048 | 654.9 |

The envelope reserves 25 MB of explicit headroom and does not represent a physical-device measurement. Actual PSS/RSS depends on Android version, allocator behavior, page residency, thread stacks, model packaging, and background pressure.
