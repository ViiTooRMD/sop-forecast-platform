from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='S&OP Control Tower', page_icon='📦', layout='wide', initial_sidebar_state='expanded')

JAMEF_RED = '#C8102E'
DARK = '#1D1D1B'
MUTED = '#6B7280'
BG = '#F6F7F9'

st.markdown(f"""
<style>
.stApp {{ background: {BG}; }}
[data-testid='stSidebar'] {{ background: #161616; }}
[data-testid='stSidebar'] * {{ color: #F7F7F7; }}
.block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px; }}
.hero {{ background: linear-gradient(120deg, #171717 0%, #292929 62%, {JAMEF_RED} 100%); color:white; padding:24px 28px; border-radius:18px; margin-bottom:18px; box-shadow:0 10px 30px rgba(0,0,0,.12); }}
.hero h1 {{ margin:0; font-size:30px; }}
.hero p {{ margin:7px 0 0; color:#E5E7EB; }}
.card {{ background:white; border:1px solid #E5E7EB; border-radius:16px; padding:18px; min-height:120px; box-shadow:0 4px 16px rgba(15,23,42,.05); }}
.card .label {{ font-size:12px; color:{MUTED}; text-transform:uppercase; letter-spacing:.08em; font-weight:700; }}
.card .value {{ font-size:26px; color:{DARK}; font-weight:800; margin-top:8px; }}
.card .delta {{ font-size:12px; color:{MUTED}; margin-top:7px; }}
.section-title {{ font-size:19px; font-weight:800; color:{DARK}; margin:4px 0 12px; }}
.process {{ display:flex; gap:10px; align-items:stretch; margin:6px 0 18px; }}
.step {{ flex:1; background:white; border:1px solid #E5E7EB; border-radius:14px; padding:14px; }}
.step.active {{ border:2px solid {JAMEF_RED}; background:#FFF7F8; }}
.step .n {{ color:{JAMEF_RED}; font-weight:900; font-size:12px; }}
.step .t {{ font-weight:800; margin-top:4px; color:{DARK}; }}
.step .d {{ color:{MUTED}; font-size:12px; margin-top:5px; }}
[data-testid='stMetric'] {{ background:white; border:1px solid #E5E7EB; border-radius:14px; padding:12px 14px; }}
</style>
""", unsafe_allow_html=True)

@dataclass
class Scenario:
    demand_factor: float
    restriction: float
    productivity: float
    overtime: float
    third_party: float
    vehicle_cost: float

SCENARIOS = {
    'Cenário Base': Scenario(1.00, 0.035, 1.00, 0.08, 0.05, 740),
    'Peak Season': Scenario(1.17, 0.025, 0.96, 0.14, 0.11, 790),
    'Otimista': Scenario(1.10, 0.015, 1.04, 0.08, 0.04, 725),
    'Conservador': Scenario(0.93, 0.055, 0.98, 0.04, 0.03, 710),
}

FILIAIS = ['SAO', 'BHZ', 'RIO', 'CWB', 'SSA', 'REC', 'FOR', 'CGB']
PROCESSOS = ['Coleta', 'Transbordo', 'Entrega']

