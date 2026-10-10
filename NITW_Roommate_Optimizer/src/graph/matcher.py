"""Compile and invoke the C++ engine; keep NetworkX as an exact comparator."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import uuid
from time import perf_counter
import networkx as nx

PROJECT = Path(__file__).resolve().parents[2]

def ensure_engine():
    source = PROJECT / 'cpp' / 'casper.cpp'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:14]
    build = Path(os.environ.get('CASPER_BUILD_DIR', str(PROJECT / 'build')))
    build.mkdir(parents=True, exist_ok=True)
    binary = build / ('casper-' + digest + ('.exe' if os.name == 'nt' else ''))
    if binary.exists():
        return binary
    compiler = os.environ.get('CXX') or shutil.which('g++') or shutil.which('clang++')
    if not compiler:
        raise RuntimeError('A C++17 compiler is required. Install g++ or set CXX to your compiler path. Community Cloud installs it from packages.txt.')
    command = [compiler]
    if Path(compiler).stem.lower() == 'zig':
        command.append('c++')
    # Compile once per source revision. No commands or source arrive from users.
    temp = binary.with_name(binary.stem + '-' + uuid.uuid4().hex[:10] + binary.suffix)
    command += ['-std=c++17','-O2',str(source),'-o',str(temp)]
    completed = subprocess.run(command,capture_output=True,text=True,timeout=240)
    if completed.returncode:
        raise RuntimeError('C++ compilation failed: ' + completed.stderr[-2000:])
    os.replace(temp,binary)
    return binary

def casper_matching(n, edges, max_sweeps=12, fairness=True):
    binary = ensure_engine()
    lines = [f'{n} {len(edges)} {max_sweeps} {int(fairness)}']
    lines += [f'{i} {j} {float(w):.17g}' for i,j,w in edges]
    start = perf_counter()
    completed = subprocess.run([str(binary)], input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=60)
    if completed.returncode:
        raise RuntimeError('Matching engine rejected input: ' + completed.stderr[:300])
    result = json.loads(completed.stdout)
    result['process_ms'] = (perf_counter()-start)*1000
    return result

def max_weight_matching(edges, n=None):
    graph = nx.Graph()
    if n is not None: graph.add_nodes_from(range(n))
    graph.add_weighted_edges_from(edges)
    return sorted(tuple(sorted(p)) for p in nx.max_weight_matching(graph,maxcardinality=True))
