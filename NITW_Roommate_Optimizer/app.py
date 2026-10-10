"""CASPER: Streamlit presentation over the C++/Python matching pipeline."""
from pathlib import Path
from dataclasses import asdict, replace
import hmac
import io
import json
import os
import sys
import hashlib
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt

PROJECT=Path(__file__).resolve().parent
if str(PROJECT) not in sys.path:sys.path.insert(0,str(PROJECT))
from src.data.data_cleaner import load_data, public_measurements, PUBLIC_PATH, NUMERIC, HOBBIES
from src.data.feature_engine import conflict_components
from src.graph.graph_builder import Settings
from src.graph.matcher import ensure_engine
from src.pipeline import run_pipeline, lambda_analysis, export_results
from src import visuals
from src.utils.email_sender import compose, send_email, email_ready

st.set_page_config(page_title='CASPER | Optimized Pairing',page_icon=':material/hub:',layout='wide')

def secret(key,default=''):
    value=os.environ.get(key)
    if value is not None:return value
    try:return str(st.secrets.get(key,default))
    except (FileNotFoundError,st.errors.StreamlitSecretNotFoundError):return default

@st.cache_resource(show_spinner=False)
def engine():return ensure_engine()

def fingerprint(df):
    return hashlib.sha256(public_measurements(df).to_csv(index=False).encode()).hexdigest()

def run(settings,preserve=()):
    with st.spinner('Computing scores, pruning edges and running the C++ engine…'):
        engine()
        result=run_pipeline(st.session_state.df,settings,preserve)
    st.session_state.result=result
    st.session_state.run_fingerprint=fingerprint(st.session_state.df)
    st.session_state.run_settings=asdict(settings)

if 'df' not in st.session_state:
    try:
        st.session_state.df,st.session_state.audit=load_data(PUBLIC_PATH)
    except (OSError,ValueError) as exc:
        st.error(f'The verified survey dataset is unavailable: {exc}');st.stop()
    st.session_state.result=None
    st.session_state.pending=[]

df=st.session_state.df
with st.sidebar:
    st.title('CASPER')
    st.caption('OPTIMIZED PAIRING ALGORITHM')
    page=st.radio('Workspace',['Overview','Pair explorer','Graph laboratory','Benchmarks','Survey evidence','Online matching','Delivery'],label_visibility='collapsed')
    st.divider()
    st.caption('SCORING CONTROLS')
    lambda_=st.slider('Conflict penalty · λ',0.0,2.0,.5,.05)
    threshold=st.slider('Conflict threshold',0.0,1.0,.4,.025)
    fairness=st.toggle('Protect weakest pairs & variance',True)
    settings=Settings(lambda_=lambda_,threshold=threshold,fairness=fairness)
    st.caption('Same-cohort restrictions stay active. Excluded edges cannot return during refinement.')
    execute=st.button('Run CASPER',type='primary',icon=':material/play_arrow:',width='stretch')
    st.divider()
    st.caption(f'{len(df)} REAL RESPONSES  ·  11 NUMERIC FEATURES')
    st.caption('Python · C++17 · Streamlit')
    with st.expander('Administrator'):
        configured=bool(secret('CASPER_ADMIN_PASSWORD'))
        if not configured:st.caption('Private uploads and email require a configured administrator password.')
        elif not st.session_state.get('admin'):
            password=st.text_input('Administrator password',type='password')
            if st.button('Sign in'):
                if hmac.compare_digest(password,secret('CASPER_ADMIN_PASSWORD')):
                    st.session_state.admin=True;st.rerun()
                else:st.error('Incorrect password.')
        else:
            st.success('Administrator session')
            if st.button('Sign out'):
                st.session_state.admin=False
                st.session_state.df,st.session_state.audit=load_data(PUBLIC_PATH)
                st.session_state.result=None;st.rerun()

if execute or st.session_state.result is None:
    try:run(settings)
    except Exception as exc:
        st.error(str(exc));st.info('See DEPLOYMENT.md for C++ build and Python environment setup.');st.stop()
result=st.session_state.result
stale=st.session_state.run_settings!=asdict(settings) or st.session_state.run_fingerprint!=fingerprint(df)

