"""Gráficos opcionais offline. Requer matplotlib (já existe no .venv Windows)."""
import argparse
import csv
import os
from pathlib import Path
from statistics import mean

os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def ler(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pasta');a=p.parse_args()
    folder=Path(a.pasta);rows=ler(folder/'resumo_real.csv')
    rows=[r for r in rows if r['status']=='concluido']
    if not rows:raise RuntimeError('Sem casos concluídos')
    sizes=sorted({int(r['carga_mib']) for r in rows})
    patterns=sorted({r['padrao'] for r in rows})
    colors=['#007C83','#BE6C24','#142C40']
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for pattern,color in zip(patterns,colors):
        for ax,field,title,unit in [(axes[0,0],'acessos_por_s','Taxa efetiva de acessos','Acessos/s'),(axes[0,1],'major_faults_por_1000_acessos','Faltas maiores do processo','Faltas / 1.000 acessos')]:
            means=[];mins=[];maxs=[]
            for size in sizes:
                vals=[float(r[field]) for r in rows if r['padrao']==pattern and int(r['carga_mib'])==size and r[field]]
                means.append(mean(vals));mins.append(min(vals));maxs.append(max(vals))
            ax.errorbar(sizes,means,yerr=[[m-v for m,v in zip(means,mins)],[v-m for m,v in zip(means,maxs)]],fmt='o-',color=color,label=pattern,capsize=4)
            ax.set(title=title,xlabel='Carga (MiB)',ylabel=unit)
            ax.grid(alpha=.2)
            ax.legend(fontsize=8)
    example=next((r for r in rows if int(r['carga_mib'])==max(sizes) and r['padrao']=='sequencial'),rows[-1])
    samples=ler(folder/example['caso']/'amostras.csv')
    start=float(samples[0]['monotonic_s'])
    ax=axes[1,0]
    for field,label,color in [('VmRSS_bytes','RSS do processo','#007C83'),('VmSwap_bytes','Swap do processo','#BE6C24')]:
        valid=[r for r in samples if r[field]]
        ax.plot([float(r['monotonic_s'])-start for r in valid],[int(r[field])/2**20 for r in valid],label=label,color=color)
    ax.set(title=f"{example['carga_mib']} MiB, {example['padrao']}, rep. {example['repeticao']}",xlabel='Tempo desde baseline (s)',ylabel='Memória (MiB)')
    ax.grid(alpha=.2);ax.legend()
    ax=axes[1,1]
    for field,label,color in [('pswpin','Swap-in global','#007C83'),('pswpout','Swap-out global','#BE6C24')]:
        valid=[r for r in samples if r[field]]
        baseline=int(valid[0][field])
        # Página registrada no ambiente, sem assumir 4 KiB.
        import json
        page=json.loads((folder/'ambiente.json').read_text(encoding='utf-8'))['ambiente']['pagina_bytes']
        ax.plot([float(r['monotonic_s'])-start for r in valid],[(int(r[field])-baseline)*page/2**20 for r in valid],label=label,color=color)
    ax.set(title='Tráfego acumulado de swap no mesmo caso',xlabel='Tempo desde baseline (s)',ylabel='MiB acumulados')
    ax.grid(alpha=.2);ax.legend()
    fig.suptitle('Linux com limite de 1 GiB: medições reais\nMédia e faixa mínimo–máximo entre repetições',fontsize=15)
    fig.savefig(folder/'paginacao_real.png',dpi=160)
    plt.close(fig)
    print(folder/'paginacao_real.png')


if __name__=='__main__':main()
