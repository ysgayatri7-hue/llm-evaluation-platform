import re
from collections import Counter

def normalize(text): return " ".join(re.findall(r"[a-z0-9]+",text.lower()))
def exact_match(output,reference=None,**_): return (None,"Reference answer required") if not reference else (float(normalize(output)==normalize(reference)),None)
def token_f1(output,reference=None,**_):
    if not reference:return None,"Reference answer required"
    a,b=Counter(normalize(output).split()),Counter(normalize(reference).split()); overlap=sum((a&b).values())
    if not a or not b:return float(a==b),None
    p,r=overlap/sum(a.values()),overlap/sum(b.values()); return (2*p*r/(p+r) if p+r else 0),None
def relevance(output,prompt="",**_):
    a,b=set(normalize(output).split()),set(normalize(prompt).split()); return min(1.,len(a&b)/max(1,min(5,len(b)))),None
def faithfulness(output,context=None,**_):
    if not context:return None,"Supporting context required"
    a,b=set(normalize(output).split()),set(normalize(context).split()); return len(a&b)/max(1,len(a)),None
REGISTRY={"exact_match":exact_match,"token_f1":token_f1,"relevance":relevance,"faithfulness":faithfulness}

