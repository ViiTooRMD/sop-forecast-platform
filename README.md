# S&OP Forecast Platform

Protótipo navegável em Streamlit para direcionar o desenvolvimento da plataforma de S&OP.

## O que esta versão demonstra

- Resumo executivo com demanda consensada, receita em risco, gap de FTE, frota e EBITDA.
- Etapa de consenso de demanda com override comercial, restrições e piso por filial.
- Capacidade operacional de pessoas por coleta, transbordo e entrega.
- Capacidade de frota e necessidade estimada de veículos adicionais.
- Conciliação financeira com waterfall de EBITDA.
- Camada simulada de premissas, governança e auditoria.
- Cenários Base, Peak Season, Otimista e Conservador.

Todos os dados são sintéticos e existem apenas para validar a experiência, a navegação e o encadeamento das decisões.

## Executar localmente

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Direcionamento de arquitetura

A próxima evolução deve separar o protótipo em:

```text
pages/          # jornadas e telas
src/data.py     # integrações e contratos de dados
src/engine.py   # regras de demanda, capacidade e financeiro
src/ui.py       # componentes visuais
src/models.py   # entidades de cenário, aprovação e auditoria
tests/          # testes unitários e reconciliação
```

## Roadmap recomendado

1. Validar conceitos e UX com Comercial, Operações e Finanças.
2. Substituir dados sintéticos pela camada de leitura do BigQuery.
3. Versionar cenários e overrides em banco.
4. Implementar workflow Comercial → Operações → Finanças → Executivo.
5. Criar autenticação, perfis, trilha de auditoria e aprovação.
6. Automatizar testes de reconciliação antes da publicação executiva.
