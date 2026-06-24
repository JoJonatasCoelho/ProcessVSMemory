import threading, copy, random
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import ipywidgets as widgets
from IPython.display import display, clear_output

class Processo:
    def __init__(self, pid, paginas):
        self.pid = pid
        self.paginas_requisitadas = deque(paginas)
        self.page_faults = 0
        self.hits = 0
    def proxima_pagina(self): return self.paginas_requisitadas.popleft() if self.paginas_requisitadas else None
    def registrar_fault(self): self.page_faults += 1
    def registrar_hit(self): self.hits += 1
    def total_acessos(self): return self.page_faults + self.hits
    def taxa_fault(self): t = self.total_acessos(); return self.page_faults / t if t > 0 else 0.0
    def __repr__(self): return f"P{self.pid}: faults={self.page_faults} hits={self.hits} taxa={self.taxa_fault():.2%}"

class GerenciadorMemoria:
    def __init__(self, capacidade, algoritmo="lru", seq_futura=None, verbose=True):
        self.capacidade = capacidade
        self.algoritmo = algoritmo.lower()
        self.verbose = verbose
        self.memoria = []
        self._fila = deque()
        self._seq_futura = list(seq_futura) if seq_futura else []
        self._cursor = 0
        self.page_faults_totais = 0
        self.hits_totais = 0
        self._lock = threading.Lock()
        self._log = []

    def _log_(self, msg):
        self._log.append(msg)
        if self.verbose: print(msg)

    def _remover_opt(self):
        futuro = self._seq_futura[self._cursor:]
        mais_longe, maior_dist = None, -1
        for p in self.memoria:
            try: d = futuro.index(p)
            except ValueError: return p
            if d > maior_dist: maior_dist, mais_longe = d, p
        return mais_longe

    def requisitar_pagina(self, processo, pagina):
        id_p = f"P{processo.pid}_Pag{pagina}"
        with self._lock:
            self._cursor += 1
            self._log_(f"[Thread-P{processo.pid}] {id_p}")
            if id_p in self.memoria:
                if self.algoritmo == "lru":
                    self._fila.remove(id_p); self._fila.append(id_p)
                self.hits_totais += 1; processo.registrar_hit()
                self._log_(f"  -> HIT  | {self.memoria}")
            else:
                self.page_faults_totais += 1; processo.registrar_fault()
                self._log_(f"  -> FAULT [{self.algoritmo.upper()}]")
                if len(self.memoria) >= self.capacidade:
                    if self.algoritmo == "lru":   removida = self._fila.popleft(); self.memoria.remove(removida)
                    elif self.algoritmo == "fifo": removida = self._fila.popleft(); self.memoria.remove(removida)
                    elif self.algoritmo == "opt":  removida = self._remover_opt(); self.memoria.remove(removida)
                    self._log_(f"     * removeu: {removida}")
                self.memoria.append(id_p); self._fila.append(id_p)
                self._log_(f"  -> Memória: {self.memoria}")

    def resumo(self):
        t = self.page_faults_totais + self.hits_totais
        return {"algoritmo": self.algoritmo.upper(), "capacidade": self.capacidade,
                "faults_totais": self.page_faults_totais, "hits_totais": self.hits_totais,
                "total_acessos": t, "taxa_fault_global": self.page_faults_totais / t if t > 0 else 0.0}

def _worker(processo, gerenciador):
    while True:
        p = processo.proxima_pagina()
        if p is None: break
        gerenciador.requisitar_pagina(processo, p)

def seq_flat(defs):
    out = []
    for d in defs:
        out.extend([f"P{d['pid']}_Pag{p}" for p in d["paginas"]])
    return out

def rodar(capacidade, defs, algoritmo, verbose=False):
    seq = seq_flat(defs)
    ger = GerenciadorMemoria(capacidade, algoritmo=algoritmo, seq_futura=seq, verbose=verbose)
    procs = [Processo(d["pid"], d["paginas"]) for d in defs]
    threads = [threading.Thread(target=_worker, args=(p, ger), daemon=True) for p in procs]
    for t in threads: t.start()
    for t in threads: t.join()
    return ger, procs

