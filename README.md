# Simulação LRU × FIFO × OPT com Threads Concorrentes

**IFCE – Sistemas Operacionais | Prof. Daniel Ferreira | 2026.1**

Simulação que integra **Gerenciamento de Processos** e **Gerenciamento de Memória**, comparando três algoritmos de substituição de página (LRU, FIFO e OPT) sob carga concorrente real, com workload realista de distribuição 80/20.

---

## Tema

**O Impacto do Escalonamento de Processos na Taxa de Falhas de Página**

Tópicos integrados: Gerenciamento de Processos + Gerenciamento de Memória.

---

## Estrutura do Repositório

```
/
├── processo.py            # Entidade Processo: estado, contadores, taxa de fault
├── memoria.py             # GerenciadorMemoria: LRU + FIFO + OPT + threading.Lock
├── workload.py            # Gerador de workload realista 80/20 (hot/cold pages)
├── simulacao.py           # Engine: threads reais por processo, ponto de entrada para demo
├── experimentos.py        # Experimentos cruzados (frames × processos × algoritmos) + gráficos
├── colab_celula_unica.py  # Versão Colab: célula única, ipywidgets interativos
└── README.md
```

---

## Pré-requisitos

```bash
python3 -m pip install matplotlib
```

`threading`, `random` e `collections` já fazem parte da biblioteca padrão do Python 3.

---

## Como Executar

### Demo completa (3 algoritmos, log visível)

```bash
python simulacao.py
```

### Experimentos com tabelas e gráficos

```bash
python experimentos.py
```

Gera tabelas no terminal e salva `resultados_experimentos.png`.

### Google Colab

Cole o conteúdo de `colab_celula_unica.py` em uma única célula e execute.
Use os sliders para ajustar frames, processos, acessos e universo de páginas em tempo real.

---

## Workload Realista 80/20

Modelado a partir do princípio de localidade temporal: 80% dos acessos de cada processo são direcionados a 20% das páginas disponíveis (hot set). Os 20% restantes acessam páginas frias aleatórias. Isso reproduz o comportamento de aplicações reais e torna a comparação entre LRU, FIFO e OPT significativa.

---

## Concorrência Real

Cada processo roda em uma `threading.Thread` independente. O `GerenciadorMemoria` usa um `threading.Lock` para garantir exclusão mútua em todas as operações sobre a memória compartilhada.

```
Thread-P1 ──┐
Thread-P2 ──┤
Thread-P3 ──┼──► GerenciadorMemoria ( Lock ) ──► Memória [ LRU | FIFO | OPT ]
Thread-P4 ──┤
...         ──┘
```

---

## Parâmetros Configuráveis

Em `simulacao.py` e `experimentos.py`:

| Parâmetro             | Onde                                 | Descrição                                       |
| ---------------------- | ------------------------------------ | ------------------------------------------------- |
| `capacidade_memoria` | `simulacao.py __main__`            | Frames de RAM disponíveis                        |
| `n_processos`        | `workload.gerar_workload_realista` | Número de processos concorrentes                 |
| `n_acessos`          | `workload.gerar_workload_realista` | Acessos por processo                              |
| `n_paginas_universo` | `workload.gerar_workload_realista` | Tamanho do espaço de endereçamento              |
| `CAPACIDADES`        | `experimentos.py __main__`         | Faixa de frames para o Experimento 1              |
| `SEEDS_PROC`         | `experimentos.py __main__`         | Configurações de processos para o Experimento 2 |

---

## Resultados

### Experimento 1 — 6 processos × 80 acessos, variando frames (1–12)

| Frames | LRU Faults | LRU Taxa | FIFO Faults | FIFO Taxa | OPT Faults | OPT Taxa |
| ------ | ---------- | -------- | ----------- | --------- | ---------- | -------- |
| 1      | 399        | 83,12%   | 399         | 83,12%    | 95         | 19,79%   |
| 3      | 274        | 57,08%   | 287         | 59,79%    | 90         | 18,75%   |
| 5      | 164        | 34,17%   | 196         | 40,83%    | 88         | 18,33%   |
| 8      | 112        | 23,33%   | 139         | 28,96%    | 88         | 18,33%   |
| 12     | 92         | 19,17%   | 104         | 21,67%    | 88         | 18,33%   |

Com 1 frame, LRU e FIFO colapsam para o mesmo comportamento. A partir de 3 frames, LRU supera FIFO por explorar localidade temporal. OPT converge com ~5 frames porque o hot set já cabe na memória; a taxa residual de ~18% representa acessos genuinamente a páginas frias.

### Experimento 2 — 5 frames fixos, variando processos (1–8)

| Processos | LRU Faults | LRU Taxa | FIFO Faults | FIFO Taxa | OPT Faults | OPT Taxa |
| --------- | ---------- | -------- | ----------- | --------- | ---------- | -------- |
| 1         | 31         | 38,75%   | 36          | 45,00%    | 15         | 18,75%   |
| 2         | 49         | 30,63%   | 52          | 32,50%    | 26         | 16,25%   |
| 4         | 124        | 38,75%   | 138         | 43,12%    | 58         | 18,12%   |
| 8         | 219        | 34,22%   | 261         | 40,78%    | 116        | 18,12%   |

O volume absoluto de faults cresce com mais processos, mas a taxa se estabiliza — evidência de que a localidade individual de cada processo se preserva mesmo sob alta concorrência. OPT mantém ~18% independente da carga, confirmando que o limite teórico é função da distribuição do workload, não da pressão concorrente.

---

## Critérios Atendidos

| Critério                           | Como é atendido                                                                    |
| ----------------------------------- | ----------------------------------------------------------------------------------- |
| Ambiente replicável                | Python 3 puro +`pip install matplotlib`                                           |
| Dois tópicos integrados            | Gerenciamento de Processos + Gerenciamento de Memória                              |
| Simulação com comportamento claro | Log de cada acesso com estado da memória                                           |
| Casos de teste com entrada/saída   | `simulacao.py` e `experimentos.py` com casos predefinidos                       |
| Métricas de desempenho             | Faults, hits, taxa por processo e global, tabelas e gráficos                       |
| Complexidade da combinação        | Três algoritmos comparados sob concorrência real (threads + lock)                 |
| Implicações arquiteturais         | Working set, localidade temporal, thrashing e limite OPT demonstrados empiricamente |
