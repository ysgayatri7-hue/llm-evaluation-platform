import csv,io,json
from fastapi import APIRouter,BackgroundTasks,Depends,HTTPException,Response
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import Dataset,DatasetVersion,DatasetExample,Experiment,EvaluationRun,ModelResponse,MetricResult,HumanAnnotation,ReliabilityAnalysis
from app.schemas.api import DatasetCreate,ExampleIn,ExperimentCreate,RunView,AnnotationCreate,AnalysisCreate
from app.services.analysis import classification_stats
from app.services.runner import execute_run

router=APIRouter(prefix="/api")

def dataset_payload(d):
    versions=sorted(d.versions,key=lambda v:v.version,reverse=True)
    return {"id":d.id,"name":d.name,"description":d.description,"is_synthetic":d.is_synthetic,"created_at":d.created_at,"versions":[{"id":v.id,"version":v.version,"example_count":len(v.examples),"validation_report":v.validation_report} for v in versions]}

@router.get("/health")
def health(db:Session=Depends(get_db)):db.execute(select(1));return {"status":"healthy","database":"ready","mock_mode":True}

@router.get("/metrics/catalog")
def metric_catalog():return [
 {"name":"exact_match","requires":["reference"],"meaning":"Normalized string equality","limitations":"Misses equivalent paraphrases."},
 {"name":"token_f1","requires":["reference"],"meaning":"Token overlap with reference","limitations":"Lexical similarity is not correctness."},
 {"name":"relevance","requires":["prompt"],"meaning":"Prompt/answer token coverage","limitations":"A topical answer can still be wrong."},
 {"name":"faithfulness","requires":["context"],"meaning":"Answer token support in supplied context","limitations":"Does not prove every claim is entailed."},
 {"name":"consistency","requires":["repetitions"],"meaning":"Stability across repeated outputs","limitations":"Consistent answers may be consistently false."}]

@router.get("/datasets")
def list_datasets(db:Session=Depends(get_db)):return [dataset_payload(d) for d in db.scalars(select(Dataset).order_by(Dataset.created_at.desc())).unique()]

@router.post("/datasets",status_code=201)
def create_dataset(payload:DatasetCreate,db:Session=Depends(get_db)):
    if db.scalar(select(Dataset).where(Dataset.name==payload.name)):raise HTTPException(409,"Dataset name already exists")
    d=Dataset(name=payload.name,description=payload.description,is_synthetic=payload.is_synthetic);db.add(d);db.flush();v=DatasetVersion(dataset_id=d.id,version=1,validation_report={"valid":True,"records":len(payload.examples),"warnings":[]});db.add(v);db.flush()
    for i,item in enumerate(payload.examples):db.add(DatasetExample(version_id=v.id,example_id=item.example_id or f"ex-{i+1:04d}",**item.model_dump(exclude={"example_id"})))
    db.commit();db.refresh(d);return dataset_payload(d)

@router.post("/datasets/{dataset_id}/versions",status_code=201)
def new_version(dataset_id:int,examples:list[ExampleIn],db:Session=Depends(get_db)):
    d=db.get(Dataset,dataset_id)
    if not d:raise HTTPException(404,"Dataset not found")
    number=(db.scalar(select(func.max(DatasetVersion.version)).where(DatasetVersion.dataset_id==dataset_id)) or 0)+1;v=DatasetVersion(dataset_id=dataset_id,version=number,validation_report={"valid":bool(examples),"records":len(examples),"warnings":[]});db.add(v);db.flush()
    for i,item in enumerate(examples):db.add(DatasetExample(version_id=v.id,example_id=item.example_id or f"ex-{i+1:04d}",**item.model_dump(exclude={"example_id"})))
    db.commit();return {"id":v.id,"version":v.version,"example_count":len(examples)}

@router.get("/dataset-versions/{version_id}/examples")
def examples(version_id:int,db:Session=Depends(get_db)):
    rows=db.scalars(select(DatasetExample).where(DatasetExample.version_id==version_id)).all();return [{"id":x.id,"example_id":x.example_id,"prompt":x.prompt,"reference_answer":x.reference_answer,"context":x.context,"task_type":x.task_type} for x in rows]

@router.post("/experiments",status_code=201)
def create_experiment(payload:ExperimentCreate,db:Session=Depends(get_db)):
    version=db.get(DatasetVersion,payload.dataset_version_id)
    if not version:raise HTTPException(404,"Dataset version not found")
    needs_ref=set(payload.metrics)&{"exact_match","token_f1"};needs_context="faithfulness" in payload.metrics
    if needs_ref and any(not e.reference_answer for e in version.examples):raise HTTPException(422,f"Metrics {sorted(needs_ref)} require references for every example")
    if needs_context and any(not e.context for e in version.examples):raise HTTPException(422,"Faithfulness requires context for every example")
    if "consistency" in payload.metrics and payload.repetitions<2:raise HTTPException(422,"Consistency requires at least 2 repetitions")
    exp=Experiment(**payload.model_dump());db.add(exp);db.commit();db.refresh(exp);return {"id":exp.id,**payload.model_dump()}

@router.get("/experiments")
def experiments(db:Session=Depends(get_db)):return [{"id":x.id,"name":x.name,"models":x.models,"metrics":x.metrics,"dataset_version_id":x.dataset_version_id,"created_at":x.created_at} for x in db.scalars(select(Experiment).order_by(Experiment.created_at.desc())).all()]