st.caption('CASPER  /  ROOMMATE ALLOCATION SYSTEM')
st.title({'Overview':'Preference to pairing.','Pair explorer':'Inspect every connection.','Graph laboratory':'The structure of a match.','Benchmarks':'Measure. Compare. Refine.','Survey evidence':'The data behind the decisions.','Online matching':'A cohort that can evolve.','Delivery':'From pairing to review.'}[page])
st.caption('Constraint-aware scoring · Nonlinear conflict penalties · Heap-based selection · Fairness refinement')
if stale:
    st.warning('Settings or participants changed. Results below belong to the previous run. Select Run CASPER to refresh; exports are disabled.')
    if st.session_state.run_fingerprint!=fingerprint(df):st.stop()

def summary():
    m=result['metrics'];cols=st.columns(4)
    for c,label,value,detail in zip(cols,['Participants','Paired coverage','Mean adjusted score','Weakest pair'],
                                  [str(len(df)),f'{m["coverage"]:.0%}',f'{m["mean"]:.3f}',f'{m["minimum"]:.3f}'],
                                  ['Verified survey records',f'{m["pairs"]} pairs · {m["unmatched"]} unmatched','Model value, not probability','Visible individual outcome']):
        with c:st.metric(label,value,border=True);st.caption(detail)

if page=='Overview':
    summary()
    left,right=st.columns([1.8,1],gap='large')
    with left:
        st.subheader('The pairing network')
        st.caption('Hover to inspect a participant and their selected connection.')
        st.plotly_chart(visuals.network_chart(df,result),width='stretch',key='overview-network')
    with right:
        st.subheader('From all pairs to valid pairs')
        g=result['graph'];st.metric('Eligible connections',f'{g["eligible"]:,}',border=True)
        st.progress(g['eligible']/max(1,g['possible']))
        st.caption(f'{g["cohort_exclusions"]:,} cohort exclusions · {g["conflict_exclusions"]:,} conflict exclusions')
        st.divider()
        st.latex(r'S_{ij}=CS_{ij}-\lambda\,CF_{ij}^{2}')
        st.caption(f'C++ refinement: {result["native"]["swaps"]} accepted swaps across {result["native"]["passes"]} sweeps.')
        st.caption('All statistics are computed from the loaded survey. No hardcoded comparison scores.')
    st.subheader('Selected pairings')
    st.dataframe(result['table'],hide_index=True,width='stretch',column_config={k:st.column_config.NumberColumn(format='%.3f') for k in ['Compatibility','Conflict','Penalty','Adjusted score']})
    if result['unmatched']:
        st.warning('Awaiting review: '+', '.join(df.iloc[result['unmatched']].participant_id))
    st.download_button('Download allocation results',export_results(result,df),'casper-allocation.csv','text/csv',disabled=stale,icon=':material/download:')

elif page=='Pair explorer':
    if result['table'].empty:st.info('No pairs survived the current constraints.');st.stop()
    row_label=st.selectbox('Choose a pairing',result['table'].index,format_func=lambda i:f'{result["table"].iloc[i]["Participant A"]} ↔ {result["table"].iloc[i]["Participant B"]} · {result["table"].iloc[i]["Adjusted score"]:.3f}')
    chosen=result['table'].iloc[row_label];a=df[df.participant_id==chosen['Participant A']].iloc[0];b=df[df.participant_id==chosen['Participant B']].iloc[0]
    left,right=st.columns([1.2,1],gap='large')
    with left:
        st.subheader(f'{a.participant_id}  ↔  {b.participant_id}')
        st.plotly_chart(visuals.radar(a,b),width='stretch')
        shared=[h.title() for h in HOBBIES if a['hobby_'+h] and b['hobby_'+h]]
        st.write('**Shared interests:** '+(', '.join(shared) if shared else 'None recorded'))
    with right:
        st.subheader('Score decomposition')
        for label in ['Compatibility','Conflict','Penalty','Adjusted score']:st.metric(label,f'{chosen[label]:.4f}',border=True)
    parts=conflict_components(a,b)
    st.plotly_chart(visuals.style(px.bar(x=list(parts.values()),y=list(parts),orientation='h',labels={'x':'Weighted contribution to conflict','y':''},color_discrete_sequence=[visuals.AMBER]),280),width='stretch')
    st.caption('Differences describe the supplied survey coding. They are not clinical assessments or a probability of a successful roommate relationship.')

