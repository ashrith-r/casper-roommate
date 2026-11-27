"""Interactive playback of measured matching states."""
from colorsys import hsv_to_rgb
from math import ceil, sqrt
from time import monotonic

import networkx as nx
import pygame as pg

from experiments.benchmark import run_full_benchmark
from src.graph.graph_builder import build_graph

BG = '#1a1a2e'
PANEL = '#252540'
TEXT = '#f2f4ff'
QUIET = '#b7bbd2'
GREEN = '#68e5bb'
YELLOW = '#ffdb70'
RED = '#ff747a'
BUTTONS = ('Run', 'Step', 'Reset', 'New data', 'Compare', 'Switch start', 'Why coverage?')
SHORT = ('Random', 'Greedy', 'Blossom', 'One pattern', 'Both patterns')
PALETTE = [tuple(int(255 * x) for x in hsv_to_rgb(i * .618034 % 1, .58, .94)) for i in range(60)]


class Replay:
    def __init__(self, report, start='v2'):
        self.start = start
        initial = list(report['pairs']['blossom' if start == 'v2' else 'greedy'])
        self.states = [('Random draw', list(report['pairs']['random'])),
                       ('Exact Blossom' if start == 'v2' else 'Greedy start', initial)]
        for action in report['traces'][start]['log']:
            updated = self.states[-1][1].copy()
            for slot, pair in zip(action['slots'], action['after']):
                updated[slot] = tuple(pair)
            self.states.append((f"Swap {action['iteration']}  /  pattern {action['pattern']}", updated))
        self.index = 0

    def advance(self):
        if self.index + 1 == len(self.states):
            return False
        self.index += 1
        return True


