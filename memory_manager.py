"""
Módulo MemoryManager - Gerenciamento de Memória Virtual por Paginação

Este módulo simula o comportamento da memória principal (RAM) do pseudo-SO,
implementando a técnica de paginação com substituição de páginas baseada no
algoritmo LRU (Least Recently Used) sob uma política de alocação local.

A arquitetura física e lógica da memória é particionada da seguinte forma:

- Capacidade Total: 20 frames de tamanho fixo (1024 bytes / 1KB cada).

- Partição de Tempo Real: 8 frames exclusivos, inacessíveis a processos comuns.

- Partição de Usuário: 12 frames exclusivos, inacessíveis a processos de tempo real.

Operações e Mecanismos Principais:

1. PRÉ-CARGA (preload): Executada no momento em que um processo é admitido
no sistema. Carrega antecipadamente a primeira página da string de referência
para a RAM, garantindo que o processo não sofra um page fault na sua primeira instrução.

2. RASTREAMENTO DE ACESSO (access_page): Analisa o pedido de memória a cada instrução.

- Page Hit: Retorna verdadeiro e reclassifica a página na fila interna do
processo como a mais recentemente usada (MRU - movida para o final da lista).

- Page Fault: Retorna falso, incrementa o contador de falhas do processo e
aciona o mecanismo de alocação. Conforme especificado, o tempo de tratamento
da falha é ignorado e o processo não perde o domínio da CPU.

3. ALOCAÇÃO E SUBSTITUIÇÃO LOCAL (LRU): Quando um page fault ocorre, o módulo
verifica se o processo excedeu seu limite de páginas (max_working_set) ou se a
partição global (tempo real ou usuário) está cheia. Caso positivo, remove a página
menos recentemente acessada pertencente estritamente àquele mesmo processo (LRU local).

4. DESALOCAÇÃO (free_process): Invocado pelo Dispatcher quando um processo conclui
seu ciclo de vida, liberando todos os frames ocupados e devolvendo o espaço
físico para o sistema operacional.
"""

from process import Process

class MemoryManager:
    def __init__(self):
        # Definição física e lógica da Memória Principal
        self.TOTAL_FRAMES = 20
        self.RT_FRAMES = 8
        self.USER_FRAMES = 12
        self.FRAME_SIZE = 1024  # 1k por frame
        
        # Rastreamento do consumo global de frames
        self.used_rt_frames = 0
        self.used_user_frames = 0
        
        # Dicionário para rastrear as páginas na RAM por processo (Escopo Local).
        # A chave é o PID, o valor é uma lista de páginas.
        # Índice 0: Least Recently Used (LRU) | Último índice: Most Recently Used (MRU)
        self.process_pages: dict[int, list[int]] = {}

    def preload(self, process: Process) -> None:
        # A pré-carga carrega a primeira página da string de referência na memória 
        # logo na inicialização, sem contabilizar como page fault no momento da execução.
        if not process.reference_string:
            return
            
        first_page = process.reference_string[0]
        self.process_pages[process.pid] = [first_page]
        process.allocated_frames = 1
        
        if process.is_real_time():
            self.used_rt_frames += 1
        else:
            self.used_user_frames += 1

    def access_page(self, process: Process, page: int) -> bool:
        # Garantia de inicialização caso o processo não tenha passado pela pré-carga
        if process.pid not in self.process_pages:
            self.process_pages[process.pid] = []
            
        pages_in_mem = self.process_pages[process.pid]
        
        # 1. VERIFICAÇÃO DE PAGE HIT
        if page in pages_in_mem:
            # Atualiza o status LRU: remove de onde está e joga para o final (MRU)
            pages_in_mem.remove(page)
            pages_in_mem.append(page)
            return True
            
        # 2. PAGE FAULT IDENTIFICADO
        process.page_faults += 1
        
        # 3. LÓGICA DE ALOCAÇÃO OU SUBSTITUIÇÃO (LRU LOCAL)
        is_rt = process.is_real_time()
        needs_replacement = False
        
        # O escopo é local: checa primeiro se estourou o working set DO processo
        if len(pages_in_mem) >= process.max_working_set:
            needs_replacement = True
        else:
            # Mesmo tendo espaço no working set, a RAM física global pode estar cheia
            if is_rt and self.used_rt_frames >= self.RT_FRAMES:
                needs_replacement = True
            elif not is_rt and self.used_user_frames >= self.USER_FRAMES:
                needs_replacement = True
                
        if needs_replacement:
            # Algoritmo LRU no escopo local: remove a página mais antiga deste processo
            if pages_in_mem:
                pages_in_mem.pop(0) 
            
            # Adiciona a nova página no final (MRU)
            pages_in_mem.append(page)
        else:
            # Há espaço físico e lógico: apenas aloca um frame novo
            pages_in_mem.append(page)
            process.allocated_frames += 1
            
            if is_rt:
                self.used_rt_frames += 1
            else:
                self.used_user_frames += 1
                
        # O processo mantém a posse da CPU conforme a especificação, retornamos False 
        # para indicar ao Dispatcher que o fault ocorreu.
        return False

    def free_process(self, process: Process) -> None:
        # Libera todos os frames físicos quando o processo for finalizado (SIGINT).
        if process.pid in self.process_pages:
            frames_freed = len(self.process_pages[process.pid])
            
            if process.is_real_time():
                self.used_rt_frames -= frames_freed
            else:
                self.used_user_frames -= frames_freed
                
            del self.process_pages[process.pid]
            process.allocated_frames = 0