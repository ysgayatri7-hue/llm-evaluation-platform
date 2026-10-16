# EvalAI example experiment report

> **Development evidence only.** This report was generated from an actually executed deterministic mock-provider run on a synthetic dataset. It is not a real LLM benchmark.

## Configuration

- Run: #1 (completed)
- Dataset: Synthetic QA report fixture, 4 examples
- Models: mock/baseline, mock/challenger
- Repetitions: 3; temperature: 0
- Metrics: exact match, token F1, lexical faithfulness, response consistency
- Completed calls: 24 / 24; errors: 0

## Aggregate comparison

| Model | Mean available metric score | Mean latency (ms) | Estimated cost | Failed calls |
|---|---:|---:|---:|---:|
| mock/baseline | 0.838 | 23.5 | $0.000034 | 0 |
| mock/challenger | 0.607 | 24.4 | $0.000058 | 0 |

Scores combine different deterministic development metrics for interface verification only. They are not calibrated correctness probabilities. Cost and usage values are estimates from fixture rates.

## Reliability and limitations

No evaluator-versus-human statistic is reported because this executed run did not collect an independently reviewed representative sample. Synthetic fixture labels are not substituted for fresh human review. Exact match misses paraphrases; token overlap and lexical faithfulness do not prove truth; consistency can reward stable false answers. See `example-run-results.json` for every response, score, usage estimate and error field.
