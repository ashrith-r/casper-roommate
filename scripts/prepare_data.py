"""Produce the public feature dataset from the actual supplied survey."""
import argparse
from pathlib import Path
import sys
import json
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'NITW_Roommate_Optimizer'))
from src.data.data_cleaner import load_data, public_measurements, PUBLIC_PATH

def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path,help='Private original raw survey CSV')
    args=p.parse_args()
    frame,audit=load_data(args.source)
    public=public_measurements(frame)
    PUBLIC_PATH.parent.mkdir(parents=True,exist_ok=True)
    public.to_csv(PUBLIC_PATH,index=False)
    manifest={**asdict(audit),'identified':False,'source':'Original raw survey supplied with the project archive',
              'transformation':f'Direct identifiers removed; all {len(frame)} supplied response rows retained; numeric features use original values divided by 10 during processing.',
              'removed_fields':['name','email','submission ID','respondent ID','timestamp','branch'],
              'notes':'Pseudonymous data derived from real responses. Repeated respondent identifiers require administrative review; they were not automatically merged.'}
    (PUBLIC_PATH.parents[1]/'provenance.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Prepared {len(frame)} real response records without direct identifiers.')

if __name__=='__main__':main()
