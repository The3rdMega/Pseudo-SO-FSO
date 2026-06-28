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

- Inicializa o tamanho total do Disco no FileSystem.

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
from file_system import FileSystem

class Dispatcher:
    """O primeiro processo criado, responsável por inicializar recursos, exibir mensagens e gerenciar a execução."""
    
    def __init__(self):
        # Instancia os gerenciadores globais que compõem o núcleo do pseudo-SO.
        self.scheduler = Scheduler()
        self.memory = MemoryManager()
        self.resources = ResourceManager()
        self.file_system = None 
        
        # Lista global que atua como a Tabela de Processos do sistema.
        self.processes: list[Process] = []

    def load_inputs(self, proc_path: str, files_path: str, string_path: str) -> None:
        """Coordena a fase de boot, lendo todos os arquivos de entrada necessários para a simulação."""
        print("dispatcher => Inicializando o sistema e lendo arquivos...")
        self._load_processes_and_strings(Path(proc_path), Path(string_path))
        self._load_file_system(Path(files_path))

    def _load_processes_and_strings(self, proc_file: Path, string_file: Path) -> None:
        """
        Lê os arquivos de definição de processos e strings de referência de memória.
        Realiza a leitura em paralelo para garantir que a string de acesso a páginas
        seja vinculada ao Process Control Block (PCB) correto.
        """
        if not proc_file.exists() or not string_file.exists():
            raise FileNotFoundError("Arquivo processes.txt ou string.txt não encontrado.")

        with proc_file.open('r') as pf, string_file.open('r') as sf:
            # O enumerate garante que o PID sempre inicie em 0 automaticamente.
            for pid, (proc_line, string_line) in enumerate(zip(pf, sf)):
                proc_line = proc_line.strip()
                string_line = string_line.strip()
                
                # Ignora linhas em branco para evitar falhas de segmentação ou parsing.
                if not proc_line:
                    continue

                # Faz o parsing dos atributos do processo separados por vírgula.
                data = [int(x.strip()) for x in proc_line.split(',')]
                
                # Faz o parsing das requisições de página. Retorna lista vazia se não houver string.
                ref_string = [int(x.strip()) for x in string_line.split(',')] if string_line else []

                # Instancia o PCB contendo as métricas de CPU e requisições de E/S.
                process = Process(
                    pid=pid,
                    init_time=data[0],
                    priority=data[1],
                    cpu_time=data[2],
                    max_working_set=data[3],
                    printer_req=data[4],
                    scanner_req=data[5],
                    modem_req=data[6],
                    sata_req=data[7],
                    reference_string=ref_string
                )
                self.processes.append(process)

    def _load_file_system(self, files_file: Path) -> None:
        """
        Realiza a leitura das configurações iniciais do disco.
        Lê a quantidade de blocos totais e prepara o sistema de arquivos.
        """
        if not files_file.exists():
            raise FileNotFoundError("Arquivo files.txt não encontrado.")
            
        with files_file.open('r') as ff:
            lines = [line.strip() for line in ff if line.strip()]
            
            if not lines:
                return

            # A primeira linha obrigatoriamente dita o limite do hardware de disco.
            total_blocks = int(lines[0])
            self.file_system = FileSystem(total_blocks)
            
            # TODO: Implementar a extração dos segmentos ocupados (linha 2)
            # e carregar as operações de criação/deleção (linhas subsequentes).

    def _print_process_creation(self, process: Process) -> None:
        """ Método Auxiliar """
        # Exibe as informações do processo no momento exato em que ele é despachado
        print("dispatcher =>")
        print(f"PID: {process.pid}")
        print(f"frames: {process.max_working_set}")
        print(f"priority: {process.priority}")
        print(f"time: {process.cpu_time}")
        print(f"printers: {process.printer_req}")
        print(f"scanners: {process.scanner_req}")
        print(f"modems: {process.modem_req}")
        print(f"drives: {process.sata_req}")
        print(f"process {process.pid} =>")
        print(f"P{process.pid} STARTED")

    def run(self) -> None:
        """
        Loop principal de execução (Main Clock).
        Responsável por orquestrar a passagem do tempo (quantum),
        acionar o escalonador e solicitar recursos/memória.
        """
        
        print(f"Total de processos carregados: {len(self.processes)}")
        
        tick = 0
        completed_processes = 0
        total_processes = len(self.processes)
        
        # O laço principal roda até que todos os processos tenham concluído seu tempo de CPU
        while completed_processes < total_processes:
            
            # 1. Fase de Admissão: Verifica quais processos "nascem" neste exato milissegundo
            for p in self.processes:
                if p.init_time == tick:
                    self._print_process_creation(p)
                    self.scheduler.admit(p)
            
            # 2. Fase de Escalonamento: Pergunta ao Scheduler quem deve usar a CPU
            current_process = self.scheduler.next()
            
            if current_process:
                # 3. Fase de Execução: O processo ganha 1ms de CPU (1 instrução)
                current_process.program_counter += 1
                current_process.cpu_time -= 1
                print(f"P{current_process.pid} instruction {current_process.program_counter}")
                
                # 4. Fase de Finalização ou Preempção
                if current_process.cpu_time <= 0:
                    # O processo terminou sua execução
                    print(f"P{current_process.pid} return SIGINT")
                    completed_processes += 1
                else:
                    # O processo não terminou, mas o quantum de 1ms esgotou
                    # Ele sofre preempção e volta para a fila correspondente
                    self.scheduler.preempt(current_process)
            
            # 5. Fase de Manutenção: Incrementa a espera nas filas e checa starvation
            self.scheduler.update_wait_times_and_age()
            
            # Avança o relógio global do pseudo-SO
            tick += 1

if __name__ == "__main__":
    # Valida a passagem de argumentos via linha de comando.
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