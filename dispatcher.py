"""
Módulo Dispatcher - Inicializador e Núcleo Central do Pseudo-SO

Este módulo atua simultaneamente como o "Bootloader" e a "CPU" do sistema operacional simulado.
Ele é o ponto de entrada da aplicação, responsável por orquestrar a interação entre todos os
outros gerenciadores (Escalonamento, Memória, Recursos e Arquivos) e garantir que a execução
ocorra de forma sincronizada e padronizada.

O funcionamento do módulo é dividido em três fases principais:

1. INICIALIZAÇÃO E ALOCAÇÃO (Setup)
Instancia as tabelas globais e as estruturas de controle do sistema operativo, inicializando
objetos do Scheduler, MemoryManager e ResourceManager. Atua como o proprietário absoluto das
instâncias globais que definem as regras do sistema.

2. CARREGAMENTO DE DADOS (Boot/Parsing)
Lê e interpreta os três arquivos passados via linha de comando (processes.txt, files.txt e string.txt).

- Cria os Blocos de Controle de Processos (PCBs - representados pela classe Process),
garantindo que cada processo inicie com o PID correto (a partir de 0) e que receba sua
respectiva string de requisição de memória (pages).

- Inicializa o tamanho total do Disco no FileSystem, pré-aloca segmentos já ocupados
e enfileira as operações de I/O de disco para cada processo.

3. CICLO DE MÁQUINA (Loop de Execução Principal)
Implementa o laço que simula o relógio do sistema (clock) e o quantum de execução (1ms).
Durante o ciclo ativo, o Dispatcher:

- Solicita ao Scheduler a definição de qual processo tem o direito à CPU.

- Intermedeia as requisições de memória do processo atual junto ao MemoryManager, lidando
com simulações de Page Faults e substituições via algoritmo LRU.

- Requisita a trava de dispositivos de I/O (impressoras, scanners, modems, SATA) ao
ResourceManager para garantir acesso de uso exclusivo, sem preempção.

- Aciona o FileSystem para operações de criação ou deleção em disco, validando
permissões (ex: processos de usuário só deletam arquivos próprios; tempo-real deleta qualquer um).

- Coordena a troca de contexto, retornando processos à fila e aplicando regras de preempção.

- Imprime no terminal o rastreamento em tempo real (logs de PID, alocações de frames, prioridades)
e exibe os relatórios finais (Mapa de Ocupação do Disco e Número de Faltas de Páginas).
"""

import sys
from pathlib import Path
from process import Process
from scheduler import Scheduler
from memory_manager import MemoryManager
from resource_manager import ResourceManager
from file_system import FileSystem, File

