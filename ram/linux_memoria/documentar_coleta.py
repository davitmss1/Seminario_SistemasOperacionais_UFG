"""Atualiza documentação de RAM somente após validação da coleta completa."""
import json
import shutil
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'resultados_linux/coleta_completa_20261118'
d=json.loads((FOLDER/'dados_apresentacao.json').read_text(encoding='utf-8'))
assert d['casos']==45 and d['simulacoes']==270
fmt=lambda x:f'{x:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
names={'sequencial':'Sequencial','localidade':'Localidade','pseudoaleatorio':'Pseudoaleatório'}
report=ROOT/'Relatorio_Tecnico_Seminario_INF0336_Revisado (1).md'
backup=ROOT/'historico/relatorio_ram_preliminar_18_casos.md'
if not backup.exists():shutil.copy2(report,backup)
old=report.read_text(encoding='utf-8')
references=old.split('## Referências',1)[1]
team=old.split('## Equipe',1)[1].split('## Resumo',1)[0]
lines=['# INF0336 - Gerenciamento de memória','', '## Equipe',team,
'## Escopo e cronograma','',
'O trabalho passa a duas apresentações: RAM em 19/11/2026, com a bateria ampliada concluída; VRAM e comparação entre os experimentos na apresentação seguinte. O experimento de substituição de blocos em VRAM ainda será implementado e executado.','',
'## Objetivo e método','',
'Investigar como a carga e a localidade afetam paginação real no Ubuntu/WSL 2 e relacionar os acessos a FIFO/LRU. Memória virtual, conjunto de trabalho e substituição fundamentam a análise (Arpaci-Dusseau e Arpaci-Dusseau, 2018; Denning, 1968; Belady, 1966; Maziero, 2019).','',
f'A bateria de RAM concluiu 45 casos: 256, 512, 768, 1024 e 1536 MiB, padrões sequencial, localidade e pseudoaleatório, três repetições e 60 segundos por fase de acessos. Teto oferecido: 50.000 acessos/s. Coleta a cada 0,5 s, baseline de 3 s antes e depois. A VM limitada a 1 GiB reportou {fmt(d["memtotal_mib"])} MiB de MemTotal, com 2 GiB de swap. A configuração original do WSL deve ser restaurada após a execução.','',
'O programa C usa mmap privado anônimo, preenche todos os bytes com dados pseudoaleatórios e solicita MADV_NOHUGEPAGE. Cada referência lê e altera um byte de uma página de 4 KiB. Localidade concentra cerca de 90% das escolhas nos primeiros 5% das páginas. A semente é 336. Processo novo por caso e ordem rotacionada entre repetições. A duração real pode superar ligeiramente 60 s ao concluir lotes.','',
'O coletor Python registra RSS e swap do processo, contadores globais de swap e PSI. getrusage mede faltas da fase de acessos excluindo inicialização. Deltas globais de swap e PSI incluem baseline/inicialização e outros processos. Análise offline reproduz o prefixo efetivamente executado e confere seu hash; não há rastreamento de todas as instruções de memória.','',
'## Retomada da execução','',
'A execução inicial terminou antes do fim da bateria, com 41 casos completos. O caso parcial foi preservado em .interrompidos e repetido integralmente, junto aos três casos restantes, após reiniciar o ambiente. Os 45 casos analisados estão completos. ambiente.json registra a retomada e sua configuração. Essa mudança de estado do sistema é uma limitação adicional na interpretação da terceira repetição.','',
'## Resultados reais','',
f'Validação: {d["casos"]} casos, {d["amostras"]} amostras, {d["acessos"]} acessos e {d["simulacoes"]} simulações. Hashes conferidos. {d["casos_com_swap"]} casos registraram aumento dos contadores globais de entrada e saída de swap.','',
'Médias de três repetições. Faixa mínimo–máximo descreve a dispersão observada, não intervalo de confiança.','',
'| Carga MiB | Padrão | Acessos/s médio | Mínimo | Máximo | Faltas maiores/1000 | Pico VmSwap médio MiB |',
'|---:|---|---:|---:|---:|---:|---:|']
for r in d['real']:
    lines.append(f'| {r["carga"]} | {names[r["padrao"]]} | '+ ' | '.join(fmt(r[k]) for k in ['acessos_por_s','acessos_por_s_min','acessos_por_s_max','major_faults_por_1000_acessos','pico_VmSwap_mib'])+' |')