def positions(n, pairs, order):
    """Give each room a slot and each unmatched participant a separate slot."""
    paired = {node for pair in pairs for node in pair}
    groups = [tuple(sorted(p, key=order.get)) for p in pairs] + [(i,) for i in range(n) if i not in paired]
    groups.sort(key=lambda p: min(order[i] for i in p))
    columns = max(1, ceil(sqrt(len(groups) * 1.95)))
    rows = max(1, ceil(len(groups) / columns))
    width, height = 864 / columns, 420 / rows
    coords, colors = {}, {}
    for idx, group in enumerate(groups):
        x = 55 + (idx % columns + .5) * width
        y = 110 + (idx // columns + .5) * height
        for side, node in enumerate(group):
            offset = (2 * side - 1) * min(17, width / 4) if len(group) == 2 else 0
            coords[node] = pg.Vector2(x + offset, y)
            colors[node] = PALETTE[idx % 60] if len(group) == 2 else '#8b91a8'
    return coords, colors


class Studio:
    def __init__(self, screen, data, settings, graph, report):
        self.screen = screen
        self.full_data = data
        self.settings = settings
        self.seed = report['seed']
        self.trials = report['trials']
        self.fonts = {size: pg.font.SysFont('monospace', size) for size in (12, 15, 18, 24, 32)}
        self.buttons = {name: pg.Rect(32 + i * 171, 840, 154, 40) for i, name in enumerate(BUTTONS)}
        self.compare = False
        self.install(graph, report)

    def install(self, graph, report):
        self.graph, self.report = graph, report
        layout_graph = nx.Graph()
        layout_graph.add_nodes_from(range(report['nodes']))
        layout_graph.add_edges_from(report['pairs']['random'])
        layout = nx.spring_layout(layout_graph, seed=self.seed % (2**32), iterations=14)
        self.order = {n: i for i, n in enumerate(sorted(layout, key=lambda n: tuple(layout[n])))}
        self.reset('v2')

    def reset(self, start):
        self.replay = Replay(self.report, start)
        self.running = False
        self.witness = -1
        self.changed = monotonic() - 1
        self.previous = self.replay.states[0][1]
        self.coords, self.colors = positions(self.report['nodes'], self.previous, self.order)
        self.old_coords = self.coords
        self.old_total = self.total(self.previous)

    def total(self, pairs):
        return sum(self.graph['score'][a, b] for a, b in pairs)

    def advance(self, now):
        previous = self.replay.states[self.replay.index][1]
        if not self.replay.advance():
            self.running = False
            return
        self.changed = now
        self.previous = previous
        self.old_total = self.total(previous)
        self.old_coords = self.coords
        self.coords, self.colors = positions(self.report['nodes'], self.replay.states[self.replay.index][1], self.order)

    def action(self, name, now):
        if name == 'Why coverage?':
            paths = self.report['coverage_paths']
            self.witness = (self.witness + 2) % (len(paths) + 1) - 1
            self.running = False
            return
        self.witness = -1
        if name == 'Reset':
            self.reset(self.replay.start)
            self.compare = False
        elif name == 'Switch start':
            self.reset('greedy' if self.replay.start == 'v2' else 'v2')
        elif name == 'Compare':
            self.compare = not self.compare
        elif name == 'New data':
            self.seed += 1
            size = min(len(self.full_data), 32)
            sample = self.full_data.sample(size, random_state=self.seed % (2**32)).reset_index(drop=True)
            graph = build_graph(sample, self.settings)
            self.install(graph, run_full_benchmark(graph, seed=self.seed, trials=self.trials))
        elif name == 'Step':
            self.running = False
            self.advance(now)
        elif name == 'Run':
            if self.replay.index == len(self.replay.states) - 1:
                self.reset(self.replay.start)
            self.running = not self.running
            self.deadline = now + (2 if self.replay.index <= 1 else .65)

    def label(self, x, y, value, size=18, color=TEXT):
        self.screen.blit(self.fonts[size].render(str(value), True, color), (x, y))

    def draw(self, now):
        if self.running and now >= self.deadline:
            self.advance(now)
            self.deadline = now + (2 if self.replay.index == 1 else .7)
        stage, pairs = self.replay.states[self.replay.index]
        t = min(1, max(0, (now - self.changed) / .30))
        self.screen.fill(BG)
        for rect in [(28, 80, 920, 482), (966, 80, 405, 482), (28, 580, 920, 236), (966, 580, 405, 236)]:
            pg.draw.rect(self.screen, PANEL, rect, border_radius=12)
        self.label(32, 21, 'CASPER  /  Roommate allocation', 32)
        self.label(970, 35, f"{self.report['nodes']} responses  ·  {self.report['eligible']} eligible edges", 15, QUIET)
        self.label(47, 89, stage, 18)
        xy = {n: self.old_coords[n].lerp(pos, t) for n, pos in self.coords.items()}
        old = {tuple(sorted(p)) for p in self.previous}
        new = {tuple(sorted(p)) for p in pairs}
        shared = old & new
        for a, b in old | new:
            score = self.graph['score'][a, b]
            alpha = 1 if (a, b) in shared else (t if (a, b) in new else 1-t)
            strength = min(1, .35 + .65 * abs(score)) * alpha
            color = pg.Color(PANEL).lerp(pg.Color(GREEN if score >= 0 else RED), strength)
            pg.draw.line(self.screen, color, xy[a], xy[b], max(1, round(1 + 2 * abs(score))))
        active = {n for pair in old ^ new for n in pair} if t < 1 else set()
        for n, pos in xy.items():
            pg.draw.circle(self.screen, self.colors[n], pos, 8)
            if n in active:
                pg.draw.circle(self.screen, YELLOW, pos, 12, 2)
            self.label(pos.x - 6, pos.y + 9, n + 1, 12, QUIET)

        total = self.old_total + t * (self.total(pairs) - self.old_total)
        self.label(989, 101, 'Allocation', 24)
        self.label(989, 155, f'{total:.3f}', 32, GREEN)
        self.label(989, 197, 'total adjusted score', 15, QUIET)
        for i, line in enumerate([f'{len(pairs)} pairs  /  {self.report["nodes"] - 2*len(pairs)} unpaired',
                                  f'{sum(self.graph["score"][a,b] < 0 for a,b in pairs)} negative-score pairs',
                                  f'{max(0, self.replay.index-1)} accepted swaps',
                                  f'{self.report["methods"][self.replay.start]["seconds"]*1000:.2f} ms · solver run']):
            self.label(989, 245 + 33*i, line)
        self.label(989, 400, 'Final exact total vs baseline', 15, QUIET)
        for i, key in enumerate(('random', 'greedy', 'blossom')):
            gain = self.report['methods'][key]['v2_gain_pct']
            change = 'n/a' if gain is None else f'{gain:+.1f}%'
            self.label(989, 429 + 28*i, f'{SHORT[i]:9}  {change}', 18)
        self.draw_charts()
        if self.witness >= 0:
            self.draw_witness()
        mouse = pg.mouse.get_pos()
        for name, rect in self.buttons.items():
            pg.draw.rect(self.screen, '#505574' if rect.collidepoint(mouse) else '#383c59', rect, border_radius=6)
            self.label(rect.x+12, rect.y+9, 'Pause' if name == 'Run' and self.running else name)
        self.label(1250, 851, 'Exact start' if self.replay.start == 'v2' else 'Greedy start', 15, QUIET)

    def draw_witness(self):
        path = self.report['coverage_paths'][self.witness]
        pg.draw.rect(self.screen, PANEL, (28, 80, 920, 482), border_radius=12)
        self.label(50, 102, 'Where does one extra room come from?', 24)
        count = len(self.report['coverage_paths'])
        self.label(50, 153, f'Path {self.witness+1} of {count}  ·  {len(path)} survey rows', 15, QUIET)
        self.label(50, 189, 'Follow the path. Alternate edges belong to different matchings.', 15)
        cols = min(len(path), max(8, ceil(sqrt(3 * len(path)))))
        rows = ceil(len(path) / cols)
        coords = []
        for i in range(len(path)):
            row, col = divmod(i, cols)
            if row % 2:
                col = cols - 1 - col
            coords.append((80 + round(col * 805 / max(1, cols-1)),
                           310 + round(row * 145 / max(1, rows-1))))
        for i, (a, b) in enumerate(zip(coords, coords[1:])):
            pg.draw.line(self.screen, GREEN if i % 2 == 0 else YELLOW, a, b, 4)
        for node, point in zip(path, coords):
            pg.draw.circle(self.screen, TEXT, point, 7)
            self.label(point[0]-10, point[1]+12, node+1, 12)
        self.label(50, 508, f'Greedy: {len(path)//2-1} rooms', 18, YELLOW)
        self.label(350, 508, f'Blossom: {len(path)//2} rooms', 18, GREEN)
        self.label(680, 510, 'Click again for next path', 15, QUIET)

    def draw_charts(self):
        self.label(48, 595, 'Score after each accepted swap', 18)
        history = self.report['traces'][self.replay.start]['history']
        if self.replay.index:
            values = history[:self.replay.index]
            lo, hi = min(history), max(history)
            for i, value in enumerate(values):
                point = (85 + int(795*i / max(1, len(history)-1)), 748 - int(81*(value-lo)/(hi-lo or 1)))
                if i:
                    pg.draw.line(self.screen, GREEN, previous, point, 3)
                pg.draw.circle(self.screen, GREEN, point, 5)
                previous = point
            self.label(48, 774, f'{values[0]:.3f} to {values[-1]:.3f}   ·   {len(values)-1} swaps', 15, QUIET)
        else:
            self.label(48, 700, 'Step to the starting allocation to see its score.', 15, QUIET)
        self.label(989, 595, 'Method comparison', 18)
        if not self.compare:
            self.label(989, 686, 'Select Compare to see the totals.', 15, QUIET)
            return
        totals = [v['total'] for v in self.report['methods'].values()]
        low, high = min(0, min(totals)), max(0, max(totals))
        def x(value):
            return 1118 + int(157 * (value - low) / (high - low or 1))
        for i, (name, value) in enumerate(zip(SHORT, totals)):
            y = 633 + 32*i
            self.label(989, y, name, 15)
            pg.draw.line(self.screen, GREEN if i == 4 else QUIET, (x(0), y+8), (x(value), y+8), 6)
            self.label(1285, y, f'{value:.2f}', 15)


def run_visualization(data, settings, graph, report):
    pg.init()
    try:
        screen = pg.display.set_mode((1400, 900), pg.SCALED | pg.RESIZABLE)
        pg.display.set_caption('CASPER v2: Conflict-Aware Roommate Optimization')
        studio = Studio(screen, data, settings, graph, report)
        clock = pg.time.Clock()
        while True:
            now = monotonic()
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    return
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    for name, rect in studio.buttons.items():
                        if rect.collidepoint(event.pos):
                            studio.action(name, now)
            studio.draw(now)
            pg.display.flip()
            clock.tick(60)
    finally:
        pg.quit()