class Dispatcher:
    """O primeiro processo criado, responsável por inicializar recursos, exibir mensagens e gerenciar a execução."""
    
    def __init__(self):
        # Instancia os gerenciadores globais que compõem o núcleo do pseudo-SO.
        self.scheduler = Scheduler()
        self.memory = MemoryManager()
        self.resources = ResourceManager()
        self.file_system = None 
        
        # Estruturas de controle do sistema
        self.processes: list[Process] = []
        self.file_operations: list[dict] = [] # Fila de operações de disco

    def load_inputs(self, proc_path: str, files_path: str, string_path: str) -> None:
        """Coordena a fase de boot, lendo todos os arquivos de entrada necessários para a simulação."""
        print("dispatcher => Inicializando o sistema e lendo arquivos...")
        self._load_processes_and_strings(Path(proc_path), Path(string_path))
        self._load_file_system(Path(files_path))

    def _load_processes_and_strings(self, proc_file: Path, string_file: Path) -> None:
        """
        Lê os arquivos de definição de processos e strings de referência de memória.
        """
        if not proc_file.exists() or not string_file.exists():
            raise FileNotFoundError("Arquivo processes.txt ou string.txt não encontrado.")

        with proc_file.open('r') as pf, string_file.open('r') as sf:
            for pid, (proc_line, string_line) in enumerate(zip(pf, sf)):
                proc_line = proc_line.strip()
                string_line = string_line.strip()
                
                if not proc_line:
                    continue

                data = [int(x.strip()) for x in proc_line.split(',')]
                ref_string = [int(x.strip()) for x in string_line.split(',')] if string_line else []

                process = Process(
                    pid=pid, init_time=data[0], priority=data[1], cpu_time=data[2],
                    max_working_set=data[3], printer_req=data[4], scanner_req=data[5],
                    modem_req=data[6], sata_req=data[7], reference_string=ref_string
                )
                self.processes.append(process)

    def _load_file_system(self, files_file: Path) -> None:
        """
        Realiza a leitura das configurações iniciais do disco e enfileira as operações de arquivos.
        """
        if not files_file.exists():
            raise FileNotFoundError("Arquivo files.txt não encontrado.")
            
        with files_file.open('r') as ff:
            lines = [line.strip() for line in ff if line.strip()]
            
            if not lines:
                return

            # Linha 1: Limite do hardware de disco
            total_blocks = int(lines[0])
            self.file_system = FileSystem(total_blocks)
            
            # Linha 2: Quantidade de segmentos pré-ocupados
            num_occupied = int(lines[1])
            current_line = 2
            
            # Carrega os segmentos pré-ocupados (Arquivos do Sistema/Base)
            for _ in range(num_occupied):
                if current_line < len(lines):
                    parts = [p.strip() for p in lines[current_line].split(',')]
                    name = parts[0]
                    start_block = int(parts[1])
                    num_blocks = int(parts[2])
                    
                    # Força a alocação direta no disco. PID -1 representa arquivo do sistema (sem dono)
                    for i in range(start_block, start_block + num_blocks):
                        self.file_system.disk[i] = name
                    self.file_system.files.append(File(name, start_block, num_blocks, -1))
                    
                    current_line += 1

            # Carrega as operações requisitadas pelos processos
            while current_line < len(lines):
                parts = [p.strip() for p in lines[current_line].split(',')]
                pid = int(parts[0])
                opcode = int(parts[1]) # 0 = Criar, 1 = Deletar
                filename = parts[2]
                blocks = int(parts[3]) if len(parts) > 3 else 0
                
                self.file_operations.append({
                    'pid': pid,
                    'opcode': opcode,
                    'filename': filename,
                    'blocks': blocks
                })
                current_line += 1

    def _print_process_creation(self, process: Process) -> None:
        usa_impressora = bool(process.printer_req > 0)
        usa_scanner = bool(process.scanner_req > 0)
        usa_drive = bool(process.sata_req > 0)

        print("dispatcher =>")
        print(f"PID: {process.pid}")
        print(f"prioridade: {process.priority}")
        print(f"páginas alocadas: {process.max_working_set}")
        print(f"impressora: {usa_impressora}")
        print(f"scanner: {usa_scanner}")
        print(f"drives: {usa_drive}")
        print(f"process {process.pid} =>")
        print(f"P{process.pid} STARTED")

    def run(self) -> None:
        """ Loop principal de execução (Main Clock). """
        
        print(f"Total de processos carregados: {len(self.processes)}")
        
        tick = 0
        completed_processes = 0
        total_processes = len(self.processes)
        
        while completed_processes < total_processes:
            
            # 1. Fase de Admissão
            for p in self.processes:
                if p.init_time == tick:
                    self.memory.preload(p) 
                    self._print_process_creation(p)
                    self.scheduler.admit(p)
            
            # 2. Fase de Escalonamento
            current_process = self.scheduler.next()
            
            if current_process:
                # 3. Fase de Execução
                if self.resources.request(current_process):
                    # Acesso à memória por instrução
                    if current_process.program_counter < len(current_process.reference_string):
                        current_page = current_process.reference_string[current_process.program_counter]
                        self.memory.access_page(current_process, current_page)

                    current_process.program_counter += 1
                    current_process.cpu_time -= 1
                    print(f"P{current_process.pid} instruction {current_process.program_counter}")
                    
                    # 4. Fase de Finalização ou Preempção
                    if current_process.cpu_time <= 0:
                        print(f"P{current_process.pid} return SIGINT")
                        self.memory.free_process(current_process)
                        self.resources.release(current_process) 
                        completed_processes += 1
                    else:
                        self.scheduler.preempt(current_process)
                else:
                    self.scheduler.preempt(current_process)
            
            self.scheduler.update_wait_times_and_age()
            tick += 1

        # --- Bloco de Relatório do Sistema de Arquivos (Pós-Execução) ---
        print("\nSistema de arquivos =>")
        for i, op in enumerate(self.file_operations, 1):
            print(f"Operação {i} =>", end=" ")
            
            # Verifica se o processo existe
            process = next((p for p in self.processes if p.pid == op['pid']), None)
            
            if not process:
                print("Falha\nO processo " + str(op['pid']) + " não existe.")
            else:
                success = False
                if op['opcode'] == 0:
                    success = self.file_system.create(process, op['filename'], op['blocks'])
                else:
                    success = self.file_system.delete(process, op['filename'])
                print("Sucesso" if success else "Falha")

        # Relatórios Finais
        self.file_system.print_disk_map()
        print("\nNúmero de Faltas de Páginas por processo:")
        for p in self.processes:
            print(f"P{p.pid} = {p.page_faults} faltas de páginas")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python dispatcher.py <processes.txt> <files.txt> <string.txt>")
        sys.exit(1)
    
    try:
        dispatcher = Dispatcher()
        dispatcher.load_inputs(sys.argv[1], sys.argv[2], sys.argv[3])
        dispatcher.run()
    except Exception as e:
        print(f"Erro fatal durante a execução do pseudo-SO: {e}")
        sys.exit(1)