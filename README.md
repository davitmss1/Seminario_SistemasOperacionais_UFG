# INF0336 - Seminário

## Gerenciamento de memória: RAM, VRAM e algoritmos de substituição

## Equipe:

- 202401768 - Davi Torres de Mesquita da Silveira e Silva
- 202406915 - Diogo de Souza Alves
- 202401823 - Rafael Augusto Dias Batista
- 202406924 - Pedro Henrique Rezende de Melo

## Apresentações

1. [Primeira semana — Gerenciamento de memória e virtualização (PDF)](apresentacoes/Slides_Primeira_Semana.pdf)
2. [Segunda semana — Fundamentação e metodologia (PDF)](apresentacoes/Slides_Segunda_Semana.pdf)
3. [Terceira semana — Paginação real com 1 GiB de RAM: resultados e comparação entre FIFO e LRU](apresentacoes/Slides_Terceira_Semana.pdf)

## Resumo

RAM e VRAM têm capacidade limitada, o que pode exigir a movimentação de dados. O trabalho investiga os efeitos da carga, do padrão de acesso e da política de substituição. Foram realizados 45 testes de RAM no Ubuntu/WSL 2 e 90 de VRAM com CUDA, além de simulações de FIFO e LRU. Esperava-se que a localidade reduzisse as faltas e favorecesse LRU. Os resultados confirmaram essa hipótese nas cargas maiores, enquanto os algoritmos tiveram taxas de faltas próximas no padrão pseudoaleatório. O desempenho depende da capacidade, da localidade e do custo das transferências.

## Introdução

**Motivação.** A memória virtual permite ao sistema operacional organizar os endereços dos processos e administrar a RAM. Quando faltam páginas, recuperá-las pode aumentar o custo dos acessos. Na GPU, a movimentação de dados entre RAM e VRAM também pode reduzir o desempenho.

**Revisão bibliográfica.** Arpaci-Dusseau e Arpaci-Dusseau (2018) e Maziero (2019) explicam memória virtual, paginação e proteção. Denning (1968) apresenta o conjunto de trabalho, relacionado à localidade. Belady (1966) estuda políticas de substituição. Ausavarungnirun et al. (2017), no trabalho Mosaic, discutem o gerenciamento de memória em GPUs e os efeitos do tamanho das páginas.

**Objetivos.** Investigar a paginação real da RAM e a substituição de blocos na VRAM, comparar FIFO e LRU e relacionar as medições às simulações e à literatura.

## Metodologia

**Conjunto de dados.** Foram testadas cinco cargas (256, 512, 768, 1024 e 1536 MiB), três padrões (sequencial, localidade e pseudoaleatório) e três repetições de 60 s. A coleta ocorreu a cada 0,5 s, com baseline de 3 s antes e depois, teto de 50.000 acessos/s e semente 336. O padrão de localidade concentra cerca de 90% dos acessos nos primeiros 5% das unidades de memória. Os [dados da RAM](ram/resultados_linux/coleta_completa_20261118/), os [dados da VRAM](vram/resultados_vram/coleta_completa/) e as [instruções de reprodução](REPRODUCAO.md) estão no repositório.

**Modelos.** FIFO retira o item que entrou primeiro; LRU retira o item usado menos recentemente. Cada referência lê e altera um byte. Os testes foram executados em processos novos, com ordem alternada entre repetições.

- **RAM:** Ubuntu/WSL 2 limitado a 1 GiB (897,61 MiB reportados), com 2 GiB de swap. O programa C inicializa a carga usando `mmap`, com páginas de 4 KiB. O Linux controla a paginação; FIFO e LRU são simulados em Python com capacidades de 128, 256 e 512 MiB.
- **VRAM:** RTX 5060, CUDA 13.5 e WSL 2 com 7,5 GiB de RAM. O programa limita os dados na GPU a 1 GiB (256 blocos de 4 MiB), inicialmente vazios. Em uma falta, copia o bloco da RAM; se a área estiver cheia, FIFO ou LRU escolhe o bloco a devolver à RAM. As duas políticas são executadas e simuladas.

**Métricas.** Acessos/s, faltas por mil acessos e taxas de faltas simuladas. Na RAM, o coletor registra faltas maiores (`getrusage`), VmSwap, contadores de swap e PSI. Na VRAM, registra faltas de blocos, substituições e tempos de cópia. A reconstrução das sequências confere hashes; na VRAM, também são conferidos os contadores e dados alterados.

**Fluxograma**

<img src="imagens/fluxograma.png" alt="Fluxograma das etapas do projeto" width="350">

## Resultados

Foram validados 45 testes de RAM (121.940.224 acessos e 270 simulações) e 90 de VRAM (188.884.795 acessos e 180 simulações). Em 30 testes de RAM houve aumento dos contadores globais de entrada e saída de swap. Na VRAM, houve substituições em 18 testes, todos com 1536 MiB.

### Desempenho real

Até 1024 MiB, a VRAM manteve cerca de 42 mil acessos/s, sem substituições. Na RAM, a carga pseudoaleatória caiu para 25.915 acessos/s em 1024 MiB. A tabela destaca a carga de 1536 MiB (médias de três repetições, valores arredondados).

| Padrão | RAM acessos/s | VRAM FIFO acessos/s | VRAM LRU acessos/s |
|---|---:|---:|---:|
| Sequencial | 43.611 | 938 | 918 |
| Localidade | 50.000 | 15.785 | 16.833 |
| Pseudoaleatório | 13.298 | 2.662 | 2.732 |

[Gráfico da paginação real na RAM](ram/resultados_linux/coleta_completa_20261118/paginacao_real.png).

