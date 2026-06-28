from dataclasses import dataclass
from process import Process

@dataclass
class File:
    name: str
    start_block: int
    num_blocks: int
    owner_pid: int

class FileSystem:
    """Gerencia a alocação contígua de arquivos no disco."""
    def __init__(self, total_blocks: int):
        self.total_blocks = total_blocks
        self.disk = [0] * total_blocks
        self.files: list[File] = []

    def create(self, process: Process, name: str, blocks: int) -> bool:
        """Aloca espaço no disco usando o algoritmo first-fit."""
        pass

    def delete(self, process: Process, name: str) -> bool:
        """
        Deleta um arquivo. Processos comuns só deletam os próprios,
        processos de tempo real deletam qualquer um.
        """
        pass

    def print_disk_map(self) -> None:
        """Mostra o mapa de ocupação do disco."""
        pass