import argparse,csv,json
from collections import defaultdict
from pathlib import Path
from statistics import mean,stdev
from analisar import write
p=argparse.ArgumentParser();p.add_argument('pasta',type=Path);root=p.parse_args().pasta
assert json.loads((root/'validacao.json').read_text())['completo'],'Bateria incompleta'
with (root/'resumo_real.csv').open() as f:rows=list(csv.DictReader(f))
groups=defaultdict(list)
for r in rows:groups[tuple(r[k] for k in ('carga_mib','padrao','algoritmo'))].append(r)
fields=['acessos_por_s','taxa_faltas_pct','faltas_por_1000_acessos','substituicoes','h2d_bytes','d2h_bytes','h2d_s','d2h_s','kernel_sync_s','ocupacao_logica_mib']
out=[]
for (size,pat,algo),rr in sorted(groups.items(),key=lambda x:(int(x[0][0]),x[0][1],x[0][2])):
    d=dict(carga_mib=size,padrao=pat,algoritmo=algo,n=len(rr))
    for k in fields:
        vals=[float(r[k]) for r in rr];d.update({k:mean(vals),k+'_min':min(vals),k+'_max':max(vals),k+'_dp':stdev(vals) if len(vals)>1 else 0})
    out.append(d)
write(root/'medias.csv',out);(root/'dados_apresentacao.json').write_text(json.dumps(out,indent=2));print('Grupos:',len(out))
