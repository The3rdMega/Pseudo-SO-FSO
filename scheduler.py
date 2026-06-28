from collections import deque
from typing import Optional
from process import Process

class Scheduler:
    """Gerencia as filas de processos e o escalonamento."""
    def __init__(self):
        # A fila de tempo real é gerenciada por FIFO (First In First Out) sem preempção.
        self.real_time_queue: deque[Process] = deque()
        
        # Processos de usuário utilizam três filas com prioridades distintas.
        self.user_queues: list[deque[Process]] = [deque(), deque(), deque()]
        self.quantum = 1 # Processos de usuário podem ser preemptados e o quantum é de 1ms.

    def admit(self, process: Process) -> None:
        """Admite um processo na fila global apropriada."""
        pass

    def next(self) -> Optional[Process]:
        """Retorna o próximo processo a ser executado segundo as regras de escalonamento."""
        pass

    def apply_aging(self) -> None:
        """Modifica a prioridade dos processos para evitar starvation."""
        pass