elif page=='Graph laboratory':
    tab1,tab2,tab3=st.tabs(['Network','Pairwise matrix','Score distribution'])
    with tab1:
        candidates=st.toggle('Show eligible graph edges',False)
        st.plotly_chart(visuals.network_chart(df,result,candidates),width='stretch')
        st.caption('Candidate display is capped at 3,500 edges for readability. Computation uses every eligible edge.')
    with tab2:
        kind=st.selectbox('Matrix', ['Adjusted score','Compatibility','Conflict'])
        st.plotly_chart(visuals.heatmap(df,result,kind),width='stretch')
        st.caption('The matrix includes excluded pairs for inspection; exclusion rules still govern the matcher.')
        if st.button('Prepare publication image'):
            fig=visuals.static_heatmap(df,result);buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=180,facecolor=fig.get_facecolor());plt.close(fig)
            st.download_button('Download matrix PNG',buffer.getvalue(),'casper-score-matrix.png','image/png')
    with tab3:st.plotly_chart(visuals.distribution(result),width='stretch')

elif page=='Benchmarks':
    st.subheader('Same data. Same edges. Different solvers.')
    st.dataframe(result['comparison'],hide_index=True,width='stretch')
    c1,c2=st.columns(2)
    with c1:
        st.plotly_chart(visuals.style(px.bar(result['comparison'],x='algorithm',y='total',color='algorithm',labels={'algorithm':'','total':'Total adjusted score'},color_discrete_sequence=visuals.PALETTE),330),width='stretch')
    with c2:
        st.plotly_chart(visuals.style(px.bar(result['comparison'],x='algorithm',y='minimum',color='algorithm',labels={'algorithm':'','minimum':'Weakest pair score'},color_discrete_sequence=visuals.PALETTE),330),width='stretch')
    st.caption('Blossom is an exact maximum-cardinality, maximum-weight reference on the same eligible graph. Compare pair counts as well as scores; CASPER does not guarantee maximum cardinality or optimal weight.')
    st.subheader('Observed execution time')
    timing={'Score matrix (Python)':result['timing']['scoring_ms'],'Heap phase (C++)':result['native']['greedy_ms'],'Refinement (C++)':result['native']['refinement_ms'],'C++ process incl. IPC':result['native']['process_ms'],'Blossom (Python)':result['timing']['exact_ms']}
    st.dataframe(pd.DataFrame({'Stage':timing.keys(),'Milliseconds':timing.values()}),hide_index=True,width='stretch')
    st.caption('Single-run measurements on this host; compilation is excluded. Subprocess overhead and language differences make these unsuitable as a universal speedup claim.')
    st.divider();st.subheader('Adaptive penalty evaluation')
    st.write('Evaluate nine λ values on the real cohort. The recommendation first maximizes paired coverage, then minimizes mean conflict, then maximizes compatibility. It is an explicit selection policy, not a trained predictor.')
    if st.button('Evaluate λ on this cohort',disabled=stale):
        with st.spinner('Running the C++ engine for each penalty value…'):
            st.session_state.sensitivity=(fingerprint(df),asdict(replace(settings,lambda_=0)),*lambda_analysis(df,settings))
    sensitivity=st.session_state.get('sensitivity')
    if sensitivity and sensitivity[0]==fingerprint(df) and sensitivity[1]==asdict(replace(settings,lambda_=0)):
        table,recommended=sensitivity[2:]
        st.metric('Policy-selected λ',f'{recommended:.2f}')
        st.plotly_chart(visuals.style(px.line(table,x='lambda',y=['compatibility','conflict'],markers=True,color_discrete_sequence=visuals.PALETTE),330),width='stretch')
        st.dataframe(table,hide_index=True,width='stretch')
        st.caption('Adjusted scores at different λ values have different penalties and should not be treated as a common evaluation target.')
    st.info('Machine-learning readiness: individual satisfaction is recorded, but current roommate links and pair-outcome labels are absent. A supervised pair-success model cannot be validated from this file. The existing data supports descriptive analysis and penalty sensitivity evaluation.')