@router.post("/experiments/{experiment_id}/runs",response_model=RunView,status_code=202)
def start_run(experiment_id:int,tasks:BackgroundTasks,db:Session=Depends(get_db)):
    exp=db.get(Experiment,experiment_id)
    if not exp:raise HTTPException(404,"Experiment not found")
    count=db.scalar(select(func.count()).select_from(DatasetExample).where(DatasetExample.version_id==exp.dataset_version_id)) or 0;run=EvaluationRun(experiment_id=experiment_id,total_cases=count*len(exp.models)*exp.repetitions);db.add(run);db.commit();db.refresh(run);tasks.add_task(execute_run,run.id);return run

@router.get("/runs")
def runs(db:Session=Depends(get_db)):return [RunView.model_validate(x) for x in db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc())).all()]

@router.get("/runs/{run_id}",response_model=RunView)
def run_status(run_id:int,db:Session=Depends(get_db)):
    run=db.get(EvaluationRun,run_id)
    if not run:raise HTTPException(404,"Run not found")
    return run

@router.post("/runs/{run_id}/cancel")
def cancel(run_id:int,db:Session=Depends(get_db)):
    run=db.get(EvaluationRun,run_id)
    if not run:raise HTTPException(404,"Run not found")
    run.cancel_requested=True;db.commit();return {"status":"cancellation_requested"}

def result_rows(run_id,db,model=None,metric=None):
    q=select(ModelResponse,DatasetExample).join(DatasetExample,ModelResponse.example_id==DatasetExample.id).where(ModelResponse.run_id==run_id)
    if model:q=q.where(ModelResponse.model==model)
    rows=[]
    for response,ex in db.execute(q):
        ms=db.scalars(select(MetricResult).where(MetricResult.response_id==response.id)).all();mapped={m.metric_name:{"score":m.score,"skip_reason":m.skip_reason,"reasoning":m.reasoning} for m in ms}
        if metric and metric not in mapped:continue
        rows.append({"id":response.id,"example_id":ex.example_id,"prompt":ex.prompt,"reference_answer":ex.reference_answer,"context":ex.context,"task_type":ex.task_type,"model":response.model,"repetition":response.repetition,"output":response.output,"latency_ms":response.latency_ms,"tokens":(response.prompt_tokens or 0)+(response.completion_tokens or 0),"estimated_cost_usd":response.estimated_cost_usd,"usage_is_estimated":response.usage_is_estimated,"error":response.error,"metrics":mapped})
    return rows

@router.get("/runs/{run_id}/results")
def results(run_id:int,model:str|None=None,metric:str|None=None,db:Session=Depends(get_db)):return result_rows(run_id,db,model,metric)

@router.post("/annotations",status_code=201)
def annotate(payload:AnnotationCreate,db:Session=Depends(get_db)):
    if not db.get(ModelResponse,payload.response_id):raise HTTPException(404,"Response not found")
    row=HumanAnnotation(**payload.model_dump());db.add(row);db.commit();db.refresh(row);return {"id":row.id,**payload.model_dump()}

@router.post("/analyses",status_code=201)
def analyze(payload:AnalysisCreate,db:Session=Depends(get_db)):
    pairs=db.execute(select(MetricResult.score,HumanAnnotation.correctness).join(ModelResponse,MetricResult.response_id==ModelResponse.id).join(HumanAnnotation,HumanAnnotation.response_id==ModelResponse.id).where(ModelResponse.run_id==payload.run_id,MetricResult.metric_name==payload.metric_name,MetricResult.score.is_not(None),HumanAnnotation.correctness.is_not(None))).all();pred=[int(s>=payload.threshold) for s,_ in pairs];actual=[int(a) for _,a in pairs];stats=classification_stats(pred,actual);limitations=["Human labels are a comparison standard, not infallible ground truth.","Small samples can make agreement estimates unstable."]
    row=ReliabilityAnalysis(run_id=payload.run_id,metric_name=payload.metric_name,threshold=payload.threshold,sample_size=len(pairs),statistics=stats,limitations=limitations);db.add(row);db.commit();db.refresh(row);return {"id":row.id,"statistics":stats,"limitations":limitations}

@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db)):
    run_count=db.scalar(select(func.count()).select_from(EvaluationRun)) or 0;dataset_count=db.scalar(select(func.count()).select_from(Dataset)) or 0;models=set(m for row in db.scalars(select(Experiment)).all() for m in row.models);avg=db.execute(select(MetricResult.metric_name,func.avg(MetricResult.score)).where(MetricResult.score.is_not(None)).group_by(MetricResult.metric_name)).all();cost=db.scalar(select(func.sum(ModelResponse.estimated_cost_usd))) or 0;latency=db.scalar(select(func.avg(ModelResponse.latency_ms))) or 0
    return {"runs":run_count,"datasets":dataset_count,"models":len(models),"average_metrics":{n:round(v,3) for n,v in avg},"estimated_cost_usd":round(cost,6),"average_latency_ms":round(latency,1),"mock_mode":True}

@router.get("/runs/{run_id}/export.{format}")
def export_results(run_id:int,format:str,db:Session=Depends(get_db)):
    data=result_rows(run_id,db)
    if format=="json":return Response(json.dumps(data,default=str,indent=2),media_type="application/json",headers={"Content-Disposition":f"attachment; filename=evalai-run-{run_id}.json"})
    if format=="csv":
        out=io.StringIO();fields=["example_id","model","repetition","prompt","reference_answer","output","latency_ms","tokens","estimated_cost_usd","error"];writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader();writer.writerows([{k:r.get(k) for k in fields} for r in data]);return Response(out.getvalue(),media_type="text/csv",headers={"Content-Disposition":f"attachment; filename=evalai-run-{run_id}.csv"})
    raise HTTPException(400,"Format must be csv or json")

