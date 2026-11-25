"""Bateria CUDA, com um processo por caso e retomada de casos incompletos."""
import argparse,csv,json,subprocess,time,sys,hashlib,platform,shutil
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent

def utc(): return datetime.now(timezone.utc).isoformat()
def save(p,obj):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False));tmp.replace(p)
def cmd(*args): return subprocess.check_output(args,text=True).strip()
def run_case(a,root,binary,size,pattern,rep,algo):
    name=f'{size:04d}MiB_{pattern}_r{rep}_{algo}'; folder=root/name
    if folder.exists():
        meta=folder/'caso.json'
        if meta.exists() and json.loads(meta.read_text()).get('status')=='concluido': return
        dest=root/'.interrompidos'/f'{name}_{time.time_ns()}';dest.parent.mkdir(exist_ok=True);folder.rename(dest)
    folder.mkdir(); m=dict(caso=name,carga_mib=size,padrao=pattern,repeticao=rep,algoritmo=algo,semente=a.semente,status='em_execucao',inicio_utc=utc());save(folder/'caso.json',m)
    proc=None;events=[];rows=[]
    def baseline(phase):
        start=time.monotonic()
        while time.monotonic()-start<a.baseline:
            rows.append(dict(evento=phase,monotonic_s=time.monotonic(),residentes=0));time.sleep(a.intervalo)
    try:
        baseline('baseline')
        with (folder/'eventos.jsonl').open('w') as log,(folder/'stderr.txt').open('w') as err:
            proc=subprocess.Popen([str(binary),str(size),pattern,str(a.duracao),str(a.semente),str(a.taxa),algo,str(a.intervalo)],stdout=subprocess.PIPE,stderr=err,text=True)
            for line in proc.stdout:
                log.write(line);log.flush(); e=json.loads(line);events.append(e)
                if 'monotonic_s' in e: rows.append(e)
            rc=proc.wait();m['exit_code']=rc
            if rc or not any(e['evento']=='fim' for e in events) or not any(e['evento']=='validacao_dados' and e['ok'] for e in events): raise RuntimeError(f'Falha CUDA: {rc}; veja {folder}/stderr.txt')
        baseline('liberado');m['status']='concluido'
    except BaseException:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
        m['status']='interrompido';raise
    finally:
        keys=list(dict.fromkeys(k for r in rows for k in r))
        if keys:
            with (folder/'amostras.csv').open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
        m['eventos']=events;m['fim_utc']=utc();save(folder/'caso.json',m)
    print(name+': concluido',flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--saida',required=True);p.add_argument('--retomar',action='store_true');p.add_argument('--cargas-mib',nargs='+',type=int,default=[256,512,768,1024,1536]);p.add_argument('--padroes',nargs='+',choices=['sequencial','localidade','pseudoaleatorio'],default=['sequencial','localidade','pseudoaleatorio']);p.add_argument('--repeticoes',type=int,default=3);p.add_argument('--duracao',type=float,default=60);p.add_argument('--intervalo',type=float,default=.5);p.add_argument('--baseline',type=float,default=3);p.add_argument('--taxa',type=int,default=50000);p.add_argument('--semente',type=int,default=336);a=p.parse_args();root=Path(a.saida).resolve();binary=root/'carga'
    if a.retomar:
        info=json.loads((root/'ambiente.json').read_text());
        for k,v in info['parametros'].items():setattr(a,k,v)
        if not binary.exists() or hashlib.sha256(binary.read_bytes()).hexdigest()!=info['sha256_binario']:raise RuntimeError('Binario ausente ou alterado')
        info.setdefault('retomadas',[]).append(utc())
    else:
        if any(x<4 or x>2048 or x%4 for x in a.cargas_mib) or min(a.repeticoes,a.duracao,a.intervalo,a.baseline,a.taxa)<=0 or not 0<=a.semente<2**64:p.error('Parametros invalidos')
        root.mkdir(parents=True,exist_ok=False)
        subprocess.run(['nvcc','-O2','-std=c++17','-arch=sm_120',str(HERE/'carga.cu'),'-o',str(binary)],check=True)
        info=dict(parametros={k:v for k,v in vars(a).items() if k not in ('saida','retomar')},inicio_utc=utc(),ambiente=dict(sistema=platform.platform(),gpu=cmd('nvidia-smi'),cuda=cmd('nvcc','--version'),meminfo=Path('/proc/meminfo').read_text()),sha256_binario=hashlib.sha256(binary.read_bytes()).hexdigest(),bloco_bytes=4*2**20,capacidade_blocos=256)
    info['status']='em_execucao';save(root/'ambiente.json',info)
    try:
        for rep in range(1,a.repeticoes+1):
            def rotate(xs):i=(rep-1)%len(xs);return xs[i:]+xs[:i]
            for size in rotate(a.cargas_mib):
                for pat in rotate(a.padroes):
                    for algo in (['FIFO','LRU'] if rep%2 else ['LRU','FIFO']):run_case(a,root,binary,size,pat,rep,algo)
        info['status']='concluido'
    except BaseException:info['status']='interrompido';raise
    finally:info['fim_utc']=utc();save(root/'ambiente.json',info)
if __name__=='__main__':main()