lines+=['','![Medições reais](resultados_linux/coleta_completa_20261118/paginacao_real.png)','',
'## FIFO e LRU','',
'Capacidades lógicas: 128, 256 e 512 MiB (32768, 65536 e 131072 quadros). Simuladores começam vazios; a carga Linux já inicializou páginas. Não houve alteração da política do kernel. Resultados abaixo: taxas médias de faltas simuladas para carga de 1536 MiB.','',
'| Padrão | Capacidade MiB | FIFO % | LRU % |','|---|---:|---:|---:|']
for r in d['sim']:
    if r['carga']==1536:lines.append(f'| {names[r["padrao"]]} | {r["cap_mib"]} | {fmt(r["FIFO"])} | {fmt(r["LRU"])} |')
lines+=['','## Pressão de memória e limitações','',
'PSI abaixo representa segundos acumulados de pressão global (some/full), do snapshot anterior ao caso até a saída da carga. Inclui inicialização; não é porcentagem dos 60 segundos de acessos.','',
'| Carga MiB | Padrão | PSI some médio s | PSI full médio s |','|---:|---|---:|---:|']
for r in d['real']:
    p=[x for x in d['psi'] if x['carga']==r['carga'] and x['padrao']==r['padrao']]
    vals=[fmt(mean(x[k] for x in p)) if all(x[k] is not None for x in p) else 'N/D' for k in ['some_stall_s','full_stall_s']]
    lines.append(f'| {r["carga"]} | {names[r["padrao"]]} | {vals[0]} | {vals[1]} |')
lines+=['',
'Uma VM, três repetições e estado global persistente entre casos limitam generalização. Não interpretar 50 mil acessos/s como velocidade máxima do hardware. Faltas maiores, faltas simuladas e substituições não são equivalentes. Os contadores globais incluem outros processos e não comprovam que cada transferência atingiu fisicamente o SSD do host. A coleta curta de 18 casos permanece separada no histórico de resultados; não foi combinada às médias de 60 segundos.','',
'## Continuidade: VRAM e comparação','',
'O próximo experimento usará CUDA e orçamento de até 1 GiB para dados na GPU, com blocos de 4 MiB e RAM de apoio suficiente. FIFO/LRU escolherão vítimas na aplicação, com cópias reais RAM–VRAM e retorno de blocos alterados. Medir acertos, faltas de blocos, substituições, bytes e tempos; reproduzir a sequência no simulador. Contexto CUDA pode consumir VRAM adicional. Não apresentar esse mecanismo como paginação automática do driver nem equiparar seus blocos às páginas de 4 KiB do Linux. A comparação abordará localidade, pressão e custo de movimentação, explicitando essas diferenças.','',
'## Referências',references]
report.write_text('\n'.join(lines),encoding='utf-8')
readme=ROOT/'README.md'
readme.write_text(f'''# Gerenciamento de memória: RAM, VRAM e simuladores

## Entrega de RAM - 19/11/2026

Bateria ampliada concluída: 45 testes de 60 s, cinco cargas, três padrões e três repetições. Teto de 50.000 acessos/s. Dados anteriores de 18 testes permanecem separados.

- [Relatório técnico](Relatorio_Tecnico_Seminario_INF0336_Revisado%20(1).md)
- [Resultados completos](resultados_linux/coleta_completa_20261118/RELATORIO_LINUX.md)
- [Gráficos](resultados_linux/coleta_completa_20261118/paginacao_real.png)
- [Guia de execução](linux_memoria/README.md)

## Próxima apresentação

Implementar e executar VRAM na GPU real, comparar com os simuladores e discutir RAM versus VRAM. Essa etapa ainda não foi executada.

## Reproduzir

Configure o WSL conforme o guia. Execute no Ubuntu:

```bash
python3 linux_memoria/coletar.py --saida resultados_linux/nova_coleta --duracao 60 --repeticoes 3 --cargas-mib 256 512 768 1024 1536 --taxa 50000
```

Após a coleta, execute com Python disponível (a antiga .venv pode precisar ser recriada após atualização do runtime):

```text
python linux_memoria/analisar.py resultados_linux/nova_coleta
python linux_memoria/validar.py resultados_linux/nova_coleta
python linux_memoria/resumir_coleta.py resultados_linux/nova_coleta
python linux_memoria/graficos.py resultados_linux/nova_coleta
```

Gráficos requerem matplotlib; coleta e análise usam biblioteca padrão e gcc. Restaure a configuração original do WSL após a coleta.
''',encoding='utf-8')
print(report)
