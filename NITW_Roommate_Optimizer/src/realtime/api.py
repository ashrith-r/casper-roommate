"""Authenticated stateless endpoints; clients provide their current cohort."""
import hmac
import io
import os
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field
import pandas as pd
from src.data.data_cleaner import load_data
from src.graph.graph_builder import Settings
from src.pipeline import run_pipeline

app=FastAPI(title='CASPER',version='2.0.0',description='Constraint-aware score-based pairing')

def authorize(x_api_key: str | None=Header(default=None)):
    expected=os.environ.get('CASPER_API_KEY','')
    if not expected: raise HTTPException(503,'Set CASPER_API_KEY before enabling the API.')
    if not x_api_key or not hmac.compare_digest(expected,x_api_key): raise HTTPException(401,'Invalid API key.')

class Request(BaseModel):
    records: list[dict] = Field(min_length=2,max_length=1000)
    lambda_: float = Field(default=.5,ge=0,le=2)
    threshold: float = Field(default=.4,ge=0,le=1)
    max_sweeps: int = Field(default=12,ge=0,le=50)
    preserve_pairs: list[tuple[str,str]] = Field(default_factory=list,max_length=500)

@app.get('/health')
def health():return {'status':'ok','service':'CASPER'}

@app.post('/run_matching/',dependencies=[Depends(authorize)])
def run_matching(request: Request):
    try:
        payload=pd.DataFrame(request.records).to_csv(index=False).encode('utf-8')
        df,_=load_data(payload)
        result=run_pipeline(df,Settings(lambda_=request.lambda_,threshold=request.threshold,max_sweeps=request.max_sweeps),request.preserve_pairs,compare=False)
        return {'pairs':result['table'].to_dict(orient='records'),
                'unmatched':df.iloc[result['unmatched']].participant_id.tolist(),
                'metrics':result['metrics'],'settings':result['settings']}
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    except (RuntimeError,TimeoutError) as exc: raise HTTPException(503,'Matching engine unavailable. Check the server configuration.') from exc
