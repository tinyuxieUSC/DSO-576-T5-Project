"""Render aggregates only. Exports use an explicit public-column whitelist."""
from __future__ import annotations
import json
import hashlib
import pandas as pd
import altair as alt
import streamlit as st
from .filters import METRIC_DTYPES

LIMITATION = ('Observed ListenBrainz submissions are an incomplete sample of playback history and client users. '
              'Missing or invalid identifiers do not establish client causation, current maintainer activity, or feasibility of a fix.')
SCENARIO_WARNING = 'Hypothetical scenario only. The target may not be attainable; additions are not observed listens, a forecast, or a causal effect.'
NONADDITIVE = 'An account may use more than one client, so account counts across clients are not additive.'
FORMULA = ('score = w × log1p(affected accounts)/log1p(max affected accounts) + '
           '(1−w) × log1p(unusable IDs)/log1p(max unusable IDs); zero maxima contribute zero. '
           'Additional tagged listens = round(min(unusable IDs, max(0, target × total − valid IDs))); ties to even.')
PUBLIC_COLUMNS = set(METRIC_DTYPES) | {'rank','score','client_version','week_start','partial_week',
                                     'reach_weight','target_coverage','additional_tagged_listens'}
METADATA_COLUMNS = {'mode','fingerprint','playback_start','playback_end','source_files','source_intervals','accepted_events',
                    'exclude_importers','minimum_accounts','account_floor','volume_weight','methodology',
                    'limitations','account_counts_note','warnings','version_evidence','comparison_clients'}