elif page=='Survey evidence':
    audit=st.session_state.audit
    st.subheader('98 original responses. Real measurements.')
    st.caption(f'Current loaded cohort: {len(df)} responses. Original values are divided by 10, without imputation or fabricated records.')
    st.plotly_chart(visuals.survey_plot(df),width='stretch')
    left,right=st.columns(2)
    with left:
        st.subheader('Recorded interests')
        counts={h.title():int(df['hobby_'+h].sum()) for h in HOBBIES}
        st.plotly_chart(visuals.style(px.bar(x=list(counts),y=list(counts.values()),color_discrete_sequence=[visuals.CYAN],labels={'x':'Interest','y':'Responses'}),300),width='stretch')
    with right:
        st.subheader('Current roommate satisfaction')
        counts=df.current_sat.value_counts().sort_index()
        st.plotly_chart(visuals.style(px.bar(x=counts.index,y=counts.values,labels={'x':'Recorded rating · 1–5','y':'Responses'},color_discrete_sequence=[visuals.AMBER]),300),width='stretch')
    st.dataframe(public_measurements(df),hide_index=True,width='stretch')
    st.caption('Direct identifiers, email addresses, submission timestamps and branch details are absent from the public dataset. Participant labels are pseudonyms, not a claim of irreversible anonymization.')
    with st.expander('Data validation and provenance'):
        manifest=PROJECT/'data'/'provenance.json'
        if manifest.exists():st.json(json.loads(manifest.read_text()))
        st.caption('Repeated respondent identifiers in the source are flagged in the audit. All source responses are retained; no records are silently merged.')
    if st.session_state.get('admin'):
        uploaded=st.file_uploader('Replace this session with a real survey CSV',type=['csv'])
        if uploaded and st.button('Validate and load survey'):
            try:
                frame,audit=load_data(uploaded);st.session_state.df=frame;st.session_state.audit=audit;st.session_state.result=None;st.session_state.pending=[];st.rerun()
            except ValueError as exc:st.error(str(exc))

elif page=='Online matching':
    st.write('Append an actual new response and either preserve existing pairs or recompute the whole cohort. Updates are isolated to this session and are not automatically saved to the repository.')
    st.caption('No sample response is prefilled. Enter only values collected from a participant.')
    with st.form('new-response'):
        pid=st.text_input('Participant ID',placeholder='Use a unique respondent label')
        gender=st.selectbox('Hostel cohort',['Male','Female'],index=None)
        columns=st.columns(3);values={}
        for i,key in enumerate(NUMERIC):
            with columns[i%3]:values[key]=st.number_input(key.replace('_',' ').title(),0.0,10.0,value=None,step=.5)
        hobbies=st.multiselect('Recorded interests',HOBBIES)
        policy=st.radio('Update policy',['Preserve existing pairs','Re-optimize all participants'],horizontal=True)
        submitted=st.form_submit_button('Add response and update matches',type='primary',disabled=stale)
    if submitted:
        if not pid or gender is None or any(v is None for v in values.values()):st.error('Complete the participant label, cohort and every numeric response.')
        elif pid in df.participant_id.values:st.error('That participant ID already exists.')
        else:
            previous=st.session_state.df
            try:
                row={'participant_id':pid,'gender':gender,**values,**{'hobby_'+h:int(h in hobbies) for h in HOBBIES},'current_sat':np.nan}
                base=public_measurements(df)
                # New records may not have a current-roommate satisfaction rating.
                augmented=pd.concat([base,pd.DataFrame([row])],ignore_index=True)
                validated,audit=load_data(augmented.to_csv(index=False).encode())
                # Retain private contact details only within an authenticated session.
                if st.session_state.get('admin'):
                    for column in ['name', 'email']:
                        contacts=df.set_index('participant_id')[column]
                        validated[column]=validated.participant_id.map(contacts).fillna('')
                preserve=[(df.iloc[a].participant_id,df.iloc[b].participant_id) for a,b in result['pairs']] if policy=='Preserve existing pairs' else []
                st.session_state.df=validated;run(settings,preserve);st.session_state.audit=audit
                st.success(f'Response {pid} added. Preserved {len(preserve)} existing pairs.');st.rerun()
            except Exception as exc:st.session_state.df=previous;st.error(str(exc))
    st.caption('Preserving pairs can leave a new participant unmatched. Fairness refinement then applies only to the remaining unlocked pool. No conflicting pair is forced into the result.')
    st.subheader('Current state')
    st.metric('Participants in this session',len(df))
    st.write('Awaiting review: '+(', '.join(df.iloc[result['unmatched']].participant_id) or 'None'))

