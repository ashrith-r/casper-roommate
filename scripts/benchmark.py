"""Reproduce comparison statistics using only the real public measurements."""
import json
from pathlib import Path
import sys
import platform
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'NITW_Roommate_Optimizer'))
from src.data.data_cleaner import load_data, PUBLIC_PATH
from src.pipeline import run_pipeline, lambda_analysis

def main():
    frame,audit=load_data(PUBLIC_PATH)
    result=run_pipeline(frame)
    sensitivity,recommendation=lambda_analysis(frame)
    output={'dataset_sha256':audit.source_sha256,'rows':len(frame),
            'host':{'system':platform.system(),'python':platform.python_version()},
            'settings':result['settings'],'eligible_edges':result['graph']['eligible'],
            'comparison':result['comparison'].to_dict(orient='records'),
            'refinement':{k:result['native'][k] for k in ['swaps','passes','converged','greedy_ms','refinement_ms','process_ms']},
            'timing_ms':result['timing'],'lambda_evaluation':sensitivity.to_dict(orient='records'),
            'policy_selected_lambda':recommendation,
            'note':'Single-host observations; timings are not universal speedup evidence. No pair-outcome labels exist.'}
    target=ROOT/'docs'/'benchmark.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(output,indent=2,allow_nan=False),encoding='utf-8')
    print(result['comparison'].to_string(index=False))
    print(f'Wrote {target.name}; policy-selected lambda: {recommendation}')

if __name__=='__main__':main()
