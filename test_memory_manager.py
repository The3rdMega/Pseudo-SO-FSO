import unittest
from process import Process
from memory_manager import MemoryManager

class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        """Inicializa o MemoryManager e cria processos falsos para os testes."""
        self.memory = MemoryManager()
        
        # Processo de Usuário (PID 1): Working set máximo de 3 frames
        self.p_user = Process(
            pid=1, init_time=0, priority=1, cpu_time=5, max_working_set=3,
            printer_req=0, scanner_req=0, modem_req=0, sata_req=0,
            reference_string=[10, 20, 10, 30, 40]
        )
        
        # Processo de Tempo Real (PID 0): Working set máximo de 2 frames
        self.p_rt = Process(
            pid=0, init_time=0, priority=0, cpu_time=5, max_working_set=2,
            printer_req=0, scanner_req=0, modem_req=0, sata_req=0,
            reference_string=[100, 200, 300]
        )

    def test_preload(self):
        """Verifica se a pré-carga carrega a primeira página e aloca 1 frame."""
        self.memory.preload(self.p_user)
        
        self.assertEqual(self.p_user.allocated_frames, 1)
        self.assertEqual(self.memory.used_user_frames, 1)
        # A página 10 deve estar na memória
        self.assertIn(10, self.memory.process_pages[self.p_user.pid])

    def test_page_hit(self):
        """Verifica se acessar uma página já carregada retorna True e não conta fault."""
        self.memory.preload(self.p_user) # Carrega página 10
        
        hit = self.memory.access_page(self.p_user, 10)
        
        self.assertTrue(hit)
        self.assertEqual(self.p_user.page_faults, 0)
        self.assertEqual(self.p_user.allocated_frames, 1)

    def test_page_fault_and_allocation(self):
        """Acessar página nova deve gerar fault e alocar novo frame (se houver espaço)."""
        self.memory.preload(self.p_user) # Carrega página 10
        
        hit = self.memory.access_page(self.p_user, 20)
        
        self.assertFalse(hit)
        self.assertEqual(self.p_user.page_faults, 1)
        self.assertEqual(self.p_user.allocated_frames, 2)
        self.assertEqual(self.memory.process_pages[self.p_user.pid], [10, 20])

    def test_lru_local_replacement(self):
        """Verifica se o LRU local ejeta a página mais antiga ao estourar o working set."""
        self.memory.preload(self.p_rt) # Carrega 100 (1 frame)
        self.memory.access_page(self.p_rt, 200) # Carrega 200 (2 frames - limite do working set)
        
        # O histórico de acesso agora é [100, 200]. O LRU (mais antigo) é 100.
        # Acessar 300 deve ejetar o 100.
        hit = self.memory.access_page(self.p_rt, 300)
        
        self.assertFalse(hit)
        self.assertEqual(self.p_rt.page_faults, 2) # Faltas para o 200 e o 300
        self.assertEqual(self.p_rt.allocated_frames, 2) # Não pode passar do limite de 2
        
        # A página 100 deve ter sumido, restando 200 e 300
        self.assertEqual(self.memory.process_pages[self.p_rt.pid], [200, 300])

    def test_free_process_memory(self):
        """Verifica se a finalização de um processo devolve os frames para o sistema."""
        self.memory.preload(self.p_user)
        self.memory.access_page(self.p_user, 20)
        self.assertEqual(self.memory.used_user_frames, 2)
        
        self.memory.free_process(self.p_user)
        
        self.assertEqual(self.memory.used_user_frames, 0)
        self.assertEqual(self.p_user.allocated_frames, 0)
        self.assertNotIn(self.p_user.pid, self.memory.process_pages)

if __name__ == '__main__':
    unittest.main()