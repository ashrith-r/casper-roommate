"""Run the reproducible benchmark and optionally replay the allocation on a desktop."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'NITW_Roommate_Optimizer'))

from experiments.benchmark import print_benchmark_table, run_full_benchmark
from experiments.charts import generate_charts
from src.data.data_cleaner import PUBLIC_PATH, load_data
from src.graph.graph_builder import Settings, build_graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=PUBLIC_PATH)
    parser.add_argument('--out', type=Path, default=Path('results'))
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--trials', type=int, default=200)
    parser.add_argument('--threshold', type=float, default=.4)
    parser.add_argument('--penalty', type=float, default=.5)
    parser.add_argument('--visualize', action='store_true')
    args = parser.parse_args()
    settings = Settings(lambda_=args.penalty, threshold=args.threshold)
    settings.validate()
    data, audit = load_data(args.data)
    graph = build_graph(data, settings)
    report = run_full_benchmark(graph, seed=args.seed, trials=args.trials)
    report.update(dataset_sha256=audit.source_sha256, threshold=settings.threshold,
                  penalty=settings.lambda_, alpha=settings.alpha)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'benchmark.json').write_text(json.dumps(report, allow_nan=False, indent=2), encoding='utf-8')
    print_benchmark_table(report)
    generate_charts(report, args.out)
    print(f'Wrote the report and five figures to {args.out.resolve()}')
    if args.visualize:
        from src.visualization.graph_viz import run_visualization
        run_visualization(data, settings, graph, report)


if __name__ == '__main__':
    main()
