"""Run the real survey through CASPER from the command line."""
import argparse
import json
from pathlib import Path
from src.data.data_cleaner import load_data, PUBLIC_PATH
from src.graph.graph_builder import Settings
from src.pipeline import run_pipeline, export_results

def main():
    parser=argparse.ArgumentParser(description='CASPER optimized pairing')
    parser.add_argument('--data',type=Path,default=PUBLIC_PATH)
    parser.add_argument('--lambda',dest='lambda_',type=float,default=.5)
    parser.add_argument('--threshold',type=float,default=.4)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    df,audit=load_data(args.data)
    result=run_pipeline(df,Settings(lambda_=args.lambda_,threshold=args.threshold))
    print(result['table'].to_string(index=False))
    print(json.dumps({'records':audit.rows,**result['metrics'],'timing':result['timing']},indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_bytes(export_results(result,df))

if __name__=='__main__':main()
