import hashlib,time
from app.providers.base import Generation,Provider

class MockProvider(Provider):
    """Deterministic offline provider. Synthetic outputs are not real benchmark evidence."""
    def generate(self,model,prompt,reference,repetition):
        start=time.perf_counter(); digest=int(hashlib.sha256(f"{model}|{prompt}|{repetition}".encode()).hexdigest()[:8],16)
        text=reference if reference and digest%5 else (f"A plausible but intentionally imperfect answer about {prompt[:50]}." if reference else f"Mock response {digest%997}: {prompt[:120]}")
        latency=(time.perf_counter()-start)*1000+8+digest%35; pt=max(1,len(prompt.split())); ct=max(1,len(text.split()))
        return Generation(text,round(latency,2),pt,ct,round(pt*.00000015+ct*.0000006,8),True)

