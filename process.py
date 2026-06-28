from dataclasses import dataclass, field
from typing import List

@dataclass
class Process:
    """Estrutura de dados relativa ao processo."""
    pid: int
    init_time: int
    priority: int
    cpu_time: int
    max_working_set: int
    printer_req: int
    scanner_req: int
    modem_req: int
    sata_req: int
    wait_time: int  # Adicionado para detecção dinâmica de starvation
    
    # Atributos dinâmicos gerenciados durante a execução
    reference_string: List[int] = field(default_factory=list)
    allocated_frames: int = 0
    page_faults: int = 0
    program_counter: int = 0

    def is_real_time(self) -> bool:
        """Processos de tempo real têm prioridade definida como 0."""
        return self.priority == 0