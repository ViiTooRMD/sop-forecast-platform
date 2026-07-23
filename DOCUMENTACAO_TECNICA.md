# Documentação funcional e técnica — S&OP Sinalpi V2

## 1. Finalidade

A aplicação foi estruturada para funcionar como uma torre de controle de S&OP. O fluxo lógico é único e integrado:

```text
previsão estatística
→ override comercial
→ restrição de cliente
→ aplicação do piso mínimo por filial
→ demanda final consensada
→ passagem por coleta/transbordo/entrega
→ capacidade de pessoas
→ capacidade de veículos
→ custos incrementais
→ EBITDA projetado
```

Uma alteração em qualquer premissa recalcula as etapas posteriores. O aplicativo não é apenas um dashboard: ele é um simulador de cenários.

---

## 2. Arquitetura do código

### `app.py`

- Configura a página.
- Inicializa dados e estado da sessão.
- Aplica o tema visual.
- Monta a navegação lateral customizada.
- Direciona para a página selecionada.

A navegação foi criada com `st.radio` em vez da navegação multipágina padrão para permitir maior controle visual e reproduzir o menu lateral azul do mockup.

### `src/data.py`

Responsável por:

- Constantes de filiais, funções, processos, veículos e cenários.
- Geração da base demonstrativa.
- Inicialização de `st.session_state`.
- Exportação de tabelas para Excel e CSV.

Na implantação real, `build_demo_data()` deve ser substituída por uma camada de leitura do BigQuery, banco SQL, arquivos ou APIs.

### `src/engine.py`

Contém o motor de cálculo. Não possui elementos visuais.

Principais funções:

- `calculate_accuracy()`
- `apply_demand_scenario()`
- `build_process_flow()`
- `calculate_people_capacity()`
- `build_people_monthly_plan()`
- `historical_delivery_reference()`
- `calculate_vehicle_capacity()`
- `calculate_financials()`
- `run_full_scenario()`

### `src/pages.py`

Monta as seis telas e conecta filtros, tabelas, gráficos e editores às funções do motor.

### `src/charts.py`

Centraliza todos os gráficos Plotly, garantindo:

- Fundo branco.
- Paleta azul, verde, laranja e vermelho.
- Legendas compactas.
- Fontes menores.
- Mesma altura e margens.
- Ausência da barra de ferramentas Plotly.

### `src/components.py`

Componentes HTML reutilizáveis:

- Logo.
- Cards de KPI.
- Cabeçalhos.
- Tabelas executivas.
- Legendas de status.
- Avisos metodológicos.

### `src/theme.py`

CSS global da aplicação. É o arquivo principal para ajustes visuais.

---

## 3. Estrutura das bases

## 3.1 Base de demanda

Granularidade:

```text
data + cliente + origem + destino
```

Campos utilizados:

| Campo | Uso |
|---|---|
| `data` | Dia da operação ou previsão |
| `data_base_modelo` | Versão temporal da previsão |
| `periodo` | Histórico ou previsão |
| `cliente` | Chave comercial |
| `segmento` | Agrupamento comercial |
| `tipo_negocio` | B2B ou B2C |
| `b2c_pct` | Participação B2C do cliente |
| `prioridade` | Estratégico, alta, média ou baixa |
| `origem` | Filial de coleta |
| `destino` | Filial de entrega |
| `rota` | Origem concatenada com destino |
| `previsao_modelo_caixas` | Resultado estatístico |
| `realizado_caixas` | Volume histórico |
| `limite_inferior_caixas` | Intervalo inferior |
| `limite_superior_caixas` | Intervalo superior |
| `receita_por_caixa` | Valorização do volume |
| `margem_contrib_pct` | Rentabilidade incremental |
| `sla_alvo_pct` | Nível de serviço contratado |
| `custo_servir_indice` | Índice comparativo do custo de servir |

## 3.2 Base de restrições

Granularidade:

```text
filial + cliente + vigência
```

Campos:

- Override percentual.
- Restrição percentual.
- Limite diário em caixas.
- Indicador de aplicação.
- Motivo.
- Vigência.
- B2C.
- Prioridade.
- Receita e margem.

## 3.3 Premissas por filial

- Piso mínimo percentual da demanda.
- Fator de transbordo.
- Capacidade física de coleta.
- Capacidade física de transbordo.
- Capacidade física de entrega.

