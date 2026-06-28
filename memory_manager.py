from process import Process

class MemoryManager:
    """Módulo de gerência de memória simulando paginação."""
    def __init__(self):
        self.TOTAL_FRAMES = 20 # Tamanho fixo de memória principal de 20 frames.
        self.RT_FRAMES = 8     # 8 frames reservados para processos de tempo real.
        self.USER_FRAMES = 12  # 12 frames para usuários.
        # Frame table implementation here

    def access_page(self, process: Process, page: int) -> bool:
        """
        Simula o acesso à página. 
        Retorna True se houve page hit, False se gerou page fault.
        """
        pass

    def replace_lru(self, process: Process) -> None:
        """Aplica o algoritmo LRU (Least Recently Used) no escopo local."""
        pass