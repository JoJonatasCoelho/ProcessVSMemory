import threading
import copy
from processo import Processo
from memoria import GerenciadorMemoria
from workload import gerar_workload_realista, sequencia_flat

ALGORITMOS = ["lru", "fifo", "opt"]

def _worker(processo: Processo, gerenciador: GerenciadorMemoria):
    while True:
        pagina = processo.proxima_pagina()
        if pagina is None:
            break
        gerenciador.requisitar_pagina(processo, pagina)

def executar_simulacao(capacidade_memoria: int, definicoes_processos: list, algoritmo: str = "lru", verbose: bool = True):
    seq_futura = sequencia_flat(definicoes_processos)
    gerenciador = GerenciadorMemoria(capacidade=capacidade_memoria, algoritmo=algoritmo, sequencia_futura=seq_futura, verbose=verbose)
    processos = [Processo(pid=d["pid"], paginas_requisitadas=d["paginas"]) for d in definicoes_processos]

    threads = [
        threading.Thread(target=_worker, args=(p, gerenciador), name=f"Thread-P{p.pid}", daemon=True)
        for p in processos
    ]

    if verbose:
        print(f"\n=== [{algoritmo.upper()}] Memória: {capacidade_memoria} frames | Threads: {[t.name for t in threads]} ===\n")

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return gerenciador, processos

def imprimir_resultados(gerenciador: GerenciadorMemoria, processos: list):
    r = gerenciador.resumo()
    print("\n" + "=" * 60)
    print(f"RESULTADOS — {r['algoritmo']} | {r['capacidade']} frames")
    print("=" * 60)
    print(f"  Total de acessos     : {r['total_acessos']}")
    print(f"  Page Faults globais  : {r['faults_totais']}")
    print(f"  Hits globais         : {r['hits_totais']}")
    print(f"  Taxa de fault global : {r['taxa_fault_global']:.2%}")
    print("-" * 60)
    for p in processos:
        print(f"  {p}")
    print("=" * 60)


if __name__ == "__main__":
    definicoes = gerar_workload_realista(n_processos=6, n_acessos=80, n_paginas_universo=20, seed=42)

    for alg in ALGORITMOS:
        defs = copy.deepcopy(definicoes)
        ger, procs = executar_simulacao(capacidade_memoria=5, definicoes_processos=defs, algoritmo=alg, verbose=False)
        imprimir_resultados(ger, procs)