<img src="vram/resultados_vram/coleta_completa/acessos_por_s.png" alt="Taxa efetiva de acessos na VRAM" width="500">

### FIFO e LRU

Taxas médias de faltas simuladas (%) para a carga de 1536 MiB. A RAM utiliza capacidades simuladas menores; na VRAM, a capacidade é a mesma do experimento real. As faltas reais da política executada na VRAM coincidiram com a simulação correspondente.

| Padrão | RAM FIFO 128 MiB | RAM LRU 128 MiB | VRAM FIFO 1024 MiB | VRAM LRU 1024 MiB |
|---|---:|---:|---:|---:|
| Sequencial | 100,00 | 100,00 | 100,00 | 100,00 |
| Localidade | 19,73 | 9,99 | 3,62 | 3,34 |
| Pseudoaleatório | 91,84 | 91,85 | 33,54 | 33,56 |

[Gráfico das faltas na VRAM](vram/resultados_vram/coleta_completa/taxa_faltas_pct.png).

**Pressão de memória.** Em 1536 MiB, o pseudoaleatório na RAM apresentou 512,49 faltas maiores por mil acessos e pico médio de VmSwap de 813,14 MiB. O PSI some médio foi de 3,25 s nesse padrão e de 1,52 s com localidade. Na VRAM, 512 MiB ficaram não residentes ao final dos acessos. Com FIFO, as cópias nos dois sentidos consumiram cerca de 54,56 s no sequencial, 33,11 s com localidade e 51,92 s no pseudoaleatório. O PSI do Linux e os tempos de cópia da GPU não são medidas equivalentes.

## Discussão

A localidade apresentou o melhor desempenho na maior carga nos dois ambientes, como esperado pelo conceito de conjunto de trabalho de Denning (1968). LRU favorece a permanência dos itens usados recentemente, o que ajuda a explicar sua menor taxa de faltas nesse padrão (Belady, 1966; Arpaci-Dusseau e Arpaci-Dusseau, 2018; Maziero, 2019). No pseudoaleatório, FIFO e LRU tiveram taxas próximas.

O pior padrão foi o pseudoaleatório na RAM e o sequencial na VRAM. Neste último, a carga percorre 384 blocos com espaço para apenas 256. Cada referência encontra o bloco ausente, exigindo novas cópias. O custo de transferir blocos de 4 MiB ajuda a explicar a queda de desempenho, em linha com a discussão de Ausavarungnirun et al. (2017).

**Limitações.** Uma VM, uma GPU e três repetições limitam a generalização. A coleta de RAM foi retomada após 41 casos completos; os quatro restantes foram executados após reiniciar o ambiente. PSI e swap incluem atividade de outros processos e não comprovam acesso físico ao SSD. Na VRAM, cada referência lança e sincroniza um kernel, e o limite é imposto pela aplicação, não pelo driver. As faltas maiores da RAM não equivalem às faltas de blocos da VRAM. O teto de acessos não representa a velocidade máxima do hardware.

## Conclusão

Os objetivos foram alcançados dentro do protocolo adotado. A localidade reduziu o impacto da falta de memória, e LRU apresentou vantagem sobre FIFO nesse padrão. As simulações ajudaram a interpretar e validar os experimentos. As diferenças de tamanho das unidades, de estado inicial e de mecanismos de substituição impedem concluir diretamente qual memória é fisicamente mais rápida.

## Referências

ARPACI-DUSSEAU, Remzi H.; ARPACI-DUSSEAU, Andrea C. **Operating systems: three easy pieces**. [S. l.]: Arpaci-Dusseau Books, 2018. Disponível em: https://pages.cs.wisc.edu/~remzi/OSTEP/. Acesso em: 4 nov. 2026.

AUSAVARUNGNIRUN, Rachata et al. Mosaic: a GPU memory manager with application-transparent support for multiple page sizes. In: IEEE/ACM INTERNATIONAL SYMPOSIUM ON MICROARCHITECTURE, 50., 2017, Cambridge. *Proceedings [...]*. [S. l.]: ACM, 2017. p. 136-150. DOI: 10.1145/3123939.3123975. Disponível em: https://doi.org/10.1145/3123939.3123975. Acesso em: 25 nov. 2026.

BELADY, L. A. A study of replacement algorithms for a virtual-storage computer. *IBM Systems Journal*, v. 5, n. 2, p. 78-101, 1966. DOI: 10.1147/sj.52.0078. Disponível em: https://doi.org/10.1147/sj.52.0078. Acesso em: 4 nov. 2026.

DENNING, Peter J. The working set model for program behavior. *Communications of the ACM*, v. 11, n. 5, p. 323-333, 1968. DOI: 10.1145/363095.363141. Disponível em: https://doi.org/10.1145/363095.363141. Acesso em: 4 nov. 2026.

LINUX MAN-PAGES. **mmap(2)**. Disponível em: https://man7.org/linux/man-pages/man2/mmap.2.html. Documentação do mapeamento de memória.

MAZIERO, Carlos Alberto. **Sistemas operacionais: conceitos e mecanismos**. Curitiba: DINF/UFPR, 2019. Disponível em: https://wiki.inf.ufpr.br/maziero/doku.php?id=so:livro_de_sistemas_operacionais. Acesso em: 4 nov. 2026.

MICROSOFT. **Advanced settings configuration in WSL**. Disponível em: https://learn.microsoft.com/en-us/windows/wsl/wsl-config. Documentação de configuração do ambiente.

THE LINUX KERNEL. **The /proc filesystem**. Disponível em: https://docs.kernel.org/filesystems/proc.html. Documentação dos indicadores de memória e processo.