As capacidades físicas são referências adicionais. O dimensionamento principal de capacidade é calculado por pessoas.

## 3.4 Premissas de pessoas

Granularidade:

```text
filial + processo + função
```

Processos:

- Coleta.
- Transbordo.
- Entrega.

Funções:

- Ajudante.
- Conferente.

Campos:

- FTE atual.
- Produtividade por hora.
- Horas produtivas.
- Eficiência.
- Absenteísmo.
- Limite de hora extra.
- Custo mensal.
- Custo de HE.
- Custo de terceiro.
- Lead time.
- Curva de aprendizado.

## 3.5 Premissas de veículos

Granularidade:

```text
filial + tipo de veículo
```

Campos:

- Drop size.
- Paradas por viagem.
- Viagens por dia.
- Ocupação.
- Disponibilidade.
- Frota atual.
- Custo diário.
- Percentual de apropriação do novo volume.
- Tipo de contratação.

## 3.6 Premissas financeiras

- Dias úteis.
- Custo de contratação.
- Custo de desligamento.
- Outros custos variáveis.
- EBITDA base mensal.
- Impostos.
- Custo variável por caixa.

---

## 4. Regras da demanda

## 4.1 Multiplicador de cenário

```text
previsão do cenário = previsão do modelo × multiplicador de demanda
```

## 4.2 Override comercial

```text
demanda após override = previsão do cenário × (1 + override / 100)
```

O override pode ser positivo ou negativo.

## 4.3 Restrição efetiva

A restrição do cliente pode ser ampliada pelo cenário, especialmente para B2C.

```text
restrição efetiva = restrição do cliente + restrição B2C adicional do cenário
```

A restrição é limitada entre 0% e 100%.

## 4.4 Limite diário

```text
demanda após restrição = mínimo(
    demanda após override × (1 - restrição efetiva),
    limite diário, quando informado
)
```

## 4.5 Piso por filial

```text
piso em caixas = demanda após override da filial × piso percentual
```

```text
demanda final da filial = máximo(
    demanda após restrições,
    piso em caixas
)
```

A demanda final não pode ultrapassar a demanda disponível antes das restrições.

## 4.6 Métodos de recomposição

Quando o piso é acionado, o volume pode ser recomposto por:

1. **Proporcional:** distribui conforme o volume retirado.
2. **Prioridade estratégica:** atribui maior peso a clientes estratégicos.
3. **Maior margem:** atribui maior peso a clientes mais rentáveis.
4. **B2B primeiro:** prioriza volumes B2B.

---

## 5. Passagem por filial

## 5.1 Coleta

```text
coleta da filial = soma da demanda cuja origem é a filial
```

## 5.2 Entrega

```text
entrega da filial = soma da demanda cujo destino é a filial
```

## 5.3 Transbordo

No MVP:

```text
transbordo = (coleta + entrega) × fator de transbordo da filial
```

Em produção, deve ser substituído por eventos reais de passagem ou cross-docking do TMS.

---

## 6. Capacidade de pessoas

## 6.1 Capacidade unitária

```text
capacidade unitária por FTE/dia =
horas produtivas
× produtividade por hora
× eficiência
× (1 - absenteísmo)
```

## 6.2 Capacidade regular

```text
capacidade regular = FTE atual × capacidade unitária
```

## 6.3 FTE necessário

```text
FTE necessário = demanda do processo / capacidade unitária
```

## 6.4 Hora extra

O volume acima da capacidade regular é convertido em horas extras. A quantidade é limitada pelo número de FTE e pelo limite de HE por pessoa por dia.

## 6.5 Terceiros

O residual após a hora extra é convertido em horas de terceiros.

## 6.6 Recomendação mensal

A necessidade mensal utiliza o percentil 90 dos FTE necessários, reduzindo o efeito de um único pico extremo.

Regras iniciais:

- Gap pequeno e temporário: HE/terceiro.
- Gap superior a 1,5 FTE e recorrente: contratar ou temporarizar.
- Excedente superior a 1,5 FTE: realocar ou reduzir.
- Faixa neutra: manter.

---

## 7. Capacidade de veículos

## 7.1 Referência histórica

A referência de entrega é a média diária dos 90 dias anteriores à data-base.

## 7.2 Capacidade unitária

```text
capacidade unitária diária =
drop size
× paradas por viagem
× viagens por dia
× ocupação
× disponibilidade
```

