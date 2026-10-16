from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ExampleIn(BaseModel):
    example_id: str|None=None; prompt: str=Field(min_length=1); reference_answer: str|None=None; context: str|None=None
    task_type: str="qa"; human_judgment: dict|None=None; expected_properties: dict|None=None

class DatasetCreate(BaseModel):
    name: str=Field(min_length=2,max_length=200); description: str=""; is_synthetic: bool=False; examples: list[ExampleIn]=Field(min_length=1)

class ExperimentCreate(BaseModel):
    name: str=Field(min_length=2); dataset_version_id: int; models: list[str]=Field(min_length=1); metrics: list[str]=Field(min_length=1)
    judge_model: str|None=None; repetitions: int=Field(default=1,ge=1,le=10); temperature: float=Field(default=0,ge=0,le=2); prompt_template: str="{prompt}"; notes: str=""
    @field_validator("metrics")
    @classmethod
    def known_metrics(cls,value):
        allowed={"exact_match","token_f1","relevance","faithfulness","consistency"}; unknown=set(value)-allowed
        if unknown: raise ValueError(f"Unsupported metrics: {sorted(unknown)}")
        return value

class AnnotationCreate(BaseModel):
    response_id: int; reviewer: str=Field(min_length=1); correctness: int|None=Field(default=None,ge=0,le=1)
    relevance: int|None=Field(default=None,ge=1,le=5); faithfulness: int|None=Field(default=None,ge=1,le=5); preferred_response_id: int|None=None; notes: str=""

class AnalysisCreate(BaseModel):
    run_id: int; metric_name: str="exact_match"; threshold: float=Field(default=.5,ge=0,le=1)

class RunView(BaseModel):
    id:int; experiment_id:int; status:str; total_cases:int; completed_cases:int; error_count:int; created_at:datetime
    model_config={"from_attributes":True}

