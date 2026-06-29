"""
Módulo FileSystem - Gerenciador de Sistema de Arquivos

Este módulo simula o armazenamento secundário (disco) do pseudo-SO, 
responsável por gerir a criação, deleção e a disposição física de arquivos 
através do método de alocação contígua.

A infraestrutura do disco é representada por um array de blocos de tamanho fixo,
onde espaços livres são marcados com '0' e espaços ocupados armazenam o nome do arquivo.

Operações e Mecanismos Principais:
1. ALOCAÇÃO (create):
   - Utiliza o algoritmo First-Fit (Primeiro Encaixe). A busca por blocos livres 
     inicia sempre a partir do bloco 0 (início do disco), alocando o arquivo na 
     primeira lacuna contígua que possua tamanho suficiente.
   - Arquivos são tratados como uma unidade indivisível; a alocação requer que 
     todos os blocos solicitados estejam sequencialmente disponíveis.

2. DELEÇÃO E CONTROLO DE ACESSO (delete):
   - Implementa regras estritas de permissão baseadas no tipo de processo:
     * Processos de Tempo Real: Possuem privilégios irrestritos, podendo 
       apagar qualquer arquivo do disco, independentemente de quem o criou.
     * Processos Comuns de Usuário: Possuem acesso restrito, sendo autorizados a 
       apagar estritamente os arquivos dos quais são donos (validação por owner_pid).
   - A deleção consiste em limpar o espaço físico (substituir o nome por 0) e 
     remover os metadados da tabela de controle.

3. MAPEAMENTO (print_disk_map):
   - Gera o relatório visual da ocupação atual do disco, exibido no fim da 
     execução do sistema operativo, mapeando as posições exatas dos arquivos 
     e os espaços vazios (0) restantes, evidenciando a fragmentação externa.
"""

from dataclasses import dataclass
from typing import Optional
from process import Process

@dataclass
class File:
    name: str
    start_block: int
    num_blocks: int
    owner_pid: int

class FileSystem:
    def __init__(self, total_blocks: int):
        self.total_blocks = total_blocks
        # Representação do disco. Blocos vazios são representados por 0 (inteiro).
        # Blocos ocupados armazenarão a string do nome do arquivo.
        self.disk: list[int | str] = [0] * total_blocks
        self.files: list[File] = []

    def _get_file(self, name: str) -> Optional[File]:
        """Método auxiliar interno para buscar metadados de um arquivo pelo nome."""
        for f in self.files:
            if f.name == name:
                return f
        return None

    def create(self, process: Process, name: str, blocks: int) -> tuple:
        """Retorna (success: bool, start_block: int). start_block é -1 em caso de falha."""
        # Verifica se um arquivo com o mesmo nome já existe para evitar colisão
        if self._get_file(name):
            return (False, -1)

        # Algoritmo First-Fit: Busca espaço contíguo a partir do primeiro bloco (índice 0)
        consecutive_free = 0
        start_index = -1

        for i in range(self.total_blocks):
            if self.disk[i] == 0:
                # Marca o início de uma potencial lacuna contígua
                if consecutive_free == 0:
                    start_index = i
                consecutive_free += 1

                # Se a lacuna for grande o suficiente, realiza a alocação
                if consecutive_free == blocks:
                    # Preenche o disco com o identificador (nome) do arquivo
                    for j in range(start_index, start_index + blocks):
                        self.disk[j] = name

                    # Registra os metadados do arquivo
                    self.files.append(File(name, start_index, blocks, process.pid))
                    return (True, start_index)
            else:
                # O bloco está ocupado. Reseta o contador contíguo.
                consecutive_free = 0

        # Varredura completa: Não encontrou espaço contíguo suficiente
        return (False, -1)

    def delete(self, process: Process, name: str) -> tuple:
        """Retorna (success: bool, reason: str). reason é '' em caso de sucesso,
        'not_found' se o arquivo não existe, 'permission' se negado por permissão."""
        file_to_delete = self._get_file(name)

        if not file_to_delete:
            return (False, 'not_found')

        # Validação de Permissões
        # Processos de tempo real (is_real_time) ignoram a verificação de dono
        if not process.is_real_time() and file_to_delete.owner_pid != process.pid:
            return (False, 'permission')

        # Deleção Autorizada: Limpa o espaço físico no disco (substitui por 0)
        for i in range(file_to_delete.start_block, file_to_delete.start_block + file_to_delete.num_blocks):
            self.disk[i] = 0

        # Remove os metadados da tabela de arquivos
        self.files.remove(file_to_delete)
        return (True, '')

    def print_disk_map(self) -> None:
        # Exibição do relatório final conforme exigência da especificação
        print("\nMapa de ocupação do disco:")
        print(' '.join(str(block) for block in self.disk))