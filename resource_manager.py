"""
Módulo ResourceManager - Gerenciamento de Recursos de E/S

Este módulo é responsável por administrar a alocação e a liberação dos 
dispositivos periféricos do pseudo-SO, garantindo o uso exclusivo (exclusão mútua) 
dos recursos de Entrada e Saída (I/O) para evitar condições de corrida.

A infraestrutura de hardware simulada dispõe das seguintes quantidades fixas:
- 1 Scanner
- 2 Impressoras
- 1 Modem
- 2 Dispositivos SATA

Operações e Regras de Negócio:
1. ALOCAÇÃO (request):
   - Realiza uma tentativa de alocação no formato "tudo ou nada". O processo 
     só recebe a permissão se o sistema possuir a quantidade suficiente de todos 
     os recursos solicitados disponíveis simultaneamente.
   - Não há preempção na alocação de dispositivos de E/S. Se os recursos estiverem 
     ocupados por outro processo, o pedido é negado (retorna False).
   - Processos de tempo real possuem permissão livre e automática, pois a 
     arquitetura do sistema determina que eles não necessitam de recursos de I/O.

2. LIBERAÇÃO (release):
   - Invocado quando um processo comum conclui sua execução.
   - Restitui exatamente as quantidades de scanners, impressoras, modems e 
     dispositivos SATA que o processo detinha de volta à reserva global do 
     sistema, permitindo que outros processos aguardando na fila possam utilizá-los.
"""

from process import Process

class ResourceManager:
    def __init__(self):
        # Capacidade máxima de recursos do sistema
        self.available_scanners = 1
        self.available_printers = 2
        self.available_modems = 1
        self.available_sata = 2

        # Dicionário para rastrear a posse dos recursos.
        # Estrutura: { pid: {'scanners': int, 'printers': int, 'modems': int, 'sata': int} }
        self.allocated_to: dict[int, dict[str, int]] = {}

    def request(self, process: Process) -> bool:
        # Processos de tempo real não realizam operações de I/O.
        # Retorna True automaticamente para não bloquear a execução.
        if process.is_real_time():
            return True

        # Se o processo já possui os recursos alocados, o acesso é garantido.
        if process.pid in self.allocated_to:
            return True

        # Verifica se o sistema possui a quantidade exata (ou mais) dos recursos requisitados.
        if (process.scanner_req > self.available_scanners or
            process.printer_req > self.available_printers or
            process.modem_req > self.available_modems or
            process.sata_req > self.available_sata):
            return False

        # Alocação bem-sucedida: Deduz os recursos da reserva global.
        self.available_scanners -= process.scanner_req
        self.available_printers -= process.printer_req
        self.available_modems -= process.modem_req
        self.available_sata -= process.sata_req

        # Registra a posse dos recursos vinculada ao PID do processo.
        self.allocated_to[process.pid] = {
            'scanners': process.scanner_req,
            'printers': process.printer_req,
            'modems': process.modem_req,
            'sata': process.sata_req
        }

        return True

    def release(self, process: Process) -> None:
        # Processos de tempo real não têm o que liberar.
        if process.is_real_time():
            return

        # Verifica se o processo realmente possuía recursos antes de tentar liberar.
        if process.pid in self.allocated_to:
            allocs = self.allocated_to.pop(process.pid)
            
            # Devolve as quantias exatas para a reserva global.
            self.available_scanners += allocs.get('scanners', 0)
            self.available_printers += allocs.get('printers', 0)
            self.available_modems += allocs.get('modems', 0)
            self.available_sata += allocs.get('sata', 0)