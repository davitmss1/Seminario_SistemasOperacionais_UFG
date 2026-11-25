"""Valida completude e consistência interna de uma coleta Linux analisada."""
import argparse
import csv
import json
from pathlib import Path


def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pasta');a=p.parse_args()
    root=Path(a.pasta)
    env=json.loads((root/'ambiente.json').read_text(encoding='utf-8'))
    assert env['status']=='concluido',env.get('erro')
    params=env['parametros']
    expected=len(params['cargas_mib'])*len(params['padroes'])*params['repeticoes']
    files=list(root.glob('*/caso.json'))
    assert len(files)==expected,(len(files),expected)
    summary=rows(root/'resumo_real.csv')
    assert len(summary)==expected
    assert all(r['hash_verificado']=='True' for r in summary)
    total_samples=0
    total_accesses=0
    for casefile in files:
        case=json.loads(casefile.read_text(encoding='utf-8'))
        assert case['status']=='concluido' and case['exit_code']==0,case['caso']
        events=case['eventos']
        assert [e['evento'] for e in events]==['inicializacao','acessos','fim']
        assert events[0]['paginas']*case['pagina_bytes']==case['carga_mib']*2**20
        assert not events[-1]['interrompido']
        assert events[-1]['acessos']>0
        assert events[-1]['major_faults_acessos']>=0
        data=rows(casefile.parent/'amostras.csv')
        assert any(r['fase']=='baseline' for r in data)
        assert any(r['fase']=='acessos' for r in data)
        assert any(r['fase']=='liberado' for r in data)
        times=[float(r['monotonic_s']) for r in data]
        assert all(b>a for a,b in zip(times,times[1:]))
        assert all(int(r['MemTotal_bytes'])<=2**30 for r in data) or params['permitir_mais_ram']
        assert all(int(r['SwapTotal_bytes'])>=2**31 for r in data)
        assert case['depois']['oom_kill']==case['antes']['oom_kill'],'Houve OOM global durante o caso'
        total_samples+=len(data);total_accesses+=events[-1]['acessos']
    simulations=rows(root/'fifo_lru.csv')
    by_name={r['caso']:int(r['acessos']) for r in summary}
    for r in simulations:
        assert int(r['acessos'])==by_name[r['caso']]
        assert 0<=int(r['faltas'])<=int(r['acessos'])
        assert abs(float(r['taxa_faltas_pct'])-100*int(r['faltas'])/int(r['acessos']))<1e-9
    print(f'OK: {expected} casos, {total_samples} amostras, {total_accesses} acessos e {len(simulations)} simulações. Hashes conferidos e sem OOM global nos casos.')


if __name__=='__main__':main()
