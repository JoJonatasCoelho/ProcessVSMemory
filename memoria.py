import threading
from collections import deque

class GerenciadorMemoria:
    def __init__(self, capacidade: int, algoritmo: str = "lru", sequencia_futura: list = None, verbose: bool = True):
        self.capacidade = capacidade
        self.algoritmo = algoritmo.lower()
        self.verbose = verbose
        self.memoria: list = []
        self._ordem_fifo: deque = deque()
        self._sequencia_futura: list = list(sequencia_futura) if sequencia_futura else []
        self._cursor_futuro: int = 0
        self.page_faults_totais = 0
        self.hits_totais = 0
        self._lock = threading.Lock()
        self._log: list = []

    def _registrar(self, msg: str):
        self._log.append(msg)
        if self.verbose:
            print(msg)

    def _remover_lru(self, rastreio_lru: list):
        removida = rastreio_lru.pop(0)
        self.memoria.remove(removida)
        return removida

    def _remover_fifo(self):
        removida = self._ordem_fifo.popleft()
        self.memoria.remove(removida)
        return removida

    def _remover_opt(self):
        futuro = self._sequencia_futura[self._cursor_futuro:]
        mais_distante = None
        maior_distancia = -1
        for pagina in self.memoria:
            try:
                dist = futuro.index(pagina)
            except ValueError:
                return pagina
            if dist > maior_distancia:
                maior_distancia = dist
                mais_distante = pagina
        self.memoria.remove(mais_distante)
        return mais_distante

    def requisitar_pagina(self, processo, pagina):
        id_pagina = f"P{processo.pid}_Pag{pagina}"

        with self._lock:
            self._registrar(f"[Thread-{processo.pid}] requisita {id_pagina}")
            self._cursor_futuro += 1

            if id_pagina in self.memoria:
                if self.algoritmo == "lru":
                    self._ordem_fifo = deque(
                        p for p in self._ordem_fifo if p != id_pagina
                    )
                    self._ordem_fifo.append(id_pagina)
                self.hits_totais += 1
                processo.registrar_hit()
                self._registrar(f"  -> HIT  | Memória: {self.memoria}")
            else:
                self.page_faults_totais += 1
                processo.registrar_fault()
                self._registrar(f"  -> FAULT | [{self.algoritmo.upper()}] buscando do disco...")

                if len(self.memoria) >= self.capacidade:
                    if self.algoritmo == "lru":
                        removida = self._ordem_fifo.popleft()
                        self.memoria.remove(removida)
                    elif self.algoritmo == "fifo":
                        removida = self._remover_fifo()
                    elif self.algoritmo == "opt":
                        removida = self._remover_opt()
                    self._registrar(f"     * [{self.algoritmo.upper()}] removeu: {removida}")

                self.memoria.append(id_pagina)
                self._ordem_fifo.append(id_pagina)
                self._registrar(f"  -> Memória: {self.memoria}")

    def resumo(self):
        total = self.page_faults_totais + self.hits_totais
        return {
            "algoritmo": self.algoritmo.upper(),
            "capacidade": self.capacidade,
            "faults_totais": self.page_faults_totais,
            "hits_totais": self.hits_totais,
            "total_acessos": total,
            "taxa_fault_global": self.page_faults_totais / total if total > 0 else 0.0,
        }

    def get_log(self):
        return list(self._log)