## 7.3 Volume incremental

```text
volume incremental = demanda futura de entrega - referência histórica
```

- Diferença positiva: novo volume.
- Diferença negativa: possível ociosidade.

## 7.4 Apropriação

O novo volume é distribuído conforme `alocacao_novo_volume_pct`.

A soma por filial deve ser 100%. O motor normaliza a participação durante a simulação, mas a tela apresenta alerta quando a premissa não fecha em 100%.

## 7.5 Frota necessária

```text
frota necessária = teto(demanda do tipo / capacidade unitária)
```

## 7.6 Viagens

```text
viagens demandadas =
demanda apropriada /
(drop size × paradas por viagem × ocupação)
```

```text
capacidade de viagens =
frota atual × viagens por dia × disponibilidade
```

---

## 8. Financeiro e EBITDA

O EBITDA base já contém o custo da estrutura atual. A ponte considera apenas diferenças incrementais.

## 8.1 Receita

```text
receita após override = demanda após override × receita por caixa
```

```text
receita final = demanda final × receita por caixa
```

## 8.2 Margem

```text
margem = receita × margem de contribuição percentual
```

## 8.3 Pessoas

- Gaps temporários: HE e terceiro.
- Gaps recorrentes: FTE adicional.
- Durante mobilização: parte do custo de HE e terceiro continua no primeiro mês.
- Reduções são descontadas, pois nem toda sobra pode ser retirada imediatamente.

## 8.4 Frota

```text
custo incremental de frota = delta de veículos × custo diário × dias
```

O valor pode ser negativo quando o cenário permite devolução ou redução.

## 8.5 EBITDA

```text
impacto EBITDA =
delta de margem
- custos incrementais de pessoas
- custos incrementais de frota
- custos variáveis incrementais
```

```text
EBITDA projetado = EBITDA base + impacto EBITDA
```

---

## 9. Estrutura das telas

## 9.1 Resumo Executivo

- Seis cards principais.
- Demanda histórica versus projetada.
- Resumo de headcount.
- Custos de cobertura.
- Waterfall de EBITDA.
- Tabela de decisões executivas.
- Status do cenário.

## 9.2 Demanda e Restrições

- Visão consolidada semelhante ao mockup.
- Gráfico detalhado de demanda e piso.
- Acurácia por filial.
- Passagem por filial.
- Editor de restrições e overrides.
- Impacto por cliente.

## 9.3 Pessoas

- Cards operacionais.
- Demanda versus capacidade diária.
- FTE mensal.
- Resumo de headcount.
- Plano mensal por filial.
- Detalhamento diário.
- Editor de premissas.

## 9.4 Veículos

- Cards de frota.
- Tabela de drop size.
- Demanda versus capacidade em viagens.
- Frota sugerida.
- Plano por filial e tipo.
- Editor da apropriação do novo volume.
- Metodologia.

## 9.5 Financeiro

- Cards financeiros.
- Tabela atual versus projetado.
- Waterfall.
- Comparação de cenários.
- Ponte detalhada.
- Resultado por filial.
- Editor de premissas.

## 9.6 Premissas e Governança

- Piso e passagem.
- Configuração dos cenários.
- Qualidade dos dados.
- Dicionário de inputs.
- Workflow de aprovação.
- Auditoria.
- Exportação e restauração.

---

## 10. Persistência em produção

O MVP usa `st.session_state`. A versão produtiva deve possuir tabelas como:

- `scenario_header`
- `scenario_version`
- `scenario_status`
- `forecast_base`
- `commercial_override`
- `customer_restriction`
- `branch_floor`
- `people_premise`
- `vehicle_premise`
- `financial_premise`
- `scenario_result`
- `scenario_audit`

Cada alteração deve registrar:

- Usuário.
- Data e hora.
- Cenário e versão.
- Valor anterior.
- Valor novo.
- Justificativa.
- Vigência.
- Status.
- Aprovador.

---

## 11. Ordem de implantação

1. Homologar dicionário de dados.
2. Integrar histórico e previsão.
3. Validar passagem por filial.
4. Medir produtividade real.
5. Homologar custos de pessoas.
6. Medir drop size por veículo.
7. Homologar custos de frota.
8. Integrar DRE e margem.
9. Implantar persistência de cenários.
10. Implantar workflow e auditoria.
11. Testar reconciliações.
12. Publicar e treinar usuários.