def export_table(table, metadata):
    # Deliberately discard every column outside the contract, including unexpected identifiers.
    out = table[[c for c in table.columns if c in PUBLIC_COLUMNS]].copy()
    for key,value in metadata.items():
        if key in METADATA_COLUMNS | {'reach_weight','target_coverage'}:
            out[key] = json.dumps(value, ensure_ascii=False, default=str) if isinstance(value,(dict,list,tuple)) else value
    # Prevent spreadsheet formula execution from untrusted free-text client/version labels.
    for col in out.select_dtypes(include=['object','string']).columns:
        out[col] = out[col].map(lambda v: "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v)
    return out.to_csv(index=False)


def briefing_markdown(table, metadata):
    clean = table[[c for c in table.columns if c in PUBLIC_COLUMNS]]
    lines = ['# Client metadata outreach briefing', '', LIMITATION, '', NONADDITIVE, '', SCENARIO_WARNING, '', '## Selected evidence']
    for row in clean.to_dict('records'):
        lines.append('')
        lines.extend(f'- {key}: {value}' for key,value in row.items())
    lines.extend(['', '## Settings and evidence'])
    lines.extend(f'- {key}: {value}' for key,value in metadata.items() if key in METADATA_COLUMNS | {'reach_weight','target_coverage'})
    lines.extend(['', '## Calculations', '', FORMULA, '', 'Recording MBID coverage measures canonical UUID syntax, not MusicBrainz existence. Opportunity includes absent and populated invalid identifiers.', '', 'Evidence summary for human review; no outreach has been sent.'])
    return '\n'.join(lines)


def table_config():
    return {'coverage':st.column_config.NumberColumn('Coverage',format='percent',step=0.1,width='small'),
            'score':st.column_config.NumberColumn('Score',format='%.3f'),
            'target_coverage':st.column_config.NumberColumn('Target',format='percent',step=0.1),
            'client':st.column_config.TextColumn('Submission client',width='medium'),
            'missing_recording_mbid':st.column_config.NumberColumn('Without usable MBID',format='localized'),
            'total_listens':st.column_config.NumberColumn('Listens',format='localized'),
            'distinct_accounts':st.column_config.NumberColumn('Accounts',format='localized'),
            'affected_accounts':st.column_config.NumberColumn('Affected accounts',format='localized')}


def shortlist(ranked, size):
    st.subheader('Find the next pilot partner')
    st.write('Compare affected-account reach and listens without a usable recording MBID. Select a row or point to inspect a candidate.')
    if ranked.empty:
        st.info('No named clients meet these filters. Lower the minimum accounts, include importers, or widen the playback dates.')
        return None
    a,b,c = st.columns(3)
    a.metric('Eligible clients',f'{len(ranked):,}')
    b.metric('Observed listens · eligible clients',f'{ranked.total_listens.sum():,}')
    c.metric('Without usable recording MBID',f'{ranked.missing_recording_mbid.sum():,}')
    cols = ['rank','client','client_type','score','total_listens','distinct_accounts','affected_accounts','missing_recording_mbid','coverage']
    top = ranked.head(size)[cols]
    styled = top.style.apply(lambda row: ['background-color: rgba(82, 169, 149, .12)' if row['rank'] <= 3 else '' for _ in row], axis=1)
    event = st.dataframe(styled,hide_index=True,width='stretch',column_config=table_config(),
                         on_select='rerun',selection_mode='single-row',key='shortlist_table')
    st.caption(f'Table: top {min(size,len(ranked))}. Scatter and selectors: all {len(ranked)} eligible clients. Unknown classification means unverified, not regular.')
    selection = alt.selection_point(name='candidate',fields=['client'],on='click',clear='dblclick')
    chart = alt.Chart(ranked).mark_circle(opacity=.75,stroke='white',strokeWidth=1).encode(
        x=alt.X('affected_accounts:Q',title='Affected accounts',scale=alt.Scale(zero=True)),
        y=alt.Y('missing_recording_mbid:Q',title='Listens without a usable recording MBID',scale=alt.Scale(zero=True)),
        size=alt.Size('total_listens:Q',title='Listens',scale=alt.Scale(range=[55,1000])),
        color=alt.Color('client_type:N',title='Classification',scale=alt.Scale(domain=['regular','importer','unknown'],range=['#398b7d','#d38753','#7b83a6'])),
        tooltip=['client','client_type',alt.Tooltip('distinct_accounts:Q',format=',.0f'),
                 alt.Tooltip('affected_accounts:Q',format=',.0f'),alt.Tooltip('total_listens:Q',format=',.0f'),
                 alt.Tooltip('missing_recording_mbid:Q',format=',.0f'),alt.Tooltip('coverage:Q',format='.1%')]
    ).add_params(selection).properties(height=340)
    point = st.altair_chart(chart,width='stretch',on_select='rerun',key='reach_scatter')
    chosen = point.selection.get('candidate',[])
    rows = list(event.selection.rows)
    new_point = chosen != st.session_state.get('_last_point_selection', [])
    new_row = rows != st.session_state.get('_last_row_selection', [])
    st.session_state['_last_point_selection'] = chosen
    st.session_state['_last_row_selection'] = rows
    if chosen and new_point:
        return chosen[0]['client']
    if rows and new_row:
        return top.iloc[event.selection.rows[0]].client
    st.caption('Usable means a recording MBID with valid UUID syntax. Both absent and populated invalid IDs count as opportunity. Score is a screening aid, not a probability.')
    return None


def detail(row,versions,weeks,sensitivity):
    if row is None:
        st.info('Select a client from the shortlist or the client selector to inspect its evidence.')
        return
    st.subheader(row['client'])
    st.caption(f"Rank {row['rank']} · {row['client_type']} classification · score {row['score']:.3f}")
    columns = st.columns(4)
    for box,label,value in zip(columns,['Listens','Distinct accounts','Affected accounts','MBID coverage'],
                                [f"{row['total_listens']:,}",f"{row['distinct_accounts']:,}",f"{row['affected_accounts']:,}",f"{row['coverage']:.1%}"]):
        box.metric(label,value)
    coverage = pd.DataFrame({'status':['Valid UUID syntax','Without usable recording MBID'],
                             'listens':[row['with_recording_mbid'],row['missing_recording_mbid']]})
    st.altair_chart(alt.Chart(coverage).mark_bar().encode(
        x=alt.X('listens:Q',stack='normalize',axis=alt.Axis(format='%'),title='Share of selected listens'),
        color=alt.Color('status:N',scale=alt.Scale(range=['#398b7d','#d8a36e']),title=None),
        tooltip=['status',alt.Tooltip('listens:Q',format=',.0f')]).properties(height=90),width='stretch')
    st.caption(f"Denominator: {row['total_listens']:,} listens. Absent IDs: {row['absent_recording_mbid']:,}; populated invalid IDs: {row['invalid_recording_mbid']:,}. UUID syntax does not verify MusicBrainz existence. Unknown-account listens: {row['unknown_account_listens']:,}.")
    st.markdown('**Version evidence**')
    known = 1-row['unknown_version_listens']/row['total_listens']
    st.caption(f'Known version share: {known:.1%}; unknown: {1-known:.1%}. Versions remain free text.')
    st.dataframe(versions,hide_index=True,width='stretch',column_config=table_config())
    if weeks is not None and len(weeks):
        st.markdown('**Weekly playback evidence**')
        plot = weeks.copy()
        plot['week_start'] = pd.to_datetime(plot.week_start)
        # Segment IDs prohibit line interpolation across unavailable weeks.
        plot['segment'] = plot.total_listens.isna().cumsum().astype(str)
        base = alt.Chart(plot).encode(x=alt.X('week_start:T',title='UTC week beginning Monday'))
        counts = base.transform_fold(['total_listens','missing_recording_mbid'],as_=['measure','listens']).mark_bar().encode(
            y=alt.Y('listens:Q',title='Observed listens'),xOffset='measure:N',color='measure:N',
            tooltip=['week_start:T','measure:N','listens:Q','partial_week:N'])
        cov = base.mark_line(point=True,color='#398b7d').encode(y=alt.Y('coverage:Q',axis=alt.Axis(format='%'),title='Coverage'),detail='segment:N')
        st.altair_chart(alt.vconcat(counts,cov).resolve_scale(color='independent'),width='stretch')
        st.dataframe(weeks,hide_index=True,column_config=table_config(),width='stretch')
        st.caption('Unavailable weeks are gaps, not measured zero coverage. Edge weeks may be partial.')
    st.markdown('**Ranking sensitivity**')
    st.dataframe(sensitivity.loc[sensitivity.client == row['client']],hide_index=True,width='stretch')
    st.caption(FORMULA)


def scenario_chart(scenarios):
    records = []
    for r in scenarios.to_dict('records'):
        for label,column in [('Observed · valid UUID','with_recording_mbid'),('Observed · unusable ID','missing_recording_mbid'),('Hypothetical · additions','additional_tagged_listens')]:
            records.append({'client':r['client'],'measure':label,'listens':r[column],
                            'kind':'Hypothetical' if label.startswith('Hypothetical') else 'Observed'})
    frame = pd.DataFrame(records)
    palette = ['#398b7d','#d38753','#7b83a6','#a26683','#587bb5','#8c873e','#ab6846','#63968d','#976da1']
    clients = sorted(scenarios.client)
    colors = [palette[int(hashlib.sha256(c.encode()).hexdigest()[:8],16) % len(palette)] for c in clients]
    client_scale = alt.Scale(domain=clients,range=colors)
    return alt.Chart(frame).mark_bar(strokeWidth=2).encode(
        x=alt.X('client:N',sort=scenarios.client.tolist(),title='Client'),xOffset=alt.XOffset('measure:N',sort=['Observed · valid UUID','Observed · unusable ID','Hypothetical · additions']),
        y=alt.Y('listens:Q',title='Listen count'),color=alt.Color('client:N',scale=client_scale,title='Client'),
        fillOpacity=alt.FillOpacity('kind:N',scale=alt.Scale(domain=['Observed','Hypothetical'],range=[.8,.12]),title='Evidence'),
        stroke=alt.Stroke('client:N',scale=client_scale,legend=None),strokeDash=alt.StrokeDash('kind:N',scale=alt.Scale(domain=['Observed','Hypothetical'],range=[[1,0],[5,3]]),title='Evidence'),
        tooltip=['client','measure',alt.Tooltip('listens:Q',format=',.0f')]).properties(height=340)


def comparison(scenarios):
    st.subheader('Compare a coverage scenario')
    st.warning(SCENARIO_WARNING)
    st.caption(NONADDITIVE)
    if len(scenarios)<2:
        st.info('Choose two or three eligible clients using the comparison selector.')
        return
    st.altair_chart(scenario_chart(scenarios),width='stretch')
    st.caption('Solid bars: observed valid and unusable identifiers. Pale dashed outlines: hypothetical additions, drawn separately from observed counts.')
    st.dataframe(scenarios[['client','distinct_accounts','affected_accounts','total_listens','coverage','target_coverage','additional_tagged_listens']],
                 hide_index=True,width='stretch',column_config=table_config())
    st.caption(FORMULA)


def briefing(ranked,row,scenario,metadata):
    st.subheader('Prepare an evidence briefing')
    st.caption(NONADDITIVE)
    st.download_button('Download all eligible clients · CSV',export_table(ranked,metadata),'eligible-clients.csv','text/csv')
    if row is None:
        st.info('Select a client to generate its outreach briefing.')
        return
    selected = scenario.loc[scenario.client == row['client']] if len(scenario) else pd.DataFrame()
    if selected.empty:
        selected = pd.DataFrame([row])
    md = briefing_markdown(selected,metadata)
    st.markdown(md)
    a,b = st.columns(2)
    a.download_button('Download client briefing · Markdown',md,'client-briefing.md','text/markdown')
    b.download_button('Download client evidence · CSV',export_table(selected,metadata),'client-briefing.csv','text/csv')
    st.info('This briefing is an aggregate evidence summary for human review. It does not send an outreach message.')
