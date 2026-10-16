"""Execute a clean local experiment and persist an evidence-based example report."""
import json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
os.environ["DATABASE_URL"]=f"sqlite:///{(ROOT/'work'/'example-report.db').as_posix()}"
from fastapi.testclient import TestClient
from app.main import app

records=[json.loads(line) for line in (ROOT/"evaluation/datasets/synthetic_qa.jsonl").read_text().splitlines() if line.strip()]
with TestClient(app) as client:
    existing=client.get("/api/datasets").json()
    if existing:
        version=existing[0]["versions"][0]["id"]
    else:
        dataset=client.post("/api/datasets",json={"name":"Synthetic QA report fixture","description":"Development-only synthetic questions.","is_synthetic":True,"examples":records}).json();version=dataset["versions"][0]["id"]
    exp=client.post("/api/experiments",json={"name":"Executed mock comparison","dataset_version_id":version,"models":["mock/baseline","mock/challenger"],"metrics":["exact_match","token_f1","faithfulness","consistency"],"repetitions":3,"temperature":0,"notes":"Generated locally with the deterministic mock provider."}).json()
    run=client.post(f"/api/experiments/{exp['id']}/runs").json();status=client.get(f"/api/runs/{run['id']}").json();results=client.get(f"/api/runs/{run['id']}/results").json()

out=ROOT/"outputs";out.mkdir(exist_ok=True)
(out/"example-run-results.json").write_text(json.dumps({"run":status,"experiment":exp,"results":results},indent=2),encoding="utf-8")
models={}
for row in results:
    m=models.setdefault(row["model"],{"scores":[],"latency":[],"cost":0,"failures":0})
    m["scores"] += [v["score"] for v in row["metrics"].values() if v["score"] is not None];m["latency"].append(row["latency_ms"]);m["cost"]+=row["estimated_cost_usd"] or 0;m["failures"]+=bool(row["error"])
table="\n".join(f"| {name} | {sum(v['scores'])/len(v['scores']):.3f} | {sum(v['latency'])/len(v['latency']):.1f} | ${v['cost']:.6f} | {v['failures']} |" for name,v in models.items())
report=f"""# EvalAI example experiment report

> **Development evidence only.** This report was generated from an actually executed deterministic mock-provider run on a synthetic dataset. It is not a real LLM benchmark.

## Configuration

- Run: #{status['id']} ({status['status']})
- Dataset: Synthetic QA report fixture, 4 examples
- Models: mock/baseline, mock/challenger
- Repetitions: 3; temperature: 0
- Metrics: exact match, token F1, lexical faithfulness, response consistency
- Completed calls: {status['completed_cases']} / {status['total_cases']}; errors: {status['error_count']}

## Aggregate comparison

| Model | Mean available metric score | Mean latency (ms) | Estimated cost | Failed calls |
|---|---:|---:|---:|---:|
{table}

Scores combine different deterministic development metrics for interface verification only. They are not calibrated correctness probabilities. Cost and usage values are estimates from fixture rates.

## Reliability and limitations

No evaluator-versus-human statistic is reported because this executed run did not collect an independently reviewed representative sample. Synthetic fixture labels are not substituted for fresh human review. Exact match misses paraphrases; token overlap and lexical faithfulness do not prove truth; consistency can reward stable false answers. See `example-run-results.json` for every response, score, usage estimate and error field.
"""
(out/"example-experiment-report.md").write_text(report,encoding="utf-8")
print(json.dumps({"status":status,"models":list(models),"report":str(out/"example-experiment-report.md")},indent=2))

