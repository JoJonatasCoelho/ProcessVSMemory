from collections import deque

class Processo:
    def __init__(self, pid: int, paginas_requisitadas: list):
        self.pid = pid
        self.paginas_requisitadas = deque(paginas_requisitadas)
        self.page_faults = 0
        self.hits = 0

    def proxima_pagina(self):
        if self.paginas_requisitadas:
            return self.paginas_requisitadas.popleft()
        return None

    def registrar_fault(self):
        self.page_faults += 1

    def registrar_hit(self):
        self.hits += 1

    def total_acessos(self):
        return self.page_faults + self.hits

    def taxa_fault(self):
        total = self.total_acessos()
        return self.page_faults / total if total > 0 else 0.0

    def __repr__(self):
        return (f"Processo(pid={self.pid}, faults={self.page_faults}, "
                f"hits={self.hits}, taxa={self.taxa_fault():.2%})")
