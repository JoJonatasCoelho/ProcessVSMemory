import random

def gerar_workload_realista(n_processos: int, n_acessos: int, n_paginas_universo: int, seed: int = 42) -> list:
    rng = random.Random(seed)
    hot_pages = list(range(1, max(2, int(n_paginas_universo * 0.2)) + 1))
    cold_pages = list(range(hot_pages[-1] + 1, n_paginas_universo + 1))

    definicoes = []
    for pid in range(1, n_processos + 1):
        paginas = []
        for _ in range(n_acessos):
            if rng.random() < 0.80:
                paginas.append(rng.choice(hot_pages))
            else:
                paginas.append(rng.choice(cold_pages) if cold_pages else rng.choice(hot_pages))
        definicoes.append({"pid": pid, "paginas": paginas})
    return definicoes

def sequencia_flat(definicoes: list) -> list:
    seq = []
    for d in definicoes:
        seq.extend([f"P{d['pid']}_Pag{p}" for p in d["paginas"]])
    return seq
