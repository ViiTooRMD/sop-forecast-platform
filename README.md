# S&OP Sinalpi — Streamlit V2

Versão reformulada para reproduzir a estrutura visual do mockup aprovado e ampliar o detalhamento funcional.

## Principais diferenças em relação ao protótipo anterior

- Layout branco e azul, compacto e corporativo.
- Menu lateral azul-marinho semelhante ao mockup.
- Sem cabeçalho gradiente grande.
- Cards de indicadores menores e alinhados.
- Filtros horizontais no topo de cada tela.
- Gráficos com fundo branco, legenda compacta e paleta padronizada.
- Visão consolidada de demanda com três blocos lado a lado.
- Página de pessoas com gráfico diário, gráfico mensal e resumo de headcount.
- Página de frota com drop size, demanda versus capacidade em viagens e frota sugerida.
- Página financeira com resumo, waterfall e comparação de cenários.
- Editores detalhados para restrições, produtividade, frota, custos e piso.
- Motor integrado de demanda → pessoas → veículos → EBITDA.

## Telas

1. Resumo Executivo.
2. Demanda & Restrições B2C.
3. Capacidade de Pessoas.
4. Frota & Veículos.
5. Financeiro & EBITDA.
6. Premissas & Governança.

## Regra de demanda

```text
previsão do cenário = previsão do modelo × multiplicador do cenário

demanda após override = previsão do cenário × (1 + override %)

demanda após restrição = menor entre:
- demanda após override × (1 - restrição efetiva %)
- limite diário, quando preenchido

piso em caixas = demanda após override da filial × piso percentual

demanda final da filial = máximo(demanda após restrições, piso em caixas)
```

A recomposição do piso pode ser configurada como:

- Proporcional.
- Prioridade estratégica.
- Maior margem.
- B2B primeiro.

## Regra de pessoas

```text
capacidade unitária FTE/dia =
horas produtivas × produtividade × eficiência × (1 - absenteísmo)

capacidade regular = FTE atual × capacidade unitária

FTE necessário = demanda / capacidade unitária
```

O déficit é coberto na seguinte ordem:

1. Capacidade regular.
2. Hora extra, limitada por FTE/dia.
3. Terceiro.
4. Contratação/temporário quando o gap for recorrente.

## Regra de veículos

```text
capacidade unitária diária =
drop size × paradas/viagem × viagens/dia × ocupação × disponibilidade
```

O novo volume é calculado contra a média diária de entrega dos 90 dias históricos anteriores à data-base. A diferença positiva é apropriada entre os tipos de veículo conforme a tabela de participação por filial.

```text
frota necessária = teto(demanda apropriada / capacidade unitária diária)
```

## Instalação — Windows

Abra o Prompt de Comando na pasta descompactada:

```bat
cd C:\caminho\sop_streamlit_v2
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Instalação — Linux/macOS

```bash
cd /caminho/sop_streamlit_v2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Estrutura

```text
sop_streamlit_v2/
├── app.py
├── requirements.txt
├── README.md
├── DOCUMENTACAO_TECNICA.md
├── .streamlit/config.toml
├── src/
│   ├── data.py
│   ├── engine.py
│   ├── pages.py
│   ├── charts.py
│   ├── components.py
│   ├── formatting.py
│   └── theme.py
└── tests/
    └── test_engine.py
```

## Integração com bases reais

Substitua `build_demo_data()` em `src/data.py` por consultas ou leituras das bases reais. Preserve o dicionário de colunas ou crie uma camada de mapeamento.

Em produção:

- Não use `st.session_state` como banco permanente.
- Salve cenários e alterações em banco relacional.
- Registre usuário, data, valor anterior, valor novo, vigência, motivo e aprovação.
- Faça reconciliação com TMS, RH, contratos de frota e DRE.
- Crie autenticação e perfis de acesso.
