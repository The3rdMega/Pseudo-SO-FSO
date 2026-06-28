import unittest
from process import Process
from scheduler import Scheduler

class TestScheduler(unittest.TestCase):
    def setUp(self):
        """Prepara o ambiente antes de cada teste rodar."""
        self.scheduler = Scheduler()
        
        # Cria processos com dados mínimos apenas para testar o escalonamento
        # Argumentos: pid, init_time, priority, cpu_time, max_working_set, printer, scanner, modem, sata
        self.p_rt = Process(0, 0, 0, 5, 2, 0, 0, 0, 0) # Tempo Real (Prioridade 0)
        self.p_user1 = Process(1, 0, 1, 5, 2, 0, 0, 0, 0) # Usuário Prioridade 1
        self.p_user3 = Process(2, 0, 3, 5, 2, 0, 0, 0, 0) # Usuário Prioridade 3

    def test_admit_routing(self):
        """Verifica se os processos vão para as filas corretas no momento da admissão."""
        self.scheduler.admit(self.p_rt)
        self.scheduler.admit(self.p_user3)
        
        self.assertEqual(len(self.scheduler.real_time_queue), 1)
        # Prioridade 3 deve ir para o índice 2 da lista de filas de usuário
        self.assertEqual(len(self.scheduler.user_queues[2]), 1)

    def test_next_strict_priority(self):
        """Garante que o processo de tempo real sempre fura a fila dos usuários."""
        self.scheduler.admit(self.p_user1)
        self.scheduler.admit(self.p_rt)
        
        # Mesmo o usuário tendo entrado primeiro, o próximo a sair deve ser o Tempo Real
        next_proc = self.scheduler.next()
        self.assertIsNotNone(next_proc)
        self.assertEqual(next_proc.pid, 0)

    def test_starvation_and_aging(self):
        """Verifica se um processo esquecido é promovido após passar do threshold."""
        self.scheduler.admit(self.p_user3) # Entra na fila user_queues[2]
        
        # Simulamos que ele ficou mofando na fila por 10 ticks
        self.p_user3.wait_time = 10 
        
        # O Dispatcher roda a verificação
        self.scheduler.update_wait_times_and_age()
        
        # O processo deve ter sido promovido:
        # Prioridade cai de 3 para 2, e ele sobe para a fila user_queues[1]
        self.assertEqual(self.p_user3.priority, 2)
        self.assertEqual(len(self.scheduler.user_queues[1]), 1)
        self.assertEqual(len(self.scheduler.user_queues[2]), 0)

if __name__ == '__main__':
    unittest.main()