import sys
from scheduler import Scheduler
from memory_manager import MemoryManager
from resource_manager import ResourceManager
from file_system import FileSystem

class Dispatcher:
    """O primeiro processo criado, responsável por exibir as mensagens e gerenciar a execução."""
    def __init__(self):
        self.scheduler = Scheduler()
        self.memory = MemoryManager()
        self.resources = ResourceManager()
        # O FileSystem será inicializado ao ler files.txt

    def load_inputs(self, proc_file: str, files_file: str, string_file: str):
        """Lê os três arquivos de entrada (.txt) do pseudo-SO."""
        pass

    def run(self):
        """Loop principal do sistema operacional."""
        pass

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python dispatcher.py <processes.txt> <files.txt> <string.txt>")
        sys.exit(1)
    
    dispatcher = Dispatcher()
    dispatcher.load_inputs(sys.argv[1], sys.argv[2], sys.argv[3])
    dispatcher.run()