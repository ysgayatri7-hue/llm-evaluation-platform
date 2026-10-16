def classification_stats(predicted,actual):
    tp=sum(p==a==1 for p,a in zip(predicted,actual));tn=sum(p==a==0 for p,a in zip(predicted,actual));fp=sum(p==1 and a==0 for p,a in zip(predicted,actual));fn=sum(p==0 and a==1 for p,a in zip(predicted,actual));n=len(actual)
    precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0;f1=2*precision*recall/(precision+recall) if precision+recall else 0;observed=(tp+tn)/n if n else 0
    expected=(((tp+fp)/n)*((tp+fn)/n)+((tn+fn)/n)*((tn+fp)/n)) if n else 0;kappa=(observed-expected)/(1-expected) if n and expected!=1 else None
    return {"accuracy":observed,"precision":precision,"recall":recall,"f1":f1,"cohen_kappa":kappa,"confusion_matrix":[[tn,fp],[fn,tp]],"sample_size":n}

