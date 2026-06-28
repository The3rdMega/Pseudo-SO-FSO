import unittest
from process import Process
from resource_manager import ResourceManager

class TestResourceManager(unittest.TestCase):
    def setUp(self):
        """Prepara o ambiente limpo de recursos antes de cada teste."""
        self.rm = ResourceManager()
        
        # Processo de Tempo Real (Prioridade 0)
        # Requisita I/O apenas para testar se o sistema ignora o pedido corretamente
        self.p_rt = Process(
            pid=0, init_time=0, priority=0, cpu_time=5, max_working_set=2,
            printer_req=2, scanner_req=1, modem_req=1, sata_req=2
        )
        
        # Processo de Usuário 1 (Pede 1 impressora, 1 scanner)
        self.p_user1 = Process(
            pid=1, init_time=0, priority=1, cpu_time=5, max_working_set=2,
            printer_req=1, scanner_req=1, modem_req=0, sata_req=0
        )
        
        # Processo de Usuário 2 (Pede 2 impressoras, esgotando o limite global)
        self.p_user2 = Process(
            pid=2, init_time=0, priority=1, cpu_time=5, max_working_set=2,
            printer_req=2, scanner_req=0, modem_req=0, sata_req=0
        )

    def test_real_time_bypass(self):
        """Valida que processos de tempo real não afetam a reserva global."""
        result = self.rm.request(self.p_rt)
        
        self.assertTrue(result)
        self.assertEqual(self.rm.available_printers, 2)
        self.assertEqual(self.rm.available_scanners, 1)
        self.assertNotIn(self.p_rt.pid, self.rm.allocated_to)

    def test_successful_allocation(self):
        """Valida a alocação atômica quando há recursos suficientes disponíveis."""
        result = self.rm.request(self.p_user1)
        
        self.assertTrue(result)
        self.assertEqual(self.rm.available_printers, 1)
        self.assertEqual(self.rm.available_scanners, 0)
        self.assertIn(self.p_user1.pid, self.rm.allocated_to)

    def test_failed_allocation_atomic(self):
        """Valida a negação (tudo ou nada) quando falta algum recurso."""
        # user1 pega 1 impressora e 1 scanner
        self.rm.request(self.p_user1) 
        
        # user2 tenta pegar 2 impressoras, mas só resta 1
        result = self.rm.request(self.p_user2)
        
        self.assertFalse(result)
        # Garante que não houve alocação parcial e os recursos continuam no estado anterior
        self.assertEqual(self.rm.available_printers, 1)
        self.assertNotIn(self.p_user2.pid, self.rm.allocated_to)

    def test_release_resources(self):
        """Valida se a liberação restaura exatamente os valores originais da reserva."""
        self.rm.request(self.p_user1)
        self.rm.release(self.p_user1)
        
        self.assertEqual(self.rm.available_printers, 2)
        self.assertEqual(self.rm.available_scanners, 1)
        self.assertNotIn(self.p_user1.pid, self.rm.allocated_to)

    def test_double_request_persistence(self):
        """Garante que sucessivos pedidos do mesmo processo não deduplicam recursos."""
        self.rm.request(self.p_user1)
        result = self.rm.request(self.p_user1) # Solicita no tick seguinte
        
        self.assertTrue(result)
        self.assertEqual(self.rm.available_printers, 1)

if __name__ == '__main__':
    unittest.main()