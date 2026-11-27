"""Static figures from the benchmark report."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from experiments.benchmark import COSTS

NAMES = ['Random', 'Greedy', 'Blossom', 'One pattern', 'Both patterns']
COLORS = ['#8797aa', '#ec9a55', '#516db0', '#509d97', '#123c45']


def generate_charts(report, directory):
    directory.mkdir(parents=True, exist_ok=True)
    rows = list(report['methods'].values())

    def save(fig, name):
        fig.savefig(directory / (name + '.png'), dpi=160, bbox_inches='tight')
        plt.close(fig)

    for field, name, title, unit in (
        ('total', 'score_comparison', 'How much compatibility did each method allocate?', 'Total adjusted score'),
        ('negative_pairs', 'conflict_comparison', 'How many selected pairs scored below zero?', 'Negative-score pairs'),
        ('seconds', 'complexity', 'What did one match computation cost?', 'Milliseconds per run'),
    ):
        fig, ax = plt.subplots(figsize=(9, 4.6), layout='constrained')
        values = [row[field] * (1000 if field == 'seconds' else 1) for row in rows]
        labels = NAMES if field != 'seconds' else [
            f'{name_}\n{COSTS[key]}' for name_, key in zip(NAMES, report['methods'])]
        bars = ax.bar(labels, values, color=COLORS)
        ax.bar_label(bars, fmt='%.2f', padding=4)
        ax.margins(y=.2)
        ax.set(title=title, ylabel=unit)
        ax.spines[['top', 'right']].set_visible(False)
        save(fig, name)

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), layout='constrained', sharey=True)
    for ax, key, title in zip(axes, ('greedy', 'v2'), ('Greedy start', 'Exact Blossom start')):
        history = report['traces'][key]['history']
        ax.plot(range(len(history)), history, 'o-', color=COLORS[-1])
        ax.set(title=f'{title} · {len(history)-1} swaps', xlabel='Accepted swap')
        if len(history) <= 10:
            ax.set_xticks(range(len(history)))
    axes[0].set_ylabel('Total adjusted score')
    save(fig, 'convergence')

    # Display normalized measurements; tied values receive equal rank on each axis.
    fields = [('coverage', 'Coverage', 1), ('mean', 'Mean score', 1), ('minimum', 'Weakest score', 1),
              ('conflict', 'Lower conflict', -1), ('variance', 'Lower variance', -1)]
    raw = np.array([[direction * row[k] for k, _, direction in fields] for row in rows])
    span = np.ptp(raw, axis=0)
    scaled = np.divide(raw - raw.min(axis=0), span, out=np.ones_like(raw), where=span > 1e-12)
    angles = np.linspace(0, 2 * np.pi, len(fields), endpoint=False).tolist()
    fig, ax = plt.subplots(figsize=(7, 5), subplot_kw={'projection': 'polar'}, layout='constrained')
    for name, color, values in zip(NAMES, COLORS, scaled):
        ax.plot(angles + angles[:1], [*values, values[0]], label=name, color=color, marker='.')
    ax.set_xticks(angles, [label for _, label, _ in fields])
    ax.set_ylim(0, 1)
    ax.set_title('Relative performance within this run', pad=24)
    ax.legend(loc='upper left', bbox_to_anchor=(1.18, 1))
    save(fig, 'radar')
