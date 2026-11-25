import argparse,csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('pasta',type=Path);root=p.parse_args().pasta
with (root/'medias.csv').open() as f:rows=list(csv.DictReader(f))
for field,title,unit in [('acessos_por_s','Taxa efetiva de acessos','Acessos/s'),('taxa_faltas_pct','Faltas de blocos','%'),('substituicoes','Substituicoes','Blocos'),('h2d_bytes','Transferencias RAM para VRAM','MiB'),('d2h_bytes','Transferencias VRAM para RAM','MiB'),('h2d_s','Tempo de transferencia H2D','s'),('d2h_s','Tempo de transferencia D2H','s')]:
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained');factor=2**20 if field.endswith('_bytes') else 1
    for pat in sorted({r['padrao'] for r in rows}):
        for algo in ('FIFO','LRU'):
            rr=sorted((r for r in rows if r['padrao']==pat and r['algoritmo']==algo),key=lambda r:int(r['carga_mib']));y=[float(r[field])/factor for r in rr];lo=[float(r[field+'_min'])/factor for r in rr];hi=[float(r[field+'_max'])/factor for r in rr]
            ax.errorbar([int(r['carga_mib']) for r in rr],y,yerr=[[max(0,a-b) for a,b in zip(y,lo)],[max(0,b-a) for a,b in zip(y,hi)]],fmt='o-' if algo=='FIFO' else 's--',capsize=3,label=f'{pat} / {algo}')
    ax.set(title=title+' — VRAM 1 GiB',xlabel='Carga (MiB)',ylabel=unit);ax.grid(alpha=.2);ax.legend(fontsize=8);fig.savefig(root/f'{field}.png',dpi=160);plt.close(fig)
