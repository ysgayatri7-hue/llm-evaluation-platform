import enum
from datetime import datetime, timezone
from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

def now(): return datetime.now(timezone.utc)

class RunStatus(str, enum.Enum):
    queued="queued"; running="running"; completed="completed"; partially_failed="partially_failed"; failed="failed"; cancelled="cancelled"

class Dataset(Base):
    __tablename__="datasets"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(200),unique=True)
    description: Mapped[str]=mapped_column(Text,default="")
    is_synthetic: Mapped[bool]=mapped_column(Boolean,default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    versions: Mapped[list["DatasetVersion"]]=relationship(cascade="all, delete-orphan",back_populates="dataset")

class DatasetVersion(Base):
    __tablename__="dataset_versions"; __table_args__=(UniqueConstraint("dataset_id","version"),)
    id: Mapped[int]=mapped_column(primary_key=True)
    dataset_id: Mapped[int]=mapped_column(ForeignKey("datasets.id",ondelete="CASCADE"))
    version: Mapped[int]=mapped_column(default=1)
    validation_report: Mapped[dict]=mapped_column(JSON,default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    dataset: Mapped[Dataset]=relationship(back_populates="versions")
    examples: Mapped[list["DatasetExample"]]=relationship(cascade="all, delete-orphan")

class DatasetExample(Base):
    __tablename__="dataset_examples"; __table_args__=(UniqueConstraint("version_id","example_id"),)
    id: Mapped[int]=mapped_column(primary_key=True)
    version_id: Mapped[int]=mapped_column(ForeignKey("dataset_versions.id",ondelete="CASCADE"))
    example_id: Mapped[str]=mapped_column(String(120)); prompt: Mapped[str]=mapped_column(Text)
    reference_answer: Mapped[str|None]=mapped_column(Text,nullable=True); context: Mapped[str|None]=mapped_column(Text,nullable=True)
    task_type: Mapped[str]=mapped_column(String(80),default="qa")
    human_judgment: Mapped[dict|None]=mapped_column(JSON,nullable=True); expected_properties: Mapped[dict|None]=mapped_column(JSON,nullable=True)

class Experiment(Base):
    __tablename__="experiments"
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(200))
    dataset_version_id: Mapped[int]=mapped_column(ForeignKey("dataset_versions.id"))
    models: Mapped[list]=mapped_column(JSON); metrics: Mapped[list]=mapped_column(JSON)
    judge_model: Mapped[str|None]=mapped_column(String(200),nullable=True); repetitions: Mapped[int]=mapped_column(default=1)
    temperature: Mapped[float]=mapped_column(Float,default=0); prompt_template: Mapped[str]=mapped_column(Text,default="{prompt}")
    notes: Mapped[str]=mapped_column(Text,default=""); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class EvaluationRun(Base):
    __tablename__="evaluation_runs"
    id: Mapped[int]=mapped_column(primary_key=True); experiment_id: Mapped[int]=mapped_column(ForeignKey("experiments.id"))
    status: Mapped[RunStatus]=mapped_column(Enum(RunStatus),default=RunStatus.queued)
    total_cases: Mapped[int]=mapped_column(default=0); completed_cases: Mapped[int]=mapped_column(default=0); error_count: Mapped[int]=mapped_column(default=0)
    cancel_requested: Mapped[bool]=mapped_column(Boolean,default=False)
    started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); completed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class ModelResponse(Base):
    __tablename__="model_responses"
    id: Mapped[int]=mapped_column(primary_key=True); run_id: Mapped[int]=mapped_column(ForeignKey("evaluation_runs.id",ondelete="CASCADE")); example_id: Mapped[int]=mapped_column(ForeignKey("dataset_examples.id"))
    model: Mapped[str]=mapped_column(String(200)); repetition: Mapped[int]=mapped_column(default=1); output: Mapped[str]=mapped_column(Text,default="")
    latency_ms: Mapped[float|None]=mapped_column(Float,nullable=True); prompt_tokens: Mapped[int|None]=mapped_column(Integer,nullable=True); completion_tokens: Mapped[int|None]=mapped_column(Integer,nullable=True)
    estimated_cost_usd: Mapped[float|None]=mapped_column(Float,nullable=True); usage_is_estimated: Mapped[bool]=mapped_column(Boolean,default=True); error: Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class MetricResult(Base):
    __tablename__="metric_results"
    id: Mapped[int]=mapped_column(primary_key=True); response_id: Mapped[int]=mapped_column(ForeignKey("model_responses.id",ondelete="CASCADE"))
    metric_name: Mapped[str]=mapped_column(String(100)); metric_version: Mapped[str]=mapped_column(String(30),default="1.0"); score: Mapped[float|None]=mapped_column(Float,nullable=True)
    method: Mapped[str]=mapped_column(String(100)); scale: Mapped[str]=mapped_column(String(40),default="0-1"); reasoning: Mapped[str|None]=mapped_column(Text,nullable=True); skip_reason: Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class HumanAnnotation(Base):
    __tablename__="human_annotations"
    id: Mapped[int]=mapped_column(primary_key=True); response_id: Mapped[int]=mapped_column(ForeignKey("model_responses.id",ondelete="CASCADE")); reviewer: Mapped[str]=mapped_column(String(120))
    correctness: Mapped[int|None]=mapped_column(Integer,nullable=True); relevance: Mapped[int|None]=mapped_column(Integer,nullable=True); faithfulness: Mapped[int|None]=mapped_column(Integer,nullable=True); preferred_response_id: Mapped[int|None]=mapped_column(Integer,nullable=True)
    notes: Mapped[str]=mapped_column(Text,default=""); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class ReliabilityAnalysis(Base):
    __tablename__="reliability_analyses"
    id: Mapped[int]=mapped_column(primary_key=True); run_id: Mapped[int]=mapped_column(ForeignKey("evaluation_runs.id")); metric_name: Mapped[str]=mapped_column(String(100)); threshold: Mapped[float]=mapped_column(Float,default=.5)
    sample_size: Mapped[int]=mapped_column(default=0); statistics: Mapped[dict]=mapped_column(JSON); limitations: Mapped[list]=mapped_column(JSON); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

