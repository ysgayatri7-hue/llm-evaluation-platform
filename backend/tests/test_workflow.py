def dataset_payload(name="Research QA"):
    return {"name":name,"examples":[{"example_id":"q1","prompt":"What is the capital of France?","reference_answer":"Paris","context":"France's capital is Paris.","task_type":"factual_qa"},{"example_id":"q2","prompt":"What planet is known as the Red Planet?","reference_answer":"Mars","context":"Mars is known as the Red Planet.","task_type":"factual_qa"}]}

def test_end_to_end_mock_workflow(client):
    ds=client.post("/api/datasets",json=dataset_payload()).json();version=ds["versions"][0]["id"]
    exp=client.post("/api/experiments",json={"name":"Mock benchmark","dataset_version_id":version,"models":["mock/accurate","mock/challenger"],"metrics":["exact_match","token_f1","faithfulness","consistency"],"repetitions":2}).json()
    response=client.post(f"/api/experiments/{exp['id']}/runs");assert response.status_code==202;run=response.json();status=client.get(f"/api/runs/{run['id']}").json();assert status["status"]=="completed";assert status["completed_cases"]==8
    results=client.get(f"/api/runs/{run['id']}/results").json();assert len(results)==8;assert "exact_match" in results[0]["metrics"]
    annotation=client.post("/api/annotations",json={"response_id":results[0]["id"],"reviewer":"researcher@example.org","correctness":1,"relevance":5,"faithfulness":5});assert annotation.status_code==201
    analysis=client.post("/api/analyses",json={"run_id":run["id"],"metric_name":"exact_match"}).json();assert analysis["statistics"]["sample_size"]==1
    assert client.get(f"/api/runs/{run['id']}/export.csv").status_code==200

def test_validation_and_versioning(client):
    ds=client.post("/api/datasets",json=dataset_payload("Versioned")).json();version=client.post(f"/api/datasets/{ds['id']}/versions",json=[{"prompt":"New question"}]);assert version.json()["version"]==2
    bad=client.post("/api/experiments",json={"name":"Invalid","dataset_version_id":version.json()["id"],"models":["mock/a"],"metrics":["exact_match"]});assert bad.status_code==422

def test_metric_edges():
    from app.evaluators.metrics import exact_match,token_f1,faithfulness
    assert exact_match("Paris!","paris")[0]==1;assert token_f1("red planet mars","mars")[0]>0;assert faithfulness("answer",None)[1]

