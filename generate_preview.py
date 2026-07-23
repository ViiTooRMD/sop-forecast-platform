from __future__ import annotations

import sys
import types
from pathlib import Path

import pandas as pd

# Allow preview generation in environments without Streamlit.
if "streamlit" not in sys.modules:
    st = types.ModuleType("streamlit")
    st.cache_data = lambda *a, **k: (lambda f: f)
    st.session_state = {}
    sys.modules["streamlit"] = st

from src.data import build_demo_data
from src.engine import run_full_scenario, calculate_accuracy
from src.formatting import compact_number, currency_br, number_br, pct_br, signed_number


def polyline(values, width=520, height=145, pad=15):
    vals = list(values)
    low, high = min(vals), max(vals)
    span = high-low or 1
    pts=[]
    for i,v in enumerate(vals):
        x=pad+i*(width-2*pad)/(len(vals)-1)
        y=height-pad-(v-low)/span*(height-2*pad)
        pts.append(f"{x:.1f},{y:.1f}")
    return " ".join(pts)


data=build_demo_data()
res=run_full_scenario(data,"Cenário Base","Proporcional")
fin=res.financial
acc=calculate_accuracy(data["demand"])
monthly=res.demand.assign(mes=res.demand.data.dt.to_period("M").dt.to_timestamp()).groupby("mes",as_index=False).agg(volume=("demanda_final_caixas","sum"))
people=res.people_monthly
first3=sorted(people.mes.unique())[:3]
p3=people[people.mes.isin(first3)]
current=people.groupby(["filial","processo","funcao"]).fte_atual.first().groupby("funcao").sum()
suggested=p3.groupby(["filial","processo","funcao"]).fte_sugerido.max().groupby("funcao").sum()
rows=[]
for fn in ["Ajudante","Conferente"]:
    rows.append((fn,int(current.get(fn,0)),int(suggested.get(fn,0)),int(suggested.get(fn,0)-current.get(fn,0))))

decisions=[
    ("Aprovar cobertura de FTE","Operações / RH","D+5","Pendente"),
    ("Contratar frota flexível","Frota","D+7","Em análise"),
    ("Revisar restrições comerciais","Comercial","D+2","Em análise"),
    ("Validar impacto EBITDA","Finanças","D+3","Pendente"),
]

