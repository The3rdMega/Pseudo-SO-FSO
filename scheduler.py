"""
Módulo Scheduler - Gerenciador de Filas e Escalonamento de Processos

Este módulo atua como o núcleo de decisão de troca de contexto do pseudo-SO. Ele organiza
os processos em estado "pronto" e determina qual deles deve receber o controle da CPU,
aplicando regras de prioridade, preempção temporal e prevenção contra inanição (starvation).

A arquitetura das estruturas de dados é dividida da seguinte forma:

- Fila de Tempo Real (Prioridade 0): Escalonamento estrito First-In-First-Out (FIFO).
Não sofre preempção por quantum e tem precedência absoluta no uso do processador.

- Filas de Usuário (Prioridades 1, 2 e 3): Sistema de múltiplas filas com realimentação.
Processos alocados aqui possuem um tempo limite de execução (quantum de 1ms) e
estão sujeitos a interrupções forçadas.

Operações e Mecanismos Principais:

1. ADMISSÃO (admit): Verifica o limite de capacidade global (1000 processos) e
insere o processo ingressante na fila adequada ao seu nível de prioridade, zerando
seu contador de espera.

2. SELEÇÃO (next): Busca e remove da estrutura o próximo processo apto a executar,
sempre inspecionando a Fila de Tempo Real primeiro e descendo pelas Filas de Usuário.

3. PREEMPÇÃO E REBAIXAMENTO (preempt): Trata processos de usuário que esgotaram
seu quantum. Aplica a penalidade de realimentação, rebaixando a prioridade do processo
e inserindo-o na fila inferior (limitado à prioridade 3).

4. ENVELHECIMENTO DINÂMICO (update_wait_times_and_age): Mecanismo invocado a cada
ciclo (tick) pelo Dispatcher. Rastreia o tempo de espera individual de processos
nas filas 2 e 3. Caso um processo atinja o limiar de espera (starvation_threshold = 10),
sua prioridade é aumentada (promovido para a fila imediatamente superior),
garantindo que todos os processos eventualmente recebam tempo de CPU.
"""

from collections import deque
from typing import Optional
from process import Process

class Scheduler:
    def __init__(self):
        # Fila exclusiva para tempo real (FIFO, prioridade 0, sem preempção)
        self.real_time_queue: deque[Process] = deque()
        
        # Múltiplas filas de usuário com realimentação. 
        # O índice da lista representa a fila:
        # user_queues[0] -> Prioridade 1 (Maior prioridade de usuário)
        # user_queues[1] -> Prioridade 2
        # user_queues[2] -> Prioridade 3 (Menor prioridade)
        self.user_queues: list[deque[Process]] = [deque(), deque(), deque()]
        
        # Quantum fixo de 1 milissegundo para processos preemptivos
        self.quantum: int = 1
        
        # Limite global de processos suportados pelas filas
        self.max_capacity: int = 1000
        self._current_count: int = 0

        # Limite de ticks que um processo pode esperar antes de ser considerado em starvation
        self.starvation_threshold: int = 10

    def admit(self, process: Process) -> bool:
        # Bloqueia a entrada se o limite máximo do sistema for atingido
        if self._current_count >= self.max_capacity:
            return False

        # Zera o tempo de espera ao entrar na fila
        process.wait_time = 0

        if process.is_real_time():
            self.real_time_queue.append(process)
        else:
            # Processos de usuário entram na fila correspondente à sua prioridade.
            # Como a prioridade 1 vai para o índice 0, subtraímos 1.
            # Se a prioridade vier fora do escopo (ex: > 3), limitamos à última fila.
            queue_index = min(max(process.priority - 1, 0), 2)
            self.user_queues[queue_index].append(process)
            
        self._current_count += 1
        return True

    def next(self) -> Optional[Process]:
        # Sempre verifica a fila de tempo real primeiro (prioridade absoluta)
        if self.real_time_queue:
            return self.real_time_queue.popleft()

        # Busca o processo de usuário na fila não vazia de maior prioridade
        for queue in self.user_queues:
            if queue:
                proc = queue.popleft()
                # O processo vai rodar, então ele não está mais esperando
                proc.wait_time = 0
                return proc

        # Retorna None se não houver processos prontos para executar
        return None

    def preempt(self, process: Process) -> None:
        # Processos de tempo real não sofrem preempção por quantum, 
        # mas caso sofram bloqueio de I/O (se aplicável), voltam ao topo.
        if process.is_real_time():
            self.real_time_queue.appendleft(process)
            return

        # Para processos de usuário, aplicamos a penalidade de realimentação.
        # Se esgotou o quantum, ele cai para a fila de prioridade inferior.
        current_queue_index = min(max(process.priority - 1, 0), 2)
        
        if current_queue_index < 2:
            process.priority += 1  # Rebaixa a prioridade (número maior = prioridade menor)
            new_queue_index = current_queue_index + 1
        else:
            new_queue_index = current_queue_index # Mantém na última fila se já estiver nela
            
        # Zera o tempo de espera ao entrar na nova fila    
        process.wait_time = 0
        self.user_queues[new_queue_index].append(process)

    def update_wait_times_and_age(self) -> None:
        # Este método deve ser chamado pelo Dispatcher a cada tick (milissegundo).
        # Ele incrementa a espera de quem está nas filas e promove quem sofreu starvation.
        
        # Ignoramos a fila 0 (prioridade 1) porque ela já é a mais alta para usuários
        for current_queue_index in range(1, 3):
            queue = self.user_queues[current_queue_index]
            processes_in_queue = len(queue)
            
            # Usamos um loop baseado no tamanho atual para rotacionar a fila
            for _ in range(processes_in_queue):
                proc = queue.popleft()
                proc.wait_time += 1
                
                # Análise de starvation: passou do limite?
                if proc.wait_time >= self.starvation_threshold:
                    # Promove o processo (aging)
                    proc.priority -= 1
                    proc.wait_time = 0 # Reseta a espera após a promoção
                    
                    # Move para a fila de prioridade superior
                    new_queue_index = current_queue_index - 1
                    self.user_queues[new_queue_index].append(proc)
                else:
                    # Não sofreu starvation, devolve para a mesma fila
                    queue.append(proc)
            
    def has_processes(self) -> bool:
        # Verifica se ainda há algum processo aguardando escalonamento
        if self.real_time_queue:
            return True
        return any(len(q) > 0 for q in self.user_queues)