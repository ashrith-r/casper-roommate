"""Shared orchestration for Streamlit, the CLI and FastAPI."""
from dataclasses import asdict, replace
from time import perf_counter
import numpy as np
import pandas as pd
from src.graph.graph_builder import Settings, build_graph
from src.graph.matcher import casper_matching, max_weight_matching
from src.optimization.fairness import metrics

def run_pipeline(df, settings=Settings(), locked_pairs=(), compare=True):
    started = perf_counter()
    graph = build_graph(df, settings)
    score_ms = (perf_counter()-started)*1000
    by_id = {pid:i for i,pid in enumerate(df.participant_id)}
    locked, taken = [], set()
    for ids in locked_pairs:
        if len(ids)!=2 or any(pid not in by_id for pid in ids):
            raise ValueError('A preserved pair contains an unknown participant.')
        a,b = (by_id[pid] for pid in ids)
        if a==b or a in taken or b in taken or not graph['allowed'][a,b]:
            raise ValueError('A preserved pair violates the current constraints. Restore the prior settings or choose full re-optimization.')
        locked.append([a,b]);taken.update([a,b])
    available = [e for e in graph['edges'] if e[0] not in taken and e[1] not in taken]
    native = casper_matching(len(df), available, settings.max_sweeps, settings.fairness)
    pairs = locked + native['pairs']
    baseline = locked + native['greedy_pairs']
    comparisons = [dict(algorithm='Heap greedy', **metrics(baseline,graph,len(df))),
                   dict(algorithm='CASPER', **metrics(pairs,graph,len(df)))]
    exact_ms = None
    if compare:
        exact_start=perf_counter()
        exact = locked + max_weight_matching(available,len(df))
        exact_ms=(perf_counter()-exact_start)*1000
        comparisons.append(dict(algorithm='Blossom reference',**metrics(exact,graph,len(df))))
    used={i for pair in pairs for i in pair}
    unmatched=[i for i in range(len(df)) if i not in used]
    pair_rows=[]
    for k,(a,b) in enumerate(sorted(pairs,key=lambda p:graph['score'][p[0],p[1]],reverse=True),1):
        pair_rows.append({'Pair':f'M{k:03d}','Participant A':df.iloc[a].participant_id,
                          'Participant B':df.iloc[b].participant_id,'Cohort':df.iloc[a].gender,
                          'Compatibility':float(graph['cs'][a,b]),'Conflict':float(graph['cf'][a,b]),
                          'Penalty':float(settings.lambda_*graph['cf'][a,b]**2),
                          'Adjusted score':float(graph['score'][a,b]),'Preserved':a in taken})
    table=pd.DataFrame(pair_rows,columns=['Pair','Participant A','Participant B','Cohort','Compatibility','Conflict','Penalty','Adjusted score','Preserved'])
    return {'pairs':pairs,'greedy_pairs':baseline,'unmatched':unmatched,'graph':graph,
            'table':table,'metrics':metrics(pairs,graph,len(df)),
            'comparison':pd.DataFrame(comparisons),'native':native,'settings':asdict(settings),
            'timing':{'scoring_ms':score_ms,'exact_ms':exact_ms,'pipeline_ms':(perf_counter()-started)*1000},
            'preserved_count':len(locked)}

def lambda_analysis(df, settings=Settings()):
    rows=[]
    for value in [0,.25,.5,.75,1,1.25,1.5,1.75,2]:
        result=run_pipeline(df,replace(settings,lambda_=value),compare=False)
        rows.append({'lambda':value,**result['metrics']})
    table=pd.DataFrame(rows)
    # Compare common, unpenalized quantities, not adjusted scores on different scales.
    order=table.sort_values(['pairs','conflict','compatibility','lambda'],ascending=[False,True,False,True],kind='stable')
    recommendation=float(order.iloc[0]['lambda'])
    return table,recommendation

def export_results(result, df):
    table=result['table'].copy()
    table.insert(0,'Status','Paired')
    for i in result['unmatched']:
        row={c:'' for c in table.columns}
        row.update({'Status':'Unmatched','Participant A':df.iloc[i].participant_id,'Cohort':df.iloc[i].gender})
        table=pd.concat([table,pd.DataFrame([row])],ignore_index=True)
    # IDs are constrained, but keep exports safe if columns are expanded later.
    for col in table.select_dtypes(include=['object','str']).columns:
        table[col]=table[col].map(lambda x: "'"+x if isinstance(x,str) and x.lstrip().startswith(('=','+','-','@')) else x)
    return table.to_csv(index=False).encode('utf-8')