html=f'''<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}} body{{margin:0;font-family:Segoe UI,Arial;background:#f5f7fb;color:#122044;font-size:12px}}
.sidebar{{position:fixed;left:0;top:0;bottom:0;width:220px;background:linear-gradient(#071d49,#061638);color:white;padding:18px 13px}}
.logo{{text-align:center;font-size:24px;font-weight:800;letter-spacing:2px;margin:8px 0 25px}}.logo small{{display:block;font-size:8px;letter-spacing:4px;color:#afc7ee;margin-top:5px}}
.nav{{padding:9px 10px;border-radius:7px;margin:4px 0;color:#d7e5fb;font-weight:600}}.nav.active{{background:#1768d9;color:white}}
.main{{margin-left:220px;padding:15px 18px;width:1380px}} h1{{font-size:22px;margin:0 0 3px;color:#071d49}} .sub{{font-size:10px;color:#6b7893;margin-bottom:10px}}
.filters{{height:55px;background:white;border:1px solid #dce4f1;border-radius:10px;display:flex;gap:10px;padding:8px 10px;margin-bottom:10px}}
.filter{{width:180px}} .filter b{{font-size:8px;text-transform:uppercase;color:#53617b}} .select{{border:1px solid #dce4f1;border-radius:6px;padding:7px;margin-top:3px;font-size:10px}}
.grid6{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}} .card{{background:white;border:1px solid #dce4f1;border-radius:10px;padding:11px 12px;height:105px;box-shadow:0 2px 8px rgba(22,52,94,.05);position:relative}}
.card:before{{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:#1664d9}}.label{{font-size:8px;font-weight:800;text-transform:uppercase;color:#45536d;min-height:22px}}.value{{font-size:21px;font-weight:800;color:#071d49;margin-top:5px}}.cap{{font-size:8px;color:#6b7893;margin-top:5px}}
.panels{{display:grid;grid-template-columns:1.35fr .72fr 1.05fr;gap:8px;margin-top:9px}} .panel{{background:white;border:1px solid #dce4f1;border-radius:10px;padding:10px;height:285px}}
.title{{font-size:11px;font-weight:800;color:#071d49;margin-bottom:3px}}.caption{{font-size:8px;color:#6b7893;margin-bottom:8px}}
table{{width:100%;border-collapse:collapse;font-size:9px}} th{{background:#f5f8fd;color:#60708f;font-size:7px;text-transform:uppercase;padding:7px;text-align:right}}th:first-child,td:first-child{{text-align:left}}td{{padding:8px 7px;border-bottom:1px solid #edf1f7;text-align:right}}tr:last-child td{{font-weight:800;background:#f8fafd}}
.lower{{display:grid;grid-template-columns:1.4fr .6fr;gap:8px;margin-top:8px}}.lowpanel{{background:white;border:1px solid #dce4f1;border-radius:10px;padding:10px;height:190px}}
.water{{display:flex;align-items:flex-end;height:175px;gap:18px;padding:20px 14px 20px}} .bar{{width:42px;background:#83aeeb;position:relative}}.bar.red{{background:#e44747}}.bar.green{{background:#28a875}}.bar span{{position:absolute;bottom:-18px;font-size:7px;width:70px;left:-14px;text-align:center}}
.decision td{{padding:9px 7px}}
</style></head><body>
<div class="sidebar"><div class="logo">SN<span style="color:#4aa3ff">O</span>P<small>SINALPI</small></div>
<div class="nav active">▥ &nbsp;Resumo Executivo</div><div class="nav">♟ &nbsp;Demanda & Restrições</div><div class="nav">♙ &nbsp;Capacidade de Pessoas</div><div class="nav">▰ &nbsp;Frota & Veículos</div><div class="nav">$ &nbsp;Financeiro & EBITDA</div><div class="nav">⚙ &nbsp;Premissas & Governança</div>
<div style="border-top:1px solid rgba(255,255,255,.15);margin-top:24px;padding-top:15px;color:#afc7ee;font-size:9px;line-height:1.8"><b style="color:white">Data-base:</b> 31/07/2026<br><b style="color:white">Horizonte:</b> 12 meses<br><b style="color:white">Unidade:</b> caixas<br><b style="color:white">Filiais:</b> 8</div></div>
<div class="main"><h1>1. RESUMO EXECUTIVO</h1><div class="sub">Consolidação das decisões de demanda, capacidade e resultado do ciclo.</div>
<div class="filters"><div class="filter"><b>Cenário</b><div class="select">Cenário Base ▾</div></div><div class="filter"><b>Filial</b><div class="select">Todas ▾</div></div><div class="filter"><b>Período</b><div class="select">Próximos 12 meses ▾</div></div><div class="filter"><b>Data-base</b><div class="select">31/07/2026</div></div><div class="filter" style="margin-left:auto;width:100px"><b>&nbsp;</b><div class="select" style="text-align:center;color:#1664d9;font-weight:700">Exportar ↓</div></div></div>
<div class="grid6">
<div class="card"><div class="label">MAPE do modelo</div><div class="value">{pct_br(acc['mape'])}</div><div class="cap">Últimos 12 meses</div></div>
<div class="card"><div class="label">Demanda projetada (ajustada)</div><div class="value">{compact_number(fin['volume_final'],1)}</div><div class="cap">Caixas nos próximos 12 meses</div></div>
<div class="card"><div class="label">Headcount sugerido (próx. 3 meses)</div><div class="value">{signed_number(sum(r[3] for r in rows))}</div><div class="cap">Ajudantes + conferentes</div></div>
<div class="card"><div class="label">Hora extra necessária</div><div class="value">{number_br(p3.he_horas.sum())} h</div><div class="cap">Próximos três meses</div></div>
<div class="card"><div class="label">Terceiros necessários</div><div class="value">{number_br(p3.terceiro_horas.sum())} h</div><div class="cap">Após limite de HE</div></div>
<div class="card"><div class="label">Impacto no custo total</div><div class="value">{currency_br(fin['custo_incremental_total'],1,compact=True)}</div><div class="cap">Horizonte selecionado</div></div>
</div>
<div class="panels"><div class="panel"><div class="title">Demanda ajustada (caixas) — próximos 12 meses</div><div class="caption">Histórico, previsão estatística e projeção consensada</div><svg width="100%" height="205" viewBox="0 0 520 145"><line x1="15" y1="130" x2="505" y2="130" stroke="#dce4f1"/><polyline fill="none" stroke="#1664d9" stroke-width="3" points="{polyline(monthly.volume)}"/><polyline fill="none" stroke="#a9b6cb" stroke-width="2" points="{polyline(monthly.volume*0.96)}"/>{''.join(f'<circle cx="{15+i*(490)/(len(monthly)-1):.1f}" cy="{(polyline(monthly.volume).split()[i].split(",")[1])}" r="3" fill="#1664d9"/>' for i in range(len(monthly)))}</svg></div>
<div class="panel"><div class="title">Resumo de headcount (FTE)</div><div class="caption">Necessidade máxima dos próximos três meses</div><table><tr><th>Função</th><th>Atual</th><th>Sugerido</th><th>Dif.</th></tr>{''.join(f'<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td style="color:{"#e44747" if r[3]>0 else "#28a875"}">{r[3]:+d}</td></tr>' for r in rows)}<tr><td>Total</td><td>{sum(r[1] for r in rows)}</td><td>{sum(r[2] for r in rows)}</td><td>{sum(r[3] for r in rows):+d}</td></tr></table><div class="title" style="margin-top:13px">Custos de cobertura</div><table><tr><td>Hora extra</td><td>{currency_br(fin['custo_he'])}</td></tr><tr><td>Terceiros</td><td>{currency_br(fin['custo_terceiro'])}</td></tr><tr><td>Frota adicional</td><td>{currency_br(fin['custo_frota'])}</td></tr></table></div>
<div class="panel"><div class="title">Impacto no EBITDA</div><div class="caption">Ponte do resultado base até o cenário projetado</div><div class="water"><div class="bar" style="height:145px"><span>EBITDA atual</span></div><div class="bar red" style="height:45px"><span>Δ Margem</span></div><div class="bar red" style="height:80px"><span>Pessoas</span></div><div class="bar green" style="height:22px"><span>Frota</span></div><div class="bar green" style="height:15px"><span>Outros</span></div><div class="bar" style="height:70px"><span>EBITDA projetado</span></div></div></div></div>
<div class="lower"><div class="lowpanel"><div class="title">Decisões executivas do ciclo</div><table class="decision"><tr><th>Decisão</th><th>Responsável</th><th>Prazo</th><th>Status</th></tr>{''.join(f'<tr><td>{d[0]}</td><td>{d[1]}</td><td>{d[2]}</td><td>{d[3]}</td></tr>' for d in decisions)}</table></div><div class="lowpanel"><div class="title">Status do cenário</div><table><tr><td>Demanda consensada</td><td style="color:#28a875">Concluído</td></tr><tr><td>Piso por filial aplicado</td><td style="color:#28a875">Concluído</td></tr><tr><td>Capacidade calculada</td><td style="color:#28a875">Concluído</td></tr><tr><td>Frota dimensionada</td><td style="color:#28a875">Concluído</td></tr><tr><td>Conciliação financeira</td><td style="color:#f2a91b">Pendente</td></tr></table></div></div>
</div></body></html>'''
Path('/mnt/data/sop_streamlit_v2/PREVIA_LAYOUT.html').write_text(html,encoding='utf-8')
print('/mnt/data/sop_streamlit_v2/PREVIA_LAYOUT.html')
