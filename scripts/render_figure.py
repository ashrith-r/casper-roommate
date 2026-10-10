"""Render a shareable analytical figure directly from the real matching output."""
from pathlib import Path
import sys
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'NITW_Roommate_Optimizer'))
from src.data.data_cleaner import load_data,PUBLIC_PATH
from src.pipeline import run_pipeline

def main():
    df,_=load_data(PUBLIC_PATH);r=run_pipeline(df);m=r['metrics']
    bg='#07131e';fg='#e5eff4';muted='#91a9bb';cyan='#64dfd3';amber='#f2af68'
    plt.rcParams.update({'font.family':'DejaVu Sans','text.color':fg,'axes.labelcolor':muted,
                         'xtick.color':muted,'ytick.color':muted,'axes.edgecolor':'#294154'})
    fig=plt.figure(figsize=(16,9),facecolor=bg)
    fig.text(.055,.935,'CASPER',fontsize=32,fontweight='bold')
    fig.text(.24,.945,'CONSTRAINT-AWARE ROOMMATE PAIRING',fontsize=12,color=cyan)
    fig.text(.24,.915,'Real survey measurements  /  C++ matching  /  Python analytics',fontsize=11,color=muted)
    stats=[('RESPONSES',str(len(df))),('SELECTED PAIRS',str(m['pairs'])),('ELIGIBLE EDGES',f'{r["graph"]["eligible"]:,}'),('MEAN SCORE',f'{m["mean"]:.3f}')]
    for i,(label,value) in enumerate(stats):
        x=.055+i*.24
        fig.text(x,.825,value,fontsize=30,color=fg)
        fig.text(x,.787,label,fontsize=10,color=muted)
    ax=fig.add_axes([.045,.12,.46,.59],facecolor=bg)
    ax.set_title('01   THE SELECTED NETWORK',loc='left',fontsize=11,color=cyan,pad=18)
    graph=nx.Graph();graph.add_nodes_from(range(len(df)))
    graph.add_weighted_edges_from(r['graph']['edges'])
    pos=nx.spring_layout(graph,seed=42,iterations=70)
    paired={v for pair in r['pairs'] for v in pair}
    nx.draw_networkx_edges(graph,pos,edgelist=r['pairs'],ax=ax,width=1.9,alpha=.7,edge_color=cyan)
    nx.draw_networkx_nodes(graph,pos,ax=ax,node_size=40,node_color=[cyan if i in paired else amber for i in graph],linewidths=.7,edgecolors=bg)
    ax.set_axis_off()
    fig.text(.055,.09,f'{m["unmatched"]} unmatched participants remain visible for review.',color=amber,fontsize=10)
    matrix=fig.add_axes([.575,.345,.355,.35],facecolor=bg)
    matrix.set_title('02   PAIRWISE SCORE MATRIX',loc='left',fontsize=11,color=cyan,pad=18)
    z=r['graph']['score'].copy();np.fill_diagonal(z,np.nan)
    matrix.imshow(z,cmap=LinearSegmentedColormap.from_list('casper',['#102535','#346b87',cyan]),aspect='auto')
    matrix.set_xticks([0,48,97],['P001','P049','P098']);matrix.set_yticks([0,48,97],['P001','P049','P098'])
    matrix.tick_params(length=0,labelsize=9)
    bars=fig.add_axes([.575,.135,.355,.13],facecolor=bg)
    bars.set_title('03   MATCHED PARTICIPANTS / SAME CONSTRAINTS',loc='left',fontsize=10,color=cyan,pad=14)
    bars.barh(['CASPER','Exact reference'],[m['pairs']*2,int(r['comparison'].iloc[-1]['pairs'])*2],color=[cyan,amber],height=.4)
    bars.set_xlim(0,105);bars.set_xticks([]);bars.tick_params(length=0,labelsize=10)
    for idx,count in enumerate([m['pairs']*2,int(r['comparison'].iloc[-1]['pairs'])*2]):bars.text(count+1,idx,str(count),va='center',fontsize=10)
    for spine in bars.spines.values():spine.set_visible(False)
    fig.text(.055,.035,'λ = 0.5   ·   Conflict threshold = 0.4   ·   Fairness enabled   ·   Model scores are not outcome probabilities',fontsize=9,color=muted)
    target=ROOT/'docs'/'analysis.png';target.parent.mkdir(exist_ok=True)
    fig.savefig(target,dpi=130,facecolor=bg);plt.close(fig)
    print(target.name)

if __name__=='__main__':main()
