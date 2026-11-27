import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'NITW_Roommate_Optimizer'))

import pygame as pg
from experiments.benchmark import run_full_benchmark, percentage
from src.data.data_cleaner import PUBLIC_PATH, load_data
from src.graph.graph_builder import build_graph, build_score_dict, Settings
from src.graph.optimizer import improve_matching_tracked
from src.graph.fallback import optimized_fallback
from src.visualization.graph_viz import Studio


class DesktopTests(unittest.TestCase):
    def test_both_swap_patterns_and_replay(self):
        for extra, pattern in [([(0, 2, 6), (1, 3, 6)], 1), ([(0, 3, 6), (1, 2, 6)], 2)]:
            initial = [(0, 1), (2, 3)]
            scores = build_score_dict([(0, 1, 10), (2, 3, 1), *extra])
            pairs, history, log = improve_matching_tracked(initial, scores)
            self.assertEqual(history, [11, 12])
            self.assertEqual(log[0]['pattern'], pattern)
            self.assertEqual(list(log[0]['before']), initial)
            self.assertEqual(list(log[0]['after']), pairs)

    def test_missing_edges_and_negative_edges_are_distinct(self):
        scores = build_score_dict([(0, 1, -1), (2, 3, -2)])
        self.assertEqual(optimized_fallback(range(5), scores), ([(0, 1), (2, 3)], [4]))
        self.assertEqual(improve_matching_tracked([(0, 1), (2, 3)], scores)[1:], ([-3], []))
        self.assertIsNone(percentage(0, 0))
        self.assertEqual(percentage(-1, -2), 50)

    def test_cli_reproduces_public_reference_and_writes_five_pngs(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = subprocess.run([sys.executable, str(ROOT/'main.py'), '--out', tmp],
                                 check=True, capture_output=True, text=True)
            print(run.stdout)
            out = Path(tmp)
            report = json.loads((out/'benchmark.json').read_text())
            self.assertEqual({p.stem for p in out.glob('*.png')},
                             {'score_comparison', 'conflict_comparison', 'complexity', 'convergence', 'radar'})
            for p in out.glob('*.png'):
                self.assertTrue(p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertEqual(len(report['coverage_paths']), 9)
            vertices = [n for path in report['coverage_paths'] for n in path]
            self.assertEqual(len(set(vertices)), len(vertices))
            self.assertEqual(report['eligible'], 1520)
            self.assertEqual(report['methods']['v2']['pairs'], 49)
            self.assertEqual(report['traces']['v2']['log'], [])
            self.assertAlmostEqual(report['methods']['v2']['total'], 31.641743388184686)
            self.assertGreater(len(report['traces']['greedy']['log']), 0)

    def test_replay_controls_and_feasibility(self):
        frame, _ = load_data(PUBLIC_PATH)
        graph = build_graph(frame)
        report = run_full_benchmark(graph, seed=7, trials=3)
        again = run_full_benchmark(graph, seed=7, trials=3)
        self.assertEqual(report['pairs']['random'], again['pairs']['random'])
        self.assertEqual(report['methods']['random']['total'], again['methods']['random']['total'])
        pg.init()
        try:
            pg.display.set_mode((1, 1))
            studio = Studio(pg.Surface((1400, 900)), frame, Settings(), graph, report)
            for mode in ('v2', 'greedy'):
                studio.reset(mode)
                for _, pairs in studio.replay.states:
                    vertices = [v for p in pairs for v in p]
                    self.assertEqual(len(vertices), len(set(vertices)))
                    self.assertTrue(all(graph['allowed'][a,b] for a,b in pairs))
                studio.action('Compare', 0)
                studio.action('Run', 0)
                studio.draw(2.1)
                self.assertEqual(studio.replay.index, 1)
                for t in range(2, len(studio.replay.states)):
                    studio.action('Step', t)
                    studio.draw(t + .15)
            studio.action('Why coverage?', 5)
            studio.draw(5)
            studio.action('Reset', 5)
            self.assertEqual(studio.replay.index, 0)
            studio.action('Switch start', 5)
            studio.action('New data', 6)
            self.assertEqual(studio.report['nodes'], 32)
            studio.draw(7)
        finally:
            pg.quit()