def gerar_workload(n_proc, n_acessos, n_paginas, seed=42):
    rng = random.Random(seed)
    hot = list(range(1, max(2, int(n_paginas * 0.2)) + 1))
    cold = list(range(hot[-1] + 1, n_paginas + 1))
    defs = []
    for pid in range(1, n_proc + 1):
        pags = [rng.choice(hot) if rng.random() < 0.80 else (rng.choice(cold) if cold else rng.choice(hot))
                for _ in range(n_acessos)]
        defs.append({"pid": pid, "paginas": pags})
    return defs

ALGORITMOS = ["lru", "fifo", "opt"]
CORES = {"lru": "#E63946", "fifo": "#457B9D", "opt": "#2A9D8F"}
LABELS = {"lru": "LRU", "fifo": "FIFO", "opt": "OPT (ótimo)"}

def experimento_memoria(defs, capacidades):
    return {alg: [rodar(cap, copy.deepcopy(defs), alg)[0].resumo() for cap in capacidades] for alg in ALGORITMOS}

def experimento_processos(cap, n_acessos, n_paginas, n_lista):
    res = {alg: [] for alg in ALGORITMOS}
    for n in n_lista:
        defs = gerar_workload(n, n_acessos, n_paginas, seed=n)
        for alg in ALGORITMOS:
            r = rodar(cap, copy.deepcopy(defs), alg)[0].resumo()
            r["n_processos"] = n
            res[alg].append(r)
    return res

def plotar(res_mem, res_proc, capacidades, n_lista):
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("LRU × FIFO × OPT — Workload Realista 80/20 com Threads Concorrentes",
                 fontsize=13, fontweight="bold")

    for alg in ALGORITMOS:
        cap = [r["capacidade"] for r in res_mem[alg]]
        axes[0][0].plot(cap, [r["faults_totais"] for r in res_mem[alg]],
                        marker="o", label=LABELS[alg], color=CORES[alg], linewidth=2)
        axes[0][1].plot(cap, [r["taxa_fault_global"] * 100 for r in res_mem[alg]],
                        marker="s", label=LABELS[alg], color=CORES[alg], linewidth=2)

    for ax, titulo, ylabel, fmt in [
        (axes[0][0], "Page Faults × Frames", "Page Faults", None),
        (axes[0][1], "Taxa de Fault (%) × Frames", "Taxa (%)", mtick.PercentFormatter()),
    ]:
        ax.set_title(titulo); ax.set_xlabel("Frames"); ax.set_ylabel(ylabel)
        ax.set_xticks(capacidades); ax.legend(); ax.grid(True, linestyle="--", alpha=0.4)
        if fmt: ax.yaxis.set_major_formatter(fmt)

    x = list(range(len(n_lista))); larg = 0.26
    for i, alg in enumerate(ALGORITMOS):
        off = (i - 1) * larg
        axes[1][0].bar([xi + off for xi in x], [r["faults_totais"] for r in res_proc[alg]],
                       width=larg, label=LABELS[alg], color=CORES[alg], edgecolor="white")
        axes[1][1].bar([xi + off for xi in x], [r["taxa_fault_global"] * 100 for r in res_proc[alg]],
                       width=larg, label=LABELS[alg], color=CORES[alg], edgecolor="white")

    for ax, titulo, ylabel, fmt in [
        (axes[1][0], "Page Faults × Nº Processos Concorrentes", "Page Faults", None),
        (axes[1][1], "Taxa de Fault (%) × Nº Processos Concorrentes", "Taxa (%)", mtick.PercentFormatter()),
    ]:
        ax.set_title(titulo); ax.set_xlabel("Processos"); ax.set_ylabel(ylabel)
        ax.set_xticks(x); ax.set_xticklabels([str(n) for n in n_lista])
        ax.legend(); ax.grid(True, axis="y", linestyle="--", alpha=0.4)
        if fmt: ax.yaxis.set_major_formatter(fmt)

    plt.tight_layout(); plt.show()

