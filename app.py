from __future__ import annotations

import pandas as pd
import streamlit as st

from src.components import render_logo, scenario_note
from src.data import initialize_state
from src.pages import render_selected_page
from src.theme import inject_global_css


st.set_page_config(
    page_title="S&OP Sinalpi",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "Plataforma demonstrativa de S&OP — Sinalpi",
    },
)

initialize_state()
inject_global_css()

PAGES = [
    "Resumo Executivo",
    "Demanda & Restrições",
    "Capacidade de Pessoas",
    "Frota & Veículos",
    "Financeiro & EBITDA",
    "Premissas & Governança",
]
PAGE_LABELS = {
    "Resumo Executivo": "▥  Resumo Executivo",
    "Demanda & Restrições": "♟  Demanda & Restrições",
    "Capacidade de Pessoas": "♙  Capacidade de Pessoas",
    "Frota & Veículos": "▰  Frota & Veículos",
    "Financeiro & EBITDA": "$  Financeiro & EBITDA",
    "Premissas & Governança": "⚙  Premissas & Governança",
}

with st.sidebar:
    render_logo()
    st.markdown('<div class="sidebar-section-title">Navegação</div>', unsafe_allow_html=True)
    selected = st.radio(
        "Navegação",
        PAGES,
        index=PAGES.index(st.session_state.selected_page),
        format_func=lambda value: PAGE_LABELS[value],
        label_visibility="collapsed",
        key="navigation_radio_v2",
    )
    st.session_state.selected_page = selected

    st.divider()
    st.markdown('<div class="sidebar-section-title">Informações do ciclo</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="padding:0 7px;color:#AFC7EE;font-size:10px;line-height:1.6">
          <div><b style="color:white">Data-base:</b> 31/07/2026</div>
          <div><b style="color:white">Horizonte:</b> 12 meses</div>
          <div><b style="color:white">Unidade:</b> caixas</div>
          <div><b style="color:white">Filiais:</b> 8</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    scenario_note(st.session_state.scenario, st.session_state.last_recalculation)

render_selected_page()
