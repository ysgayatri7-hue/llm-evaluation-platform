export type Dataset={id:number;name:string;description:string;is_synthetic:boolean;versions:{id:number;version:number;example_count:number;validation_report:any}[]};
export type Run={id:number;experiment_id:number;status:string;total_cases:number;completed_cases:number;error_count:number;created_at:string};
export type Result={id:number;example_id:string;prompt:string;reference_answer?:string;context?:string;model:string;output:string;latency_ms:number;tokens:number;estimated_cost_usd:number;usage_is_estimated:boolean;metrics:Record<string,{score:number|null;skip_reason?:string;reasoning?:string}>};

