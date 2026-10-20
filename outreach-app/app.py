"""Streamlit entry point: configuration, controls, shared selection, wiring."""
from datetime import date
from pathlib import Path
import streamlit as st
from outreach.setup import load_config, cli_args, DataFilters
from outreach.loader import open_prepared, get_data_status, get_client_metrics, get_version_metrics, get_weekly_metrics
from outreach.filters import rank_clients, rank_sensitivity, estimate_scenarios
from outreach import views

st.set_page_config(page_title='Client Metadata Outreach Prioritizer',page_icon='◈',layout='wide')
st.markdown('''<style>
.block-container{max-width:1400px;padding-top:2.3rem}h1{letter-spacing:-.045em;font-weight:650!important}
[data-testid="stMetricValue"]{font-variant-numeric:tabular-nums} [data-testid="stSidebar"]{border-right:1px solid #dce6e2}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner=False,max_entries=48)
def client_query(fingerprint,mode,query,budget,_data):
    return get_client_metrics(_data,query)

@st.cache_data(show_spinner=False,max_entries=64)
def detail_query(fingerprint,mode,query,client,grouping,budget,_data):
    return (get_version_metrics if grouping=='version' else get_weekly_metrics)(_data,query,client)


def main():
    args=cli_args()
    st.caption('METABRAINZ · OUTREACH PLANNING')
    st.title('Client metadata outreach prioritizer')
    st.write('Choose which observed ListenBrainz client maintainer to investigate first for better recording identifiers.')
    try:
        config=load_config(args.config,args.mode)
        data=open_prepared(config)
        status=get_data_status(data)
    except (ValueError,OSError,KeyError) as e:
        st.error(str(e))
        st.code(f'python -m outreach.prepare --config "{args.config}" --mode {args.mode or "sample"}')
        return
    d=config.defaults
    with st.sidebar:
        st.header('Decision settings')
        st.badge(f'{data.mode.upper()} DATA',color='blue' if data.mode=='sample' else 'green')
        dates=st.date_input('Inclusive UTC playback dates',value=(status.start,status.end),min_value=status.start,max_value=status.end)
        exclude=st.toggle('Exclude classified importers',value=d['exclude_importers'])
        minimum=st.number_input('Minimum distinct accounts',min_value=d['minimum_accounts_floor'],value=max(d['minimum_accounts'],d['minimum_accounts_floor']),step=1)
        reach=st.slider('Affected-account reach weight (%)',0,100,round(d['reach_weight']*100))/100
        st.caption(f'Missing-ID volume weight: {1-reach:.0%}')
        target=st.slider('Scenario target coverage (%)',0,100,round(d['target_coverage']*100))/100
        st.caption(f'Account floor: {d["minimum_accounts_floor"]}. This is not an anonymity guarantee.')
    if len(dates)!=2:
        st.info('Choose both endpoints of the playback date range.')
        return
    try:
        query=DataFilters(dates[0],dates[1],exclude,int(minimum))
        with st.spinner('Querying prepared aggregates…'):
            metrics=client_query(data.fingerprint,data.mode,query,data.memory_budget_mb,data)
    except (ValueError,MemoryError,OSError) as e:
        st.error(str(e))
        return
    ranked=rank_clients(metrics,reach)
    choices=ranked.client.tolist()
    if st.session_state.get('detail_client') not in choices:
        st.session_state['detail_client']=None
    if 'comparison_clients' in st.session_state:
        st.session_state['comparison_clients']=[c for c in st.session_state['comparison_clients'] if c in choices]
    with st.sidebar:
        selected=st.selectbox('Inspect a client',choices,index=None,placeholder='Select a candidate',key='detail_client')
        clients=st.multiselect('Compare two or three clients',choices,max_selections=3,key='comparison_clients')
    st.caption(f'{data.mode.upper()} · {status.accepted:,} accepted source events · playback {query.start} → {query.end} · importer exclusion {"on" if exclude else "off"}')
    st.caption(views.LIMITATION)
    with st.expander('Source provenance, quality, and methodology'):
        st.write('Submission collection interval(s):',status.provenance['source_intervals'] or 'Unknown for this sample')
        st.write('Available observed playback dates:',f'{status.start} → {status.end}')
        st.write('Prepared fingerprint:',data.fingerprint)
        st.json({'quality':status.provenance['quality'],'accepted':status.accepted,'rejected':status.provenance['rejected'],
                 'inputs':status.provenance['input_records'],'classification':config.classification,'aliases':config.aliases})
        for warning in status.warnings: st.warning(warning)
        st.caption(views.FORMULA)
    scenarios=estimate_scenarios(ranked,clients,target)
    row=ranked.loc[ranked.client==selected].iloc[0].to_dict() if selected in choices else None
    versions=weeks=None
    try:
        if row:
            versions=detail_query(data.fingerprint,data.mode,query,selected,'version',data.memory_budget_mb,data)
            if (query.end-query.start).days>=7:
                weeks=detail_query(data.fingerprint,data.mode,query,selected,'week',data.memory_budget_mb,data)
    except (MemoryError,OSError,ValueError) as e:
        st.error(str(e))
        return
    metadata={'mode':data.mode,'fingerprint':data.fingerprint,'playback_start':str(query.start),'playback_end':str(query.end),
              'source_files':[Path(i['path']).name for i in status.provenance.get('inputs',[])],
              'source_intervals':status.provenance['source_intervals'],'accepted_events':status.accepted,
              'exclude_importers':exclude,'minimum_accounts':minimum,'account_floor':d['minimum_accounts_floor'],
              'reach_weight':reach,'volume_weight':1-reach,'target_coverage':target,'methodology':views.FORMULA,
              'limitations':views.LIMITATION+' '+views.SCENARIO_WARNING,'account_counts_note':views.NONADDITIVE,
              'warnings':status.warnings,'comparison_clients':clients,
              'version_evidence':versions.to_dict('records') if versions is not None else []}
    tabs=st.tabs(['Shortlist','Client detail','Scenario comparison','Briefing'],key='active_tab',on_change='rerun')
    with tabs[0]:
        clicked=views.shortlist(ranked,d['shortlist_size'])
        if clicked and clicked!=selected:
            # Apply before the next run's selector is instantiated.
            st.session_state['_pending_client']=clicked
            st.rerun()
    with tabs[1]: views.detail(row,versions,weeks,rank_sensitivity(metrics,[0,.5,1,reach]))
    with tabs[2]: views.comparison(scenarios)
    with tabs[3]: views.briefing(ranked,row,scenarios,metadata)

if '_pending_client' in st.session_state:
    st.session_state['detail_client']=st.session_state.pop('_pending_client')
    st.session_state['active_tab']='Client detail'
main()
