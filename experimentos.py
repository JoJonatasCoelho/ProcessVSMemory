import copy
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from simulacao import executar_simulacao, ALGORITMOS
from workload import gerar_workload_realista

CORES = {"lru": "#E63946", "fifo": "#457B9D", "opt": "#2A9D8F"}
LABELS = {"lru": "LRU", "fifo": "FIFO", "opt": "OPT (ótimo)"}

def _rodar(capacidade, definicoes, algoritmo):
    defs = copy.deepcopy(definicoes)
    ger, _ = executar_simulacao(capacidade, defs, algoritmo=algoritmo, verbose=False)
    return ger.resumo()

def experimento_variar_memoria(definicoes, capacidades):
    return {
        alg: [_rodar(cap, definicoes, alg) for cap in capacidades]
        for alg in ALGORITMOS
    }

def experimento_variar_processos(capacidade, n_acessos, n_paginas, seeds):
    resultados = {alg: [] for alg in ALGORITMOS}
    n_lista = sorted(seeds.keys())
    for n in n_lista:
        defs = gerar_workload_realista(n_processos=n, n_acessos=n_acessos, n_paginas_universo=n_paginas, seed=seeds[n])
        for alg in ALGORITMOS:
            r = _rodar(capacidade, defs, alg)
            r["n_processos"] = n
            resultados[alg].append(r)
    return resultados

def plotar_comparacao(res_mem, res_proc, capacidades):
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(
        "LRU × FIFO × OPT — Workload Realista (80/20) com Threads Concorrentes",
        fontsize=13, fontweight="bold"
    )

    for alg in ALGORITMOS:
        cap = [r["capacidade"] for r in res_mem[alg]]
        faults = [r["faults_totais"] for r in res_mem[alg]]
        taxa = [r["taxa_fault_global"] * 100 for r in res_mem[alg]]

        axes[0][0].plot(cap, faults, marker="o", label=LABELS[alg], color=CORES[alg], linewidth=2)
        axes[0][1].plot(cap, taxa, marker="s", label=LABELS[alg], color=CORES[alg], linewidth=2)

    axes[0][0].set_title("Page Faults × Frames (capacidade)")
    axes[0][0].set_xlabel("Frames")
    axes[0][0].set_ylabel("Page Faults")
    axes[0][0].set_xticks(capacidades)
    axes[0][0].legend()
    axes[0][0].grid(True, linestyle="--", alpha=0.4)

    axes[0][1].set_title("Taxa de Fault (%) × Frames")
    axes[0][1].set_xlabel("Frames")
    axes[0][1].set_ylabel("Taxa de Fault (%)")
    axes[0][1].yaxis.set_major_formatter(mtick.PercentFormatter())
    axes[0][1].set_xticks(capacidades)
    axes[0][1].legend()
    axes[0][1].grid(True, linestyle="--", alpha=0.4)

    nproc = [r["n_processos"] for r in res_proc["lru"]]
    x = list(range(len(nproc)))
    largura = 0.26

    for i, alg in enumerate(ALGORITMOS):
        faults_p = [r["faults_totais"] for r in res_proc[alg]]
        taxa_p = [r["taxa_fault_global"] * 100 for r in res_proc[alg]]
        offset = (i - 1) * largura
        axes[1][0].bar([xi + offset for xi in x], faults_p, width=largura, label=LABELS[alg], color=CORES[alg], edgecolor="white")
        axes[1][1].bar([xi + offset for xi in x], taxa_p, width=largura, label=LABELS[alg], color=CORES[alg], edgecolor="white")

    for ax, titulo, ylabel in [
        (axes[1][0], "Page Faults × Nº de Processos Concorrentes", "Page Faults"),
        (axes[1][1], "Taxa de Fault (%) × Nº de Processos Concorrentes", "Taxa de Fault (%)"),
    ]:
        ax.set_title(titulo)
        ax.set_xlabel("Processos")
        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels([str(n) for n in nproc])
        ax.legend()
        ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    axes[1][1].yaxis.set_major_formatter(mtick.PercentFormatter())

    plt.tight_layout()
    plt.savefig("resultados_experimentos.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("[✓] Gráfico salvo: resultados_experimentos.png")

def imprimir_tabela_comparativa(resultados, eixo):
    cabecalho = "Frames" if eixo == "capacidade" else "Processos"
    chave = eixo if eixo == "capacidade" else "n_processos"
    print(f"\n{'─'*70}")
    print(f"  {cabecalho:<10} {'Algoritmo':<8} {'Faults':>8} {'Hits':>8} {'Taxa Fault':>12}")
    print(f"{'─'*70}")
    base_alg = list(resultados.values())[0]
    for i, _ in enumerate(base_alg):
        for alg in ALGORITMOS:
            r = resultados[alg][i]
            val = r.get(chave, r.get("capacidade"))
            print(f"  {val:<10} {LABELS[alg]:<8} {r['faults_totais']:>8} {r['hits_totais']:>8} {r['taxa_fault_global']:>11.2%}")
        print(f"{'─'*70}")


if __name__ == "__main__":
    N_ACESSOS = 80
    N_PAGINAS = 20
    SEED_BASE = 42
    CAPACIDADES = list(range(1, 13))
    CAP_FIXA = 5
    SEEDS_PROC = {1: 42, 2: 43, 3: 44, 4: 45, 6: 46, 8: 47}

    definicoes_base = gerar_workload_realista(n_processos=6, n_acessos=N_ACESSOS, n_paginas_universo=N_PAGINAS, seed=SEED_BASE)

    print(">>> Experimento 1: variando capacidade de memória (6 processos, 80 acessos cada)")
    res_mem = experimento_variar_memoria(definicoes_base, CAPACIDADES)
    imprimir_tabela_comparativa(res_mem, eixo="capacidade")

    print("\n>>> Experimento 2: variando nº de processos (memória fixa = 5 frames, 80 acessos cada)")
    res_proc = experimento_variar_processos(CAP_FIXA, N_ACESSOS, N_PAGINAS, SEEDS_PROC)
    imprimir_tabela_comparativa(res_proc, eixo="n_processos")

    plotar_comparacao(res_mem, res_proc, CAPACIDADES)
