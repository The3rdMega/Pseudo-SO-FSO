from process import Process

class ResourceManager:
    """Administra a alocação de recursos garantindo uso exclusivo."""
    def __init__(self):
        self.scanners = 1 # 1 scanner disponível.
        self.printers = 2 # 2 impressoras disponíveis.
        self.modems = 1   # 1 modem disponível.
        self.sata_devices = 2 # 2 dispositivos SATA disponíveis.

    def request(self, process: Process) -> bool:
        """
        Tenta alocar recursos. Não há preempção na alocação de I/O.
        Processos de tempo real não precisam de recursos de I/O.
        """
        pass

    def release(self, process: Process) -> None:
        """Libera todos os recursos segurados pelo processo."""
        pass