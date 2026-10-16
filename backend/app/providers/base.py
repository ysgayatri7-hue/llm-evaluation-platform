from dataclasses import dataclass

@dataclass
class Generation:
    text:str; latency_ms:float; prompt_tokens:int|None; completion_tokens:int|None; estimated_cost_usd:float|None; usage_is_estimated:bool

class Provider:
    def generate(self,model:str,prompt:str,reference:str|None,repetition:int)->Generation: raise NotImplementedError