def imprimir_tabela(res, chave, label_col):
    print(f"\n{'─'*65}")
    print(f"  {label_col:<10} {'Algoritmo':<8} {'Faults':>8} {'Hits':>8} {'Taxa':>10}")
    print(f"{'─'*65}")
    base = list(res.values())[0]
    for i in range(len(base)):
        for alg in ALGORITMOS:
            r = res[alg][i]
            v = r.get(chave, r.get("capacidade"))
            print(f"  {v:<10} {LABELS[alg]:<8} {r['faults_totais']:>8} {r['hits_totais']:>8} {r['taxa_fault_global']:>9.2%}")
        print(f"{'─'*65}")

sl_frames     = widgets.IntSlider(value=5, min=1, max=14, step=1, description="Frames fixos:", style={"description_width": "120px"})
sl_cap_max    = widgets.IntSlider(value=12, min=3, max=20, step=1, description="Frames máx:", style={"description_width": "120px"})
sl_proc       = widgets.IntSlider(value=6, min=1, max=10, step=1, description="Processos:", style={"description_width": "120px"})
sl_acessos    = widgets.IntSlider(value=80, min=20, max=200, step=10, description="Acessos/proc:", style={"description_width": "120px"})
sl_paginas    = widgets.IntSlider(value=20, min=5, max=50, step=5, description="Universo págs:", style={"description_width": "120px"})
btn           = widgets.Button(description="▶  Rodar Experimentos", button_style="success",
                               layout=widgets.Layout(width="240px", height="36px"))
out           = widgets.Output()

display(widgets.VBox([
    widgets.HTML("<h3>🖥️  LRU × FIFO × OPT — Simulação com Threads Concorrentes</h3>"
                 "<p>Workload <b>realista 80/20</b>: 80% dos acessos em 20% das páginas (hot set).</p>"),
    widgets.HBox([sl_frames, sl_cap_max]),
    widgets.HBox([sl_proc, sl_acessos, sl_paginas]),
    btn, out
]))

def on_click(_):
    with out:
        clear_output(wait=True)
        cap_fixa  = sl_frames.value
        cap_max   = sl_cap_max.value
        n_proc    = sl_proc.value
        n_acessos = sl_acessos.value
        n_paginas = sl_paginas.value
        capacidades = list(range(1, cap_max + 1))
        n_lista     = sorted(set([1, 2, 3, 4, n_proc] + ([6] if n_proc >= 6 else []) + ([8] if n_proc >= 8 else [])))
        n_lista     = [n for n in n_lista if n <= n_proc]

        print(f"Workload: {n_proc} processos × {n_acessos} acessos × {n_paginas} páginas (universo) | seed=42\n")

        defs_base = gerar_workload(n_proc, n_acessos, n_paginas)

        print(">>> Experimento 1: variando capacidade de memória")
        res_mem = experimento_memoria(defs_base, capacidades)
        imprimir_tabela(res_mem, "capacidade", "Frames")

        print("\n>>> Experimento 2: variando nº de processos concorrentes")
        res_proc = experimento_processos(cap_fixa, n_acessos, n_paginas, n_lista)
        imprimir_tabela(res_proc, "n_processos", "Processos")

        plotar(res_mem, res_proc, capacidades, n_lista)

        print(f"\n--- Verbose: {n_proc} processos, {cap_fixa} frames, LRU ---\n")
        ger, procs = rodar(cap_fixa, gerar_workload(n_proc, n_acessos, n_paginas), "lru", verbose=True)
        r = ger.resumo()
        print(f"\nResumo LRU: faults={r['faults_totais']} hits={r['hits_totais']} taxa={r['taxa_fault_global']:.2%}")
        for p in procs: print(f"  {p}")

btn.on_click(on_click)
