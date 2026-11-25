# Paginação real em Linux limitado a 1 GiB

Coleta: **concluido**. MemTotal: **897.61 MiB**. Swap total: **2048.00 MiB**.

Parâmetros: 3 repetições, duração solicitada 60.0 s por fase de acessos, teto de 50000 acessos/s. A inicialização é medida separadamente. A duração pode ultrapassar o alvo ao concluir um lote de até 256 acessos, caso haja bloqueio por I/O.

## Medições reais

| Carga MiB | Padrão | Rep. | Acessos/s | Faltas maiores na fase de acessos | Swap-in MiB¹ | Swap-out MiB¹ | Pico VmSwap MiB |
|---:|---|---:|---:|---:|---:|---:|---:|
| 256 | localidade | 1 | 49999.86 | 0 | 0.00 | 0.00 | 0.00 |
| 256 | localidade | 2 | 49999.97 | 0 | 2.57 | 0.00 | 0.00 |
| 256 | localidade | 3 | 49999.86 | 0 | 0.00 | 0.00 | 0.00 |
| 256 | pseudoaleatorio | 1 | 49999.90 | 0 | 0.00 | 0.00 | 0.00 |
| 256 | pseudoaleatorio | 2 | 49999.90 | 0 | 0.02 | 0.00 | 0.00 |
| 256 | pseudoaleatorio | 3 | 49999.79 | 0 | 0.77 | 0.00 | 0.00 |
| 256 | sequencial | 1 | 49999.97 | 0 | 0.00 | 0.00 | 0.00 |
| 256 | sequencial | 2 | 49999.87 | 0 | 0.02 | 0.00 | 0.00 |
| 256 | sequencial | 3 | 49999.74 | 0 | 0.02 | 0.00 | 0.00 |
| 512 | localidade | 1 | 49999.91 | 0 | 1.51 | 1.49 | 0.00 |
| 512 | localidade | 2 | 49999.84 | 0 | 1.11 | 0.00 | 0.00 |
| 512 | localidade | 3 | 49999.94 | 0 | 0.00 | 0.00 | 0.00 |
| 512 | pseudoaleatorio | 1 | 49999.94 | 95552 | 556.19 | 656.79 | 105.55 |
| 512 | pseudoaleatorio | 2 | 49999.93 | 0 | 0.07 | 0.00 | 0.00 |
| 512 | pseudoaleatorio | 3 | 49999.88 | 0 | 0.00 | 0.02 | 0.00 |
| 512 | sequencial | 1 | 49999.95 | 1616 | 55.71 | 75.79 | 44.06 |
| 512 | sequencial | 2 | 49999.90 | 0 | 0.32 | 0.00 | 0.00 |
| 512 | sequencial | 3 | 49999.97 | 0 | 0.00 | 0.00 | 0.00 |
| 768 | localidade | 1 | 49999.94 | 189988 | 1120.74 | 1377.98 | 538.55 |
| 768 | localidade | 2 | 49999.77 | 23171 | 94.16 | 134.51 | 51.77 |
| 768 | localidade | 3 | 49999.94 | 16377 | 90.95 | 130.30 | 51.79 |
| 768 | pseudoaleatorio | 1 | 49999.88 | 73279 | 360.22 | 399.83 | 58.82 |
| 768 | pseudoaleatorio | 2 | 49999.86 | 60623 | 337.68 | 363.47 | 65.74 |
| 768 | pseudoaleatorio | 3 | 49999.94 | 60780 | 297.14 | 331.01 | 41.80 |
| 768 | sequencial | 1 | 46782.70 | 397670 | 10473.02 | 10434.63 | 414.13 |
| 768 | sequencial | 2 | 49999.98 | 165421 | 4954.93 | 4998.66 | 49.19 |
| 768 | sequencial | 3 | 49996.20 | 162248 | 4908.86 | 4931.30 | 49.43 |
| 1024 | localidade | 1 | 49999.97 | 96726 | 393.16 | 698.30 | 311.62 |
| 1024 | localidade | 2 | 49999.79 | 94798 | 372.71 | 663.30 | 303.95 |
| 1024 | localidade | 3 | 49999.98 | 100195 | 401.77 | 704.03 | 343.07 |
| 1024 | pseudoaleatorio | 1 | 25329.21 | 405644 | 1590.69 | 1875.59 | 293.64 |
| 1024 | pseudoaleatorio | 2 | 26131.06 | 413529 | 1624.29 | 1902.12 | 293.40 |
| 1024 | pseudoaleatorio | 3 | 26283.42 | 416967 | 1636.28 | 1915.12 | 296.85 |
| 1024 | sequencial | 1 | 45151.07 | 377606 | 10684.47 | 10823.02 | 311.60 |
| 1024 | sequencial | 2 | 47929.64 | 405055 | 11376.75 | 11507.81 | 304.27 |
| 1024 | sequencial | 3 | 43942.96 | 358710 | 10457.53 | 10585.36 | 298.31 |
| 1536 | localidade | 1 | 49999.92 | 173761 | 699.02 | 1491.01 | 818.55 |
| 1536 | localidade | 2 | 49999.96 | 173363 | 684.12 | 1471.58 | 803.50 |
| 1536 | localidade | 3 | 49999.98 | 173650 | 693.64 | 1463.38 | 826.64 |
| 1536 | pseudoaleatorio | 1 | 13676.63 | 421319 | 1653.14 | 2434.97 | 817.28 |
| 1536 | pseudoaleatorio | 2 | 13002.16 | 398664 | 1562.37 | 2348.71 | 808.78 |
| 1536 | pseudoaleatorio | 3 | 13216.53 | 407009 | 1598.39 | 2392.90 | 813.36 |
| 1536 | sequencial | 1 | 38296.36 | 381415 | 9491.52 | 9796.18 | 872.31 |
| 1536 | sequencial | 2 | 45487.84 | 400295 | 10966.00 | 11481.35 | 844.40 |
| 1536 | sequencial | 3 | 47047.75 | 407877 | 11337.19 | 11851.50 | 826.46 |

