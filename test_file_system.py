import unittest
from process import Process
from file_system import FileSystem

class TestFileSystem(unittest.TestCase):
    def setUp(self):
        """Prepara um disco limpo de 10 blocos e processos para os testes."""
        self.fs = FileSystem(10)
        
        # Processo de Tempo Real (Prioridade 0)
        self.p_rt = Process(
            pid=0, init_time=0, priority=0, cpu_time=5, max_working_set=2,
            printer_req=0, scanner_req=0, modem_req=0, sata_req=0
        )
        
        # Processo de Usuário 1 
        self.p_user1 = Process(
            pid=1, init_time=0, priority=1, cpu_time=5, max_working_set=2,
            printer_req=0, scanner_req=0, modem_req=0, sata_req=0
        )
        
        # Processo de Usuário 2 
        self.p_user2 = Process(
            pid=2, init_time=0, priority=1, cpu_time=5, max_working_set=2,
            printer_req=0, scanner_req=0, modem_req=0, sata_req=0
        )

    def test_create_first_fit(self):
        """Valida se a alocação inicial preenche o disco a partir do bloco 0."""
        result = self.fs.create(self.p_user1, "A.txt", 3)

        self.assertTrue(result[0])
        self.assertEqual(self.fs.disk[0:3], ["A.txt", "A.txt", "A.txt"])
        self.assertEqual(self.fs.disk[3], 0)

    def test_create_fragmentation_reuse(self):
        """Valida se o First-Fit aloca corretamente na primeira lacuna disponível."""
        self.fs.create(self.p_user1, "A.txt", 2)
        self.fs.create(self.p_user1, "B.txt", 3)
        
        # Estado atual: [A, A, B, B, B, 0, 0, 0, 0, 0]
        self.fs.delete(self.p_user1, "A.txt")
        # Após deleção: [0, 0, B, B, B, 0, 0, 0, 0, 0]
        
        # O arquivo C precisa de 1 bloco. O First-Fit deve colocá-lo no índice 0.
        self.fs.create(self.p_user2, "C.txt", 1)
        
        self.assertEqual(self.fs.disk[0], "C.txt")
        self.assertEqual(self.fs.disk[1], 0) # O bloco 1 continua vazio

    def test_create_insufficient_space(self):
        """Valida falha ao tentar alocar arquivo maior do que o espaço contíguo disponível."""
        self.fs.create(self.p_user1, "A.txt", 8)
        
        # Restam apenas 2 blocos livres no final. Pedir 3 deve falhar.
        result = self.fs.create(self.p_user2, "B.txt", 3)

        self.assertFalse(result[0])

    def test_delete_permission_user_denied(self):
        """Valida se um usuário é bloqueado ao tentar deletar arquivo de outro PID."""
        self.fs.create(self.p_user1, "A.txt", 2)
        
        # P2 tenta deletar arquivo de P1
        result = self.fs.delete(self.p_user2, "A.txt")

        self.assertFalse(result[0])
        self.assertEqual(self.fs.disk[0], "A.txt") # Arquivo permanece intacto

    def test_delete_permission_rt_allowed(self):
        """Valida se o processo de tempo real consegue burlar a regra do proprietário."""
        self.fs.create(self.p_user1, "A.txt", 2)
        
        # Tempo Real tenta deletar arquivo de P1
        result = self.fs.delete(self.p_rt, "A.txt")

        self.assertTrue(result[0])
        self.assertEqual(self.fs.disk[0], 0) # Arquivo foi deletado com sucesso

if __name__ == '__main__':
    unittest.main()