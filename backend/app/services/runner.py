from datetime import datetime,timezone
from sqlalchemy import select
from app.db.session import SessionLocal
from app.evaluators.metrics import REGISTRY,token_f1
from app.models.entities import DatasetExample,EvaluationRun,Experiment,MetricResult,ModelResponse,RunStatus
from app.providers.mock import MockProvider

def execute_run(run_id):
    db=SessionLocal();provider=MockProvider();run=None
    try:
        run=db.get(EvaluationRun,run_id);exp=db.get(Experiment,run.experiment_id);examples=db.scalars(select(DatasetExample).where(DatasetExample.version_id==exp.dataset_version_id)).all()
        run.status=RunStatus.running;run.started_at=datetime.now(timezone.utc);db.commit();grouped={}
        for ex in examples:
            for model in exp.models:
                for rep in range(1,exp.repetitions+1):
                    db.refresh(run)
                    if run.cancel_requested:run.status=RunStatus.cancelled;run.completed_at=datetime.now(timezone.utc);db.commit();return
                    try:
                        g=provider.generate(model,exp.prompt_template.format(prompt=ex.prompt),ex.reference_answer,rep)
                        response=ModelResponse(run_id=run.id,example_id=ex.id,model=model,repetition=rep,output=g.text,latency_ms=g.latency_ms,prompt_tokens=g.prompt_tokens,completion_tokens=g.completion_tokens,estimated_cost_usd=g.estimated_cost_usd,usage_is_estimated=g.usage_is_estimated);db.add(response);db.flush();grouped.setdefault((ex.id,model),[]).append(response)
                        for name in exp.metrics:
                            if name=="consistency":continue
                            score,skip=REGISTRY[name](output=g.text,reference=ex.reference_answer,prompt=ex.prompt,context=ex.context);db.add(MetricResult(response_id=response.id,metric_name=name,score=score,method="deterministic lexical adapter",skip_reason=skip))
                    except Exception as exc:run.error_count+=1;db.add(ModelResponse(run_id=run.id,example_id=ex.id,model=model,repetition=rep,error=str(exc)))
                    run.completed_cases+=1;db.commit()
        if "consistency" in exp.metrics:
            for responses in grouped.values():
                anchor=responses[0];scores=[token_f1(r.output,anchor.output)[0] for r in responses[1:]] or [1.]
                db.add(MetricResult(response_id=anchor.id,metric_name="consistency",score=sum(scores)/len(scores),method="pairwise token F1 against first generation",reasoning="Similarity measures stability, not factual correctness."))
        run.status=RunStatus.partially_failed if run.error_count else RunStatus.completed;run.completed_at=datetime.now(timezone.utc);db.commit()
    except Exception:
        if run:run.status=RunStatus.failed;run.completed_at=datetime.now(timezone.utc);db.commit()
        raise
    finally:db.close()