elif page=='Delivery':
    st.subheader('Allocation report')
    st.download_button('Download pairings and unmatched participants',export_results(result,df),'casper-allocation.csv','text/csv',disabled=stale)
    st.caption('Pair IDs are identifiers, not fabricated room numbers. Real room inventory is required to attach room assignments.')
    rooms=st.text_area('Available room IDs · one per line',help='Enter actual room identifiers only.')
    room_list=[r.strip() for r in rooms.splitlines() if r.strip()]
    allocated=result['table'].copy()
    if room_list:
        if len(set(room_list))!=len(room_list):st.error('Room identifiers must be unique.')
        elif len(room_list)<len(allocated):st.error('Provide at least one real room per matched pair.')
        else:
            allocated.insert(1,'Room',room_list[:len(allocated)])
            st.dataframe(allocated,hide_index=True,width='stretch')
            safe=allocated.map(lambda x:"'"+x if isinstance(x,str) and x.lstrip().startswith(('=','+','-','@')) else x)
            st.download_button('Download room assignments',safe.to_csv(index=False).encode(),'casper-rooms.csv','text/csv',disabled=stale)
    st.divider();st.subheader('Email notifications')
    st.write('Notification text is prepared from the selected pairing. Delivery requires an administrator session, real addresses and server-side SMTP credentials.')
    if not st.session_state.get('admin'):
        st.info('Email delivery is disabled for public visitors.')
    elif result['table'].empty:st.info('No pairings to notify.')
    else:
        for key in ['EMAIL_USER','EMAIL_PASS','CASPER_ADMIN_PASSWORD','SMTP_HOST','SMTP_PORT']:
            if secret(key):os.environ[key]=secret(key)
        selected=st.selectbox('Pair to notify',result['table'].index,format_func=lambda i:result['table'].iloc[i]['Pair'])
        row=result['table'].iloc[selected];a=df[df.participant_id==row['Participant A']].iloc[0];b=df[df.participant_id==row['Participant B']].iloc[0]
        st.code(f'Your participant ID: {a.participant_id}\nProposed roommate ID: {b.participant_id}\nPlease review this proposed pairing with the allocation coordinator.',language=None)
        confirmed=st.checkbox('I reviewed this pairing and intend to notify both participants.')
        ready=email_ready() and bool(a.email) and bool(b.email) and confirmed and not stale
        if not bool(a.email) or not bool(b.email):st.caption('Load the private source CSV in the administrator survey view to resolve recipient addresses.')
        if st.button('Send the two notifications',disabled=not ready):
            sent=[]
            history=st.session_state.setdefault('sent_notifications',set())
            try:
                for person,other in [(a,b),(b,a)]:
                    key=(fingerprint(df),person.participant_id,other.participant_id)
                    if key not in history:
                        actual_room=allocated.iloc[selected].get('Room',None)
                        send_email(compose(person.email,person.participant_id,other.participant_id,actual_room))
                        history.add(key)
                    sent.append(person.participant_id)
                st.success('Sent to both participants.')
            except Exception:
                st.error('Delivery failed. Successfully sent participant IDs: '+(', '.join(sent) or 'none')+'. Check SMTP settings before retrying.')

st.divider()
st.caption('CASPER · Score-based pairing. Human review remains part of allocation. No optimality, stable-roommate or predictive-accuracy guarantee is implied.')
