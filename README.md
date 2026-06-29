# Pseudo-SO

Simulação de um sistema operacional multiprogramado desenvolvida em Python 3.

## Requisitos

- Python 3.10 ou superior
- Nenhuma dependência externa (apenas biblioteca padrão)

## Como executar

```bash
python dispatcher.py <processes.txt> <files.txt> <string.txt>
```

Exemplo com os arquivos de teste incluídos:

```bash
python dispatcher.py processes.txt files.txt string.txt
```

## Arquivos de entrada

### `processes.txt`
Cada linha define um processo. Os campos são separados por vírgula:

```
<tempo_de_inicialização>, <prioridade>, <tempo_de_cpu>, <tamanho_max_working_set>, <impressora>, <scanner>, <modem>, <sata>
```

- **tempo_de_inicialização**: tick em que o processo entra no sistema
- **prioridade**: `0` = tempo real (FIFO, sem preempção); `1`, `2` ou `3` = usuário
- **tempo_de_cpu**: número de instruções que o processo executa
- **tamanho_max_working_set**: número máximo de frames de memória que o processo pode usar
- **impressora / scanner / modem / sata**: `1` se o processo requisita o dispositivo, `0` caso contrário

Exemplo:
```
2, 0, 3, 4, 0, 0, 0, 0
8, 1, 5, 2, 1, 0, 0, 1
```

---

### `files.txt`
Descreve o estado inicial do disco e as operações a serem executadas.

```
<total_de_blocos>
<quantidade_de_segmentos_pre_ocupados>
<nome>, <bloco_inicial>, <quantidade_de_blocos>   ← repetido n vezes
<pid>, <operação>, <nome_arquivo>[, <blocos>]     ← uma linha por operação
```

- **operação**: `0` = criar arquivo (requer o campo `blocos`); `1` = deletar arquivo
- Processos de tempo real podem deletar qualquer arquivo; processos de usuário só deletam os próprios

Exemplo:
```
10
3
X, 0, 2
Y, 3, 1
Z, 5, 3
0, 0, A, 5
0, 1, X
1, 0, B, 2
```

---

### `string.txt`
Cada linha contém a string de referência de memória do processo correspondente (mesma ordem de `processes.txt`). Os valores são os números das páginas acessadas, separados por vírgula.

Exemplo:
```
1,2,3,4,1,2,5,1,2,3,4,5
7,0,1,2,0,3,0,4,2,3,0,3,1,0,2
```

## Como executar os testes

```bash
python test_scheduler.py
python test_memory_manager.py
python test_resource_manager.py
python test_file_system.py
```
