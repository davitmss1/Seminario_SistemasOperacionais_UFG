"""Reconstitui acessos, verifica hash C/Python e compara FIFO/LRU offline."""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from comum import acessos,resumo_politicas
MIB=2**20


def write_csv(path,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pasta')
    p.add_argument('--quadros',nargs='+',type=int,default=[32768,65536,131072])
    p.add_argument('--exportar-primeiros',type=int,default=100)
    args=p.parse_args()
    if min(args.quadros)<1 or args.exportar_primeiros<0:p.error('Parâmetros inválidos')
    folder=Path(args.pasta)
    env=json.loads((folder/'ambiente.json').read_text(encoding='utf-8'))
    metrics=[];simulations=[];prefixes=[]
    for casefile in sorted(folder.glob('*/caso.json')):
        case=json.loads(casefile.read_text(encoding='utf-8'))
        samples=read_csv(casefile.parent/'amostras.csv')
        init=next((e for e in case.get('eventos',[]) if e['evento']=='acessos'),{})
        end=next((e for e in case.get('eventos',[]) if e['evento']=='fim'),{})
        start=next((e for e in case.get('eventos',[]) if e['evento']=='inicializacao'),{})
        row={k:case.get(k) for k in ['caso','carga_mib','padrao','repeticao','status']}
        row.update(inicializacao_s=init.get('inicializacao_s'),acessos=end.get('acessos'),
                   duracao_real_s=end.get('duracao_real_s'),
                   major_faults_acessos=end.get('major_faults_acessos'),
                   minor_faults_acessos=end.get('minor_faults_acessos'),
                   nohugepage_ok=start.get('nohugepage_ok'),
                   hash_verificado=False)
        if end:
            row['acessos_por_s']=end['acessos']/end['duracao_real_s']
            row['major_faults_por_1000_acessos']=1000*end['major_faults_acessos']/end['acessos'] if end['acessos'] else None
        for field in ['VmRSS_bytes','VmSwap_bytes']:
            vals=[int(r[field]) for r in samples if r.get(field)]
            row['pico_'+field.replace('_bytes','_mib')]=max(vals)/MIB if vals else None
        before,after=case['antes'],case.get('depois_carga',case['depois'])
        for field in ['pswpin','pswpout','oom_kill']:
            a,b=before.get(field),after.get(field)
            row['delta_'+field]=b-a if a is not None and b is not None else None
        for field in ['pswpin','pswpout']:
            row[field+'_mib']=(row['delta_'+field]*case['pagina_bytes']/MIB) if row['delta_'+field] is not None else None
        row['swap_entrada_e_saida_observados']=bool((row.get('delta_pswpin') or 0)>0 and (row.get('delta_pswpout') or 0)>0)
        if end and case['status']=='concluido':
            states,total,hash_value=resumo_politicas(acessos(case['padrao'],start['paginas'],end['acessos'],case['seed']),args.quadros)
            if hash_value!=end['hash_paginas']:raise RuntimeError('Sequência reconstruída diverge da carga C: '+case['caso'])
            row['hash_verificado']=True
            for cap,state in states.items():
                for algo in ['FIFO','LRU']:
                    faults=state[algo.lower()+'_faltas']
                    simulations.append(dict(caso=case['caso'],carga_mib=case['carga_mib'],padrao=case['padrao'],repeticao=case['repeticao'],algoritmo=algo,quadros=cap,capacidade_logica_mib=cap*case['pagina_bytes']/MIB,acessos=total,faltas=faults,taxa_faltas_pct=100*faults/total if total else 0,hash_paginas=hash_value))
            for i,page in enumerate(acessos(case['padrao'],start['paginas'],min(end['acessos'],args.exportar_primeiros),case['seed']),1):
                prefixes.append(dict(caso=case['caso'],acesso=i,pagina_logica=page))
        metrics.append(row)
        print(f"Analisado: {row['caso']} / hash={row['hash_verificado']}",flush=True)
    write_csv(folder/'resumo_real.csv',metrics)
    write_csv(folder/'fifo_lru.csv',simulations)
    write_csv(folder/'primeiros_acessos.csv',prefixes)
    lines=['# Paginação real em Linux limitado a 1 GiB','',
           f"Coleta: **{env['status']}**. MemTotal: **{env['ambiente']['meminfo']['MemTotal']/MIB:.2f} MiB**. Swap total: **{env['ambiente']['meminfo']['SwapTotal']/MIB:.2f} MiB**.",'',
           f"Parâmetros: {env['parametros']['repeticoes']} repetições, duração solicitada {env['parametros']['duracao']} s por fase de acessos, teto de {env['parametros']['taxa']} acessos/s. A inicialização é medida separadamente. A duração pode ultrapassar o alvo ao concluir um lote de até 256 acessos, caso haja bloqueio por I/O.",'',
           '## Medições reais','',
           '| Carga MiB | Padrão | Rep. | Acessos/s | Faltas maiores na fase de acessos | Swap-in MiB¹ | Swap-out MiB¹ | Pico VmSwap MiB |',
           '|---:|---|---:|---:|---:|---:|---:|---:|']
    fmt=lambda v: 'N/D' if v is None else f'{v:.2f}'
    for row in metrics:
        lines.append(f"| {row['carga_mib']} | {row['padrao']} | {row['repeticao']} | {fmt(row.get('acessos_por_s'))} | {row.get('major_faults_acessos','N/D')} | {fmt(row.get('pswpin_mib'))} | {fmt(row.get('pswpout_mib'))} | {fmt(row.get('pico_VmSwap_mib'))} |")
    count=sum(r['swap_entrada_e_saida_observados'] for r in metrics)
    lines += ['',f'**{count} de {len(metrics)} casos registraram aumento de swap-in e swap-out.** Esta classificação usa contadores reais, não a quantidade de RAM ocupada.', '',
              '¹ Variações globais de /proc/vmstat desde antes do caso até a saída do processo; incluem inicialização e atividade de outros processos. As faltas maiores na fase de acessos vêm de getrusage do próprio processo, excluindo a inicialização. VmSwap é amostrado e seu pico pode ser subestimado.', '',
              '## Simulação integrada', '',
              'fifo_lru.csv contém FIFO e LRU sobre o prefixo efetivamente executado. O gerador, a semente e a contagem são registrados e o hash de 64 bits do programa C é conferido contra a reconstrução Python. Acessos lógicos são deslocamentos de páginas dentro do buffer anônimo, não números de quadros físicos. Inicialização não entra na simulação. O simulador começa vazio, enquanto a fase real começa com páginas já materializadas.', '',
              'As capacidades simuladas são hipóteses explícitas. Não correspondem à RAM total menos um valor estimado para o kernel. Não se espera igualdade entre faltas FIFO/LRU e faltas reais do Linux. Nos testes de duração fixa, a quantidade efetiva de acessos pode variar; comparar taxas e contagens normalizadas, não apenas totais brutos.', '',
              '## Condições e limites', '',
              '- A carga usa mmap privado anônimo, preenche todos os bytes com dados pseudoaleatórios e solicita MADV_NOHUGEPAGE. Cada acesso lê e altera um byte na página escolhida.',
              '- Localidade: aproximadamente 90% dos acessos concentrados nos primeiros 5% das páginas; os demais podem atingir todo o conjunto. O programa não escolhe quais páginas o Linux deve remover.',
              '- O limite é da VM WSL, não do Windows inteiro. MemTotal fica abaixo de 1 GiB por reservas e overhead do kernel. Não há alteração de VRAM.',
              '- Faltas maiores isoladas não comprovam swap. Cruzar com pswpin/pswpout e VmSwap. Swap-in/out mede o subsistema de swap do Linux; o host pode armazenar I/O em cache. Não afirmar que cada acesso chegou fisicamente ao SSD.',
              '- Estado de zswap/zram, swappiness e THP está em ambiente.json. Indicador ausente fica indisponível, não é assumido desligado.',
              '- Não foi usado drop_caches, swapoff, mlock ou troca da política do kernel. Cada caso usa processo novo; caches/estado global podem persistir entre casos. Baselines e ordem rotacionada ajudam a documentar essa variação.',
              '- Os dados não mostram diretamente a identidade de cada página escolhida pelo kernel. Demonstram pressão, recuperação e faltas por meio de contadores reais.', '',
              '## Arquivos', '',
              '- ambiente.json: configuração, versões, hashes e estado da coleta.',
              '- Cada pasta de caso: caso.json, amostras.csv, eventos.jsonl e stderr.txt. Casos interrompidos não são apresentados como concluídos.',
              '- resumo_real.csv: métricas reais e evidência de swap.',
              '- fifo_lru.csv: resultados simulados offline.',
              '- primeiros_acessos.csv: prefixo para demonstração em sala.', '',
              'Fontes técnicas: [WSL](https://learn.microsoft.com/en-us/windows/wsl/wsl-config), [proc](https://docs.kernel.org/filesystems/proc.html), [mmap](https://man7.org/linux/man-pages/man2/mmap.2.html).']
    (folder/'RELATORIO_LINUX.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(folder/'RELATORIO_LINUX.md')


if __name__=='__main__':main()
