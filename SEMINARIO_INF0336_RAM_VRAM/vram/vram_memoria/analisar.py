"""Replay independente usando comum.py original; gera CSVs apenas de casos completos."""
import argparse,csv,json
from pathlib import Path
from comum import acessos,resumo_politicas

def write(path,rows):
    if not rows:raise RuntimeError('Sem dados')
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def analyze(root):
    env=json.loads((root/'ambiente.json').read_text());p=env['parametros'];cap=env['capacidade_blocos'];b=env['bloco_bytes'];real=[];sim=[];seen=set()
    for path in sorted(root.glob('*/caso.json')):
        m=json.loads(path.read_text());
        if m['status']!='concluido':continue
        key=(m['carga_mib'],m['padrao'],m['repeticao'],m['algoritmo']);assert key not in seen;seen.add(key)
        e=next(x for x in m['eventos'] if x['evento']=='fim');v=next(x for x in m['eventos'] if x['evento']=='validacao_dados');n=e['acessos'];assert n>0 and v['ok'] and m['exit_code']==0
        states,count,h=resumo_politicas(acessos(m['padrao'],m['carga_mib']//4,n,m['semente']),[cap]);s=states[cap];algo=m['algoritmo'];miss=s[algo.lower()+'_faltas'];resident=len(s['fila'] if algo=='FIFO' else s['lru']);assert count==n and h==e['hash_blocos'],path
        assert e['faltas']==miss and e['acertos']==n-miss and e['residentes']==resident and e['substituicoes']==miss-resident,path
        assert e['h2d_bytes']==miss*b and e['d2h_bytes']==e['substituicoes']*b and v['flush_final_bytes']==resident*b,path
        base={k:m[k] for k in ('caso','carga_mib','padrao','repeticao','algoritmo')}
        real.append(dict(**base,**{k:e[k] for k in ('acessos','acertos','faltas','substituicoes','duracao_real_s','h2d_bytes','d2h_bytes','h2d_s','d2h_s','kernel_sync_s','residentes','hash_blocos')},acessos_por_s=n/e['duracao_real_s'],taxa_faltas_pct=100*miss/n,faltas_por_1000_acessos=1000*miss/n,ocupacao_logica_mib=resident*4,blocos_so_ram=m['carga_mib']//4-resident,flush_final_bytes=v['flush_final_bytes'],flush_final_s=v['flush_final_s'],hash_verificado=True))
        for policy in ('FIFO','LRU'):
            f=s[policy.lower()+'_faltas'];sim.append(dict(caso=m['caso'],carga_mib=m['carga_mib'],padrao=m['padrao'],repeticao=m['repeticao'],algoritmo_real=algo,algoritmo=policy,capacidade_logica_mib=cap*4,acessos=n,faltas=f,taxa_faltas_pct=100*f/n,hash_blocos=h))
        print(m['caso']+': validado',flush=True)
    expected={(size,pat,rep,algo) for size in p['cargas_mib'] for pat in p['padroes'] for rep in range(1,p['repeticoes']+1) for algo in ('FIFO','LRU')}
    assert seen<=expected
    if env['status']=='concluido':assert seen==expected,'Casos ausentes'
    write(root/'resumo_real.csv',real);write(root/'fifo_lru.csv',sim)
    report=dict(casos=len(real),esperados=len(expected),acessos=sum(x['acessos'] for x in real),simulacoes=len(sim),completo=seen==expected,hashes_ok=True,contadores_ok=True,dados_ok=True);(root/'validacao.json').write_text(json.dumps(report,indent=2));print(report)

def main():
    p=argparse.ArgumentParser();p.add_argument('pasta',type=Path);analyze(p.parse_args().pasta)
if __name__=='__main__':main()
