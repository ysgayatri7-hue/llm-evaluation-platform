"""Seed and execute the reproducible synthetic benchmark against a running API."""
import json
from pathlib import Path
import httpx

API="http://localhost:8000/api"
records=[json.loads(line) for line in Path("evaluation/datasets/synthetic_qa.jsonl").read_text().splitlines() if line.strip()]
dataset=httpx.post(f"{API}/datasets",json={"name":"Synthetic QA (development only)","description":"Small synthetic dataset; not research evidence.","is_synthetic":True,"examples":records}).raise_for_status().json()
experiment=httpx.post(f"{API}/experiments",json={"name":"Reproducible mock baseline","dataset_version_id":dataset["versions"][0]["id"],"models":["mock/baseline","mock/challenger"],"metrics":["exact_match","token_f1","faithfulness","consistency"],"repetitions":3,"temperature":0}).raise_for_status().json()
run=httpx.post(f"{API}/experiments/{experiment['id']}/runs").raise_for_status().json();print(json.dumps(run,indent=2))