**30 de 45 casos registraram aumento de swap-in e swap-out.** Esta classificação usa contadores reais, não a quantidade de RAM ocupada.

¹ Variações globais de /proc/vmstat desde antes do caso até a saída do processo; incluem inicialização e atividade de outros processos. As faltas maiores na fase de acessos vêm de getrusage do próprio processo, excluindo a inicialização. VmSwap é amostrado e seu pico pode ser subestimado.

## Simulação integrada

fifo_lru.csv contém FIFO e LRU sobre o prefixo efetivamente executado. O gerador, a semente e a contagem são registrados e o hash de 64 bits do programa C é conferido contra a reconstrução Python. Acessos lógicos são deslocamentos de páginas dentro do buffer anônimo, não números de quadros físicos. Inicialização não entra na simulação. O simulador começa vazio, enquanto a fase real começa com páginas já materializadas.

As capacidades simuladas são hipóteses explícitas. Não correspondem à RAM total menos um valor estimado para o kernel. Não se espera igualdade entre faltas FIFO/LRU e faltas reais do Linux. Nos testes de duração fixa, a quantidade efetiva de acessos pode variar; comparar taxas e contagens normalizadas, não apenas totais brutos.

## Condições e limites

- A carga usa mmap privado anônimo, preenche todos os bytes com dados pseudoaleatórios e solicita MADV_NOHUGEPAGE. Cada acesso lê e altera um byte na página escolhida.
- Localidade: aproximadamente 90% dos acessos concentrados nos primeiros 5% das páginas; os demais podem atingir todo o conjunto. O programa não escolhe quais páginas o Linux deve remover.
- O limite é da VM WSL, não do Windows inteiro. MemTotal fica abaixo de 1 GiB por reservas e overhead do kernel. Não há alteração de VRAM.
- Faltas maiores isoladas não comprovam swap. Cruzar com pswpin/pswpout e VmSwap. Swap-in/out mede o subsistema de swap do Linux; o host pode armazenar I/O em cache. Não afirmar que cada acesso chegou fisicamente ao SSD.
- Estado de zswap/zram, swappiness e THP está em ambiente.json. Indicador ausente fica indisponível, não é assumido desligado.
- Não foi usado drop_caches, swapoff, mlock ou troca da política do kernel. Cada caso usa processo novo; caches/estado global podem persistir entre casos. Baselines e ordem rotacionada ajudam a documentar essa variação.
- Os dados não mostram diretamente a identidade de cada página escolhida pelo kernel. Demonstram pressão, recuperação e faltas por meio de contadores reais.

## Arquivos

- ambiente.json: configuração, versões, hashes e estado da coleta.
- Cada pasta de caso: caso.json, amostras.csv, eventos.jsonl e stderr.txt. Casos interrompidos não são apresentados como concluídos.
- resumo_real.csv: métricas reais e evidência de swap.
- fifo_lru.csv: resultados simulados offline.
- primeiros_acessos.csv: prefixo para demonstração em sala.

Fontes técnicas: [WSL](https://learn.microsoft.com/en-us/windows/wsl/wsl-config), [proc](https://docs.kernel.org/filesystems/proc.html), [mmap](https://man7.org/linux/man-pages/man2/mmap.2.html).