@st.cache_data
def build_data(seed: int = 42):
    rng = np.random.default_rng(seed)
    days = pd.date_range('2026-08-01', periods=122, freq='D')
    rows = []
    base_branch = {'SAO': 28000, 'BHZ': 15500, 'RIO': 17600, 'CWB': 14200, 'SSA': 10800, 'REC': 9700, 'FOR': 8800, 'CGB': 7200}
    for d in days:
        weekday = 0.68 if d.weekday() >= 5 else 1.0
        seasonal = 1 + 0.12 * math.sin((d.dayofyear - 210) / 35)
        for i, filial in enumerate(FILIAIS):
            forecast = base_branch[filial] * weekday * seasonal * rng.normal(1, 0.055)
            rows.append({'data': d, 'filial': filial, 'previsao': max(forecast, 0), 'b2c_pct': 0.13 + 0.02*i + rng.normal(0, .006)})
    demand = pd.DataFrame(rows)
    demand['receita_caixa'] = demand['filial'].map({'SAO':48,'BHZ':46,'RIO':49,'CWB':47,'SSA':53,'REC':55,'FOR':56,'CGB':52})
    demand['margem_pct'] = demand['filial'].map({'SAO':.31,'BHZ':.29,'RIO':.28,'CWB':.33,'SSA':.27,'REC':.26,'FOR':.25,'CGB':.30})
    people = pd.DataFrame([(f,p) for f in FILIAIS for p in PROCESSOS], columns=['filial','processo'])
    people['fte_atual'] = [72,55,81, 42,34,49, 48,38,56, 39,31,44, 30,25,36, 28,23,34, 25,21,31, 22,19,27]
    people['produtividade'] = people['processo'].map({'Coleta':64,'Transbordo':78,'Entrega':58})
    people['horas'] = 7.2
    people['eficiencia'] = .88
    vehicles = pd.DataFrame([(f,t) for f in FILIAIS for t in ['VUC','3/4','Toco']], columns=['filial','tipo'])
    vehicles['frota_atual'] = np.tile([18,12,8], len(FILIAIS)) - np.repeat(np.arange(len(FILIAIS))//3, 3)
    vehicles['capacidade_unitaria'] = vehicles['tipo'].map({'VUC':520,'3/4':780,'Toco':1120})
    vehicles['share'] = vehicles['tipo'].map({'VUC':.40,'3/4':.37,'Toco':.23})
    return demand, people, vehicles

def apply_scenario(demand: pd.DataFrame, scenario: Scenario, override: float, floor_pct: float):
    df = demand.copy()
    df['apos_override'] = df['previsao'] * scenario.demand_factor * (1 + override)
    df['apos_restricao'] = df['apos_override'] * (1 - scenario.restriction)
    branch_total = df.groupby(['data','filial'])['apos_override'].transform('sum')
    df['piso'] = branch_total * floor_pct
    restricted_total = df.groupby(['data','filial'])['apos_restricao'].transform('sum')
    recomposition = np.maximum(df['piso'] - restricted_total, 0)
    share = df['apos_restricao'] / restricted_total.replace(0, np.nan)
    df['demanda_final'] = df['apos_restricao'] + recomposition * share.fillna(0)
    return df

def fmt_currency(v):
    return f"R$ {v/1_000_000:,.1f} mi".replace(',', 'X').replace('.', ',').replace('X', '.')

def card(label, value, delta):
    st.markdown(f"<div class='card'><div class='label'>{label}</div><div class='value'>{value}</div><div class='delta'>{delta}</div></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('## S&OP Control Tower')
    st.caption('Planejamento integrado | visão simulada')
    st.divider()
    page = st.radio('Navegação', ['Resumo Executivo','Demanda e Restrições','Capacidade de Pessoas','Frota e Veículos','Financeiro e EBITDA','Premissas e Governança'])
    st.divider()
    scenario_name = st.selectbox('Cenário', list(SCENARIOS))
    selected_filiais = st.multiselect('Filiais', FILIAIS, default=FILIAIS)
    override = st.slider('Override comercial', -10, 20, 4, 1) / 100
    floor_pct = st.slider('Piso mínimo da filial', 70, 100, 92, 1) / 100
    st.caption('Os controles recalculam toda a cadeia de demanda, capacidade e EBITDA.')

scenario = SCENARIOS[scenario_name]
demand, people, vehicles = build_data()
adj = apply_scenario(demand[demand.filial.isin(selected_filiais)], scenario, override, floor_pct)

month = adj.assign(mes=adj.data.dt.to_period('M').astype(str)).groupby(['mes','filial'], as_index=False).agg(previsao=('previsao','sum'), demanda_final=('demanda_final','sum'), receita_caixa=('receita_caixa','mean'), margem_pct=('margem_pct','mean'))
flow = month.copy()
flow['coleta'] = flow['demanda_final']
flow['transbordo'] = flow['demanda_final'] * .64
flow['entrega'] = flow['demanda_final'] * (1 + adj.groupby('filial').b2c_pct.mean().reindex(flow.filial).values * .18)

people_calc = people[people.filial.isin(selected_filiais)].merge(flow.groupby('filial', as_index=False)[['coleta','transbordo','entrega']].mean(), on='filial')
people_calc['demanda_processo'] = people_calc.apply(lambda r: r[r.processo.lower()], axis=1) / 22
people_calc['capacidade_atual'] = people_calc.fte_atual * people_calc.horas * people_calc.produtividade * people_calc.eficiencia * scenario.productivity
people_calc['fte_necessario'] = people_calc.demanda_processo / (people_calc.horas * people_calc.produtividade * people_calc.eficiencia * scenario.productivity)
people_calc['gap_fte'] = people_calc.fte_necessario - people_calc.fte_atual
people_calc['acao'] = np.select([people_calc.gap_fte > 3, people_calc.gap_fte > 0, people_calc.gap_fte < -4], ['Contratar / terceiro','Hora extra','Realocar / reduzir'], default='Manter')

veh = vehicles[vehicles.filial.isin(selected_filiais)].merge(flow.groupby('filial', as_index=False).entrega.mean(), on='filial')
veh['capacidade_atual'] = veh.frota_atual * veh.capacidade_unitaria
branch_cap = veh.groupby('filial').capacidade_atual.transform('sum')
veh['novo_volume'] = np.maximum(veh.entrega/22 - branch_cap, 0)
veh['veiculos_adicionais'] = np.ceil(veh.novo_volume * veh.share / veh.capacidade_unitaria).astype(int)

revenue_base = (month.previsao * month.receita_caixa).sum()
revenue_final = (month.demanda_final * month.receita_caixa).sum()
margin_base = (month.previsao * month.receita_caixa * month.margem_pct).sum()
margin_final = (month.demanda_final * month.receita_caixa * month.margem_pct).sum()
fte_hires = int(np.ceil(people_calc.gap_fte.clip(lower=0).sum()))
people_cost = fte_hires * 5200 * 4 + people_calc.capacidade_atual.sum() * scenario.overtime * 0.16
vehicle_cost = veh.veiculos_adicionais.sum() * scenario.vehicle_cost * 22 * 4
eb_base = 24_800_000
eb_proj = eb_base + (margin_final - margin_base) - people_cost - vehicle_cost

st.markdown(f"<div class='hero'><h1>{page}</h1><p>{scenario_name} · horizonte ago–nov/2026 · {len(selected_filiais)} filiais selecionadas</p></div>", unsafe_allow_html=True)

steps = [('01','Consenso de demanda','Comercial + IM'),('02','Capacidade operacional','Operações'),('03','Plano de atuação','Pessoas + frota'),('04','Conciliação financeira','Finanças'),('05','Reconciliação executiva','Decisão')]
active_map = {'Resumo Executivo':5,'Demanda e Restrições':1,'Capacidade de Pessoas':2,'Frota e Veículos':3,'Financeiro e EBITDA':4,'Premissas e Governança':5}
html = "<div class='process'>" + ''.join([f"<div class='step {'active' if i==active_map[page] else ''}'><div class='n'>{n}</div><div class='t'>{t}</div><div class='d'>{d}</div></div>" for i,(n,t,d) in enumerate(steps,1)]) + '</div>'
st.markdown(html, unsafe_allow_html=True)

if page == 'Resumo Executivo':
    cols = st.columns(5)
    values = [('Demanda consensada', f"{month.demanda_final.sum()/1e6:.2f} mi caixas", f"{(month.demanda_final.sum()/month.previsao.sum()-1)*100:+.1f}% vs. previsão"),('Receita em risco', fmt_currency(max(revenue_base-revenue_final,0)), 'efeito das restrições'),('Gap de FTE', f"{fte_hires}", 'contratar ou cobrir'),('Veículos adicionais', f"{veh.veiculos_adicionais.sum()}", 'média do horizonte'),('EBITDA projetado', fmt_currency(eb_proj), f"{(eb_proj/eb_base-1)*100:+.1f}% vs. base")]
    for c,(a,b,d) in zip(cols,values):
        with c: card(a,b,d)
    c1,c2 = st.columns([1.7,1])
    with c1:
        st.markdown("<div class='section-title'>Demanda, capacidade e risco por mês</div>", unsafe_allow_html=True)
        agg = flow.groupby('mes', as_index=False).agg(demanda=('demanda_final','sum'), capacidade=('coleta','sum'))
        agg['capacidade'] *= .96
        fig = go.Figure()
        fig.add_trace(go.Bar(x=agg.mes,y=agg.demanda,name='Demanda consensada'))
        fig.add_trace(go.Scatter(x=agg.mes,y=agg.capacidade,name='Capacidade base',mode='lines+markers',line=dict(width=4)))
        fig.update_layout(height=360, margin=dict(l=10,r=10,t=20,b=10), legend=dict(orientation='h'))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("<div class='section-title'>Decisões para o fórum executivo</div>", unsafe_allow_html=True)
        decisions = pd.DataFrame({'Decisão':['Aprovar cobertura de FTE','Contratar frota flexível','Revisar restrições comerciais','Validar impacto EBITDA'],'Responsável':['Operações','Frota','Comercial','Finanças'],'Prazo':['D+5','D+7','D+2','D+3'],'Status':['Pendente','Em análise','Em análise','Pendente']})
        st.dataframe(decisions, hide_index=True, use_container_width=True, height=275)

elif page == 'Demanda e Restrições':
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Previsão bruta', f"{month.previsao.sum()/1e6:.2f} mi")
    c2.metric('Após override', f"{adj.apos_override.sum()/1e6:.2f} mi", f"{override*100:+.0f}%")
    c3.metric('Após restrições', f"{adj.apos_restricao.sum()/1e6:.2f} mi", f"-{scenario.restriction*100:.1f}%")
    c4.metric('Demanda final', f"{month.demanda_final.sum()/1e6:.2f} mi", 'piso aplicado')
    trend = adj.groupby('data',as_index=False)[['previsao','apos_override','apos_restricao','demanda_final']].sum()
    fig = px.line(trend, x='data', y=['previsao','apos_override','apos_restricao','demanda_final'], labels={'value':'Caixas','variable':'Camada'})
    fig.update_layout(height=390, legend=dict(orientation='h'))
    st.plotly_chart(fig, use_container_width=True)
    review = month.groupby('filial',as_index=False).agg(previsao=('previsao','sum'),demanda_final=('demanda_final','sum'))
    review['variacao_pct'] = review.demanda_final/review.previsao-1
    review['status'] = np.where(review.variacao_pct > .08,'Revisar capacidade',np.where(review.variacao_pct < -.03,'Validar restrição','Consensado'))
    st.dataframe(review, hide_index=True, use_container_width=True)

elif page == 'Capacidade de Pessoas':
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('FTE atual', f"{people_calc.fte_atual.sum():.0f}")
    c2.metric('FTE necessário', f"{people_calc.fte_necessario.sum():.0f}")
    c3.metric('Cobertura por HE', f"{scenario.overtime*100:.0f}%")
    c4.metric('Cobertura terceiros', f"{scenario.third_party*100:.0f}%")
    fig = px.bar(people_calc, x='filial', y='gap_fte', color='processo', barmode='group', title='Gap de FTE por filial e processo')
    fig.add_hline(y=0, line_width=1)
    fig.update_layout(height=390)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(people_calc[['filial','processo','fte_atual','fte_necessario','gap_fte','acao']], hide_index=True, use_container_width=True)

elif page == 'Frota e Veículos':
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Frota atual', f"{veh.frota_atual.sum()}")
    c2.metric('Veículos adicionais', f"{veh.veiculos_adicionais.sum()}")
    c3.metric('Custo incremental', fmt_currency(vehicle_cost))
    c4.metric('Apropriação validada', '100%', 'por filial')
    summary = veh.groupby('filial',as_index=False).agg(demanda=('entrega','mean'),capacidade=('capacidade_atual','sum'),adicionais=('veiculos_adicionais','sum'))
    summary['demanda_dia'] = summary.demanda/22
    fig = go.Figure([go.Bar(x=summary.filial,y=summary.demanda_dia,name='Demanda entrega/dia'),go.Bar(x=summary.filial,y=summary.capacidade,name='Capacidade frota')])
    fig.update_layout(barmode='group',height=390,legend=dict(orientation='h'))
    st.plotly_chart(fig,use_container_width=True)
    st.dataframe(veh[['filial','tipo','frota_atual','capacidade_unitaria','share','veiculos_adicionais']], hide_index=True,use_container_width=True)

elif page == 'Financeiro e EBITDA':
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Receita projetada', fmt_currency(revenue_final), f"{(revenue_final/revenue_base-1)*100:+.1f}%")
    c2.metric('Margem contribuição', fmt_currency(margin_final))
    c3.metric('Custos incrementais', fmt_currency(people_cost+vehicle_cost))
    c4.metric('EBITDA projetado', fmt_currency(eb_proj), f"{(eb_proj/eb_base-1)*100:+.1f}%")
    labels=['EBITDA base','Variação de margem','Pessoas','Veículos','EBITDA projetado']
    vals=[eb_base,margin_final-margin_base,-people_cost,-vehicle_cost,eb_proj]
    measure=['absolute','relative','relative','relative','total']
    fig=go.Figure(go.Waterfall(x=labels,y=vals,measure=measure,connector={'line':{'color':'#9CA3AF'}}))
    fig.update_layout(height=420,showlegend=False)
    st.plotly_chart(fig,use_container_width=True)
    fin = month.copy(); fin['receita']=fin.demanda_final*fin.receita_caixa; fin['margem']=fin.receita*fin.margem_pct
    st.dataframe(fin.groupby('filial',as_index=False)[['receita','margem']].sum(),hide_index=True,use_container_width=True)

else:
    st.info('Esta página representa a camada de governança que deverá persistir inputs, responsáveis, justificativas, vigência e aprovação.')
    tabs=st.tabs(['Piso por filial','Produtividade','Frota','Auditoria'])
    with tabs[0]:
        st.data_editor(pd.DataFrame({'filial':selected_filiais,'piso_demanda_pct':[floor_pct]*len(selected_filiais),'responsável':['Inteligência de Mercado']*len(selected_filiais),'status':['Aprovado']*len(selected_filiais)}),hide_index=True,use_container_width=True)
    with tabs[1]: st.data_editor(people[people.filial.isin(selected_filiais)],hide_index=True,use_container_width=True)
    with tabs[2]: st.data_editor(vehicles[vehicles.filial.isin(selected_filiais)],hide_index=True,use_container_width=True)
    with tabs[3]:
        st.dataframe(pd.DataFrame({'data_hora':['23/07/2026 09:15','23/07/2026 09:24','23/07/2026 09:41'],'usuário':['Comercial','Operações','Finanças'],'campo':['override_pct','produtividade','custo_veículo'],'anterior':['0%','64 cx/h','R$ 720'],'novo':['4%','67 cx/h','R$ 740'],'status':['Aprovado','Pendente','Aprovado']}),hide_index=True,use_container_width=True)

st.divider()
st.caption('Protótipo conceitual — dados sintéticos. Próxima etapa: separar dados, motor, páginas e persistência de cenários.')
