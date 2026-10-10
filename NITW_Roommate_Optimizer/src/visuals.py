"""Native Python visualizations for the Streamlit application."""
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from src.data.data_cleaner import NUMERIC

CYAN='#64DFD3'
AMBER='#F2AF68'
BLUE='#78A6E8'
MUTED='#7D98AA'
BG='#07131E'
PALETTE=[CYAN,AMBER,BLUE,'#D89CC1']

def style(fig,height=410):
    fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(family='Arial',color='#C7D9E6',size=12),height=height,
                      margin=dict(l=15,r=15,t=35,b=20),colorway=PALETTE,
                      legend=dict(orientation='h',y=-.12),hoverlabel=dict(bgcolor='#163044'))
    fig.update_xaxes(gridcolor='#183042',zerolinecolor='#183042')
    fig.update_yaxes(gridcolor='#183042',zerolinecolor='#183042')
    return fig

def network_chart(df,result,show_candidates=False):
    graph=nx.Graph();graph.add_nodes_from(range(len(df)))
    for a,b,w in result['graph']['edges']:graph.add_edge(a,b,weight=max(.01,w))
    pos=nx.spring_layout(graph,seed=42,iterations=60,weight='weight')
    fig=go.Figure()
    if show_candidates:
        ex,ey=[],[]
        for a,b,_ in result['graph']['edges'][:3500]:
            ex += [pos[a][0],pos[b][0],None];ey += [pos[a][1],pos[b][1],None]
        fig.add_trace(go.Scatter(x=ex,y=ey,mode='lines',line=dict(width=.4,color='#254555'),hoverinfo='skip',name='Eligible edges'))
    for label,color,condition in [('Higher score',CYAN,lambda x:x>=result['metrics']['mean']),('Lower score',AMBER,lambda x:x<result['metrics']['mean'])]:
        ex,ey=[],[]
        for a,b in result['pairs']:
            if condition(result['graph']['score'][a,b]):
                ex += [pos[a][0],pos[b][0],None];ey += [pos[a][1],pos[b][1],None]
        fig.add_trace(go.Scatter(x=ex,y=ey,mode='lines',line=dict(width=2,color=color),hoverinfo='skip',name=label))
    paired={i for p in result['pairs'] for i in p}
    hover=[]
    for i in range(len(df)):
        partner=next((b if a==i else a for a,b in result['pairs'] if i in (a,b)),None)
        hover.append(f'{df.iloc[i].participant_id}<br>'+('Awaiting pairing' if partner is None else f'Partner: {df.iloc[partner].participant_id}<br>Score: {result["graph"]["score"][i,partner]:.3f}'))
    fig.add_trace(go.Scatter(x=[pos[i][0] for i in range(len(df))],y=[pos[i][1] for i in range(len(df))],
        mode='markers',marker=dict(size=10,color=[CYAN if i in paired else AMBER for i in range(len(df))],line=dict(width=1,color=BG)),
        text=hover,hovertemplate='%{text}<extra></extra>',name='Participants'))
    style(fig,430);fig.update_xaxes(visible=False);fig.update_yaxes(visible=False,scaleanchor='x',scaleratio=1)
    return fig

def heatmap(df,result,kind='Adjusted score'):
    key={'Adjusted score':'score','Compatibility':'cs','Conflict':'cf'}[kind]
    z=result['graph'][key].copy();np.fill_diagonal(z,np.nan)
    fig=go.Figure(go.Heatmap(z=z,x=df.participant_id,y=df.participant_id,
        colorscale=[[0,'#102535'],[.5,'#346B87'],[1,CYAN]] if key!='cf' else [[0,'#102535'],[1,AMBER]],
        colorbar=dict(title=kind),hovertemplate='%{x} / %{y}<br>%{z:.3f}<extra></extra>'))
    style(fig,600);fig.update_layout(xaxis_title='Participant',yaxis_title='Participant')
    return fig

def radar(a,b):
    labels=['Cleanliness','Sleep','Social','Noise tolerance','Visitor frequency','Snoring','Snoring sensitivity']
    keys=['cleanliness','sleep_time','social','noise_tolerance','friends_freq','snore_freq','snore_sensitivity']
    fig=go.Figure()
    for row,color in [(a,CYAN),(b,AMBER)]:
        vals=[float(row[k])/10 for k in keys]
        fig.add_trace(go.Scatterpolar(r=vals+[vals[0]],theta=labels+[labels[0]],fill='toself',name=row.participant_id,line_color=color,opacity=.8))
    style(fig,350);fig.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)',radialaxis=dict(range=[0,1],gridcolor='#294154'),angularaxis=dict(gridcolor='#294154')))
    return fig

def distribution(result):
    series=[]
    for label,pairs in [('Heap greedy',result['greedy_pairs']),('CASPER',result['pairs'])]:
        series.extend({'Algorithm':label,'Adjusted score':result['graph']['score'][a,b]} for a,b in pairs)
    if not series:return style(go.Figure(),300)
    return style(px.histogram(series,x='Adjusted score',color='Algorithm',barmode='overlay',opacity=.7,nbins=18,color_discrete_sequence=[AMBER,CYAN]),320)

def survey_plot(df):
    records=[{'Feature':key.replace('_',' ').title(),'Response':value} for key in NUMERIC for value in df[key]]
    fig=px.box(records,x='Response',y='Feature',orientation='h',color_discrete_sequence=[CYAN],points=False)
    style(fig,460);fig.update_xaxes(range=[-.2,10.2],title='Original survey scale · 0–10');return fig

def static_heatmap(df,result):
    fig,ax=plt.subplots(figsize=(10,8),facecolor=BG)
    ax.set_facecolor(BG)
    sns.heatmap(result['graph']['score'],cmap=sns.blend_palette(['#102535','#346B87',CYAN],as_cmap=True),ax=ax,
                xticklabels=False,yticklabels=False,cbar_kws={'label':'Adjusted score'})
    ax.set(title='CASPER · Pairwise score matrix',xlabel='Participant index',ylabel='Participant index')
    ax.tick_params(colors='#C7D9E6');ax.title.set_color('#C7D9E6');ax.xaxis.label.set_color('#C7D9E6');ax.yaxis.label.set_color('#C7D9E6')
    fig.axes[-1].tick_params(colors='#C7D9E6');fig.axes[-1].yaxis.label.set_color('#C7D9E6')
    fig.tight_layout();return fig
