"""Agrega uma coleta concluída para a apresentação, incluindo variação."""
import argparse
import csv
import json
import re
from pathlib import Path
from statistics import mean, stdev

def ler(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pasta',type=Path)
    root=p.parse_args().pasta
    env=json.loads((root/'ambiente.json').read_text(encoding='utf-8'))
    assert env['status']=='concluido', 'A coleta ainda não terminou'
    real=ler(root/'resumo_real.csv');sim=ler(root/'fifo_lru.csv')
    sizes=sorted({int(r['carga_mib']) for r in real});patterns=env['parametros']['padroes']
    fields=['acessos_por_s','major_faults_acessos','major_faults_por_1000_acessos','pswpin_mib','pswpout_mib','pico_VmSwap_mib']
    out={'parametros':env['parametros'],'memtotal_mib':env['ambiente']['meminfo']['MemTotal']/2**20,'real':[],'sim':[]}
    for size in sizes:
        for pat in patterns:
            rows=[r for r in real if int(r['carga_mib'])==size and r['padrao']==pat]
            assert len(rows)==env['parametros']['repeticoes'] and all(r['hash_verificado']=='True' for r in rows)
            group=dict(carga=size,padrao=pat,n=len(rows))
            for field in fields:
                vals=[float(r[field]) for r in rows]
                group[field]=mean(vals)
                group[field+'_min']=min(vals);group[field+'_max']=max(vals)
                group[field+'_dp']=stdev(vals) if len(vals)>1 else 0
            out['real'].append(group)
    caps=sorted({int(float(r['capacidade_logica_mib'])) for r in sim})
    for size in sizes:
        for pat in patterns:
            for cap in caps:
                out['sim'].append(dict(carga=size,padrao=pat,cap_mib=cap,**{algo:mean(float(r['taxa_faltas_pct']) for r in sim if int(r['carga_mib'])==size and r['padrao']==pat and int(float(r['capacidade_logica_mib']))==cap and r['algoritmo']==algo) for algo in ['FIFO','LRU']}))
    samples=ler(root/f'{max(sizes):04d}MiB_sequencial_r1'/'amostras.csv')
    t0=float(samples[0]['monotonic_s']);page=env['ambiente']['pagina_bytes']
    out['timeline']=[dict(t=float(r['monotonic_s'])-t0,rss=float(r['VmRSS_bytes'])/2**20,swap=float(r['VmSwap_bytes'])/2**20) for r in samples if r['VmRSS_bytes'] and r['VmSwap_bytes']]
    out['io']=[dict(t=float(r['monotonic_s'])-t0,entrada=(int(r['pswpin'])-int(samples[0]['pswpin']))*page/2**20,saida=(int(r['pswpout'])-int(samples[0]['pswpout']))*page/2**20) for r in samples]
    out['casos']=len(real);out['acessos']=sum(int(r['acessos']) for r in real);out['simulacoes']=len(sim)
    out['casos_com_swap']=sum(r['swap_entrada_e_saida_observados']=='True' for r in real)
    out['amostras']=sum(len(ler(f)) for f in root.glob('*/amostras.csv'))
    out['psi']=[]
    for casefile in sorted(root.glob('*/caso.json')):
        case=json.loads(casefile.read_text(encoding='utf-8'))
        before=case['antes'].get('psi_memoria') or '';after=case['depois_carga'].get('psi_memoria') or ''
        row={'caso':case['caso'],'carga':case['carga_mib'],'padrao':case['padrao']}
        for kind in ['some','full']:
            a=re.search(rf'{kind} .*?total=(\d+)',before);b=re.search(rf'{kind} .*?total=(\d+)',after)
            row[kind+'_stall_s']=(int(b[1])-int(a[1]))/1e6 if a and b else None
        out['psi'].append(row)
    (root/'dados_apresentacao.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:out[k] for k in ['casos','acessos','simulacoes','casos_com_swap','amostras']},ensure_ascii=False))

if __name__=='__main__':main()
