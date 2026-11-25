"""Coletor Linux sem dependências externas; requer gcc para compilar carga.c."""
import argparse
import csv
import hashlib
import json
import os
import platform
import selectors
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
MIB=2**20


def texto(path):
    try:
        return Path(path).read_text().strip()
    except (OSError,PermissionError):
        return None


def chaves(path):
    result={}
    for line in (texto(path) or '').splitlines():
        parts=line.replace(':',' ').split()
        if len(parts)>=2:
            try:
                result[parts[0]]=int(parts[1])*(1024 if len(parts)>2 and parts[2]=='kB' else 1)
            except ValueError:
                pass
    return result


def proc_faults(pid):
    raw=texto(f'/proc/{pid}/stat')
    if not raw:return {}
    # Nome do processo pode conter espaços/parênteses. Campo 3 segue o último ')'.
    fields=raw[raw.rfind(')')+2:].split()
    return {'processo_minor_faults':int(fields[7]),'processo_major_faults':int(fields[9])}


def snapshot(pid=None):
    mem=chaves('/proc/meminfo')
    vm=chaves('/proc/vmstat')
    row={'utc':datetime.now(timezone.utc).isoformat(),'monotonic_s':time.monotonic()}
    for name in ['MemTotal','MemAvailable','SwapTotal','SwapFree','SwapCached','Cached','AnonPages']:
        row[name+'_bytes']=mem.get(name)
    for name in ['pswpin','pswpout','pgfault','pgmajfault','oom_kill']:
        row[name]=vm.get(name)
    row['psi_memoria']=texto('/proc/pressure/memory')
    if pid:
        status=chaves(f'/proc/{pid}/status')
        for name in ['VmRSS','VmSwap','VmSize']:
            row[name+'_bytes']=status.get(name)
        row.update(proc_faults(pid))
    return row


def salvar(path,data):
    temp=Path(str(path)+'.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(path)


def ambiente():
    return dict(sistema=platform.platform(),python=sys.version,pagina_bytes=os.sysconf('SC_PAGE_SIZE'),
                meminfo=chaves('/proc/meminfo'),swaps=texto('/proc/swaps'),
                swappiness=texto('/proc/sys/vm/swappiness'),
                zswap=texto('/sys/module/zswap/parameters/enabled'),
                thp=texto('/sys/kernel/mm/transparent_hugepage/enabled'),
                versao_kernel=texto('/proc/version'),cmdline=texto('/proc/cmdline'),
                zram=[str(p) for p in Path('/sys/block').glob('zram*')],
                cgroup=texto('/proc/self/cgroup'),
                cpu=texto('/proc/cpuinfo'),
                sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'carga.c',HERE/'coletar.py',HERE/'comum.py']})


def executar_caso(args, binary, out, carga, padrao, rep):
    name=f'{carga:04d}MiB_{padrao}_r{rep}'
    folder=out/name
    folder.mkdir()
    meta=dict(caso=name,carga_mib=carga,padrao=padrao,repeticao=rep,seed=args.semente,
              duracao_s=args.duracao,taxa_alvo=args.taxa,status='em_execucao',
              pagina_bytes=os.sysconf('SC_PAGE_SIZE'),inicio_utc=datetime.now(timezone.utc).isoformat(),
              antes=snapshot())
    salvar(folder/'caso.json',meta)
    fields=['caso','fase','utc','monotonic_s','MemTotal_bytes','MemAvailable_bytes','SwapTotal_bytes','SwapFree_bytes','SwapCached_bytes','Cached_bytes','AnonPages_bytes','pswpin','pswpout','pgfault','pgmajfault','oom_kill','psi_memoria','VmRSS_bytes','VmSwap_bytes','VmSize_bytes','processo_minor_faults','processo_major_faults']
    proc=None
    try:
        with (folder/'amostras.csv').open('w',newline='',encoding='utf-8') as f, (folder/'eventos.jsonl').open('w',encoding='utf-8') as events, (folder/'stderr.txt').open('w',encoding='utf-8') as errors:
            writer=csv.DictWriter(f,fieldnames=fields)
            writer.writeheader()
            def sample(fase,pid=None):
                writer.writerow(dict(caso=name,fase=fase,**snapshot(pid)))
                f.flush()
            start=time.monotonic()
            while time.monotonic()-start<args.baseline:
                sample('baseline')
                time.sleep(args.intervalo)
            proc=subprocess.Popen([str(binary),str(carga),padrao,str(args.duracao),str(args.semente),str(args.taxa)],stdout=subprocess.PIPE,stderr=errors,text=True,bufsize=1)
            meta['pid']=proc.pid
            sel=selectors.DefaultSelector()
            sel.register(proc.stdout,selectors.EVENT_READ)
            fase='inicializacao'
            received=[]
            start=time.monotonic()
            last=0
            while proc.poll() is None:
                for key,_ in sel.select(timeout=.05):
                    line=key.fileobj.readline()
                    if line:
                        events.write(line); events.flush()
                        event=json.loads(line)
                        received.append(event)
                        fase=event['evento']
                now=time.monotonic()
                if now-last>=args.intervalo:
                    sample(fase,proc.pid);last=now
                if now-start>args.timeout_inicializacao+args.duracao+10:
                    meta['timeout']=True
                    proc.terminate()
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait()
            for line in proc.stdout:
                if line.strip():
                    events.write(line)
                    received.append(json.loads(line))
            sel.close()
            proc.stdout.close()
            meta['eventos']=received
            meta['exit_code']=proc.returncode
            meta['depois_carga']=snapshot()
            meta['status']='concluido' if proc.returncode==0 and any(e['evento']=='fim' for e in received) else 'falhou'
            start=time.monotonic()
            while time.monotonic()-start<args.baseline:
                sample('liberado')
                time.sleep(args.intervalo)
    except BaseException as e:
        meta['status']='interrompido'
        meta['erro']=f'{type(e).__name__}: {e}'
        if proc and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
        raise
    finally:
        meta['depois']=snapshot()
        meta['fim_utc']=datetime.now(timezone.utc).isoformat()
        salvar(folder/'caso.json',meta)
    print(f'{name}: {meta["status"]}',flush=True)
    return meta['status']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida',required=True)
    p.add_argument('--cargas-mib',nargs='+',type=int,default=[256,512,768,1024,1536])
    p.add_argument('--padroes',nargs='+',choices=['sequencial','localidade','pseudoaleatorio'],default=['sequencial','localidade','pseudoaleatorio'])
    p.add_argument('--repeticoes',type=int,default=3)
    p.add_argument('--duracao',type=float,default=60)
    p.add_argument('--intervalo',type=float,default=.5)
    p.add_argument('--baseline',type=float,default=3)
    p.add_argument('--taxa',type=int,default=20000)
    p.add_argument('--semente',type=int,default=336)
    p.add_argument('--timeout-inicializacao',type=float,default=180)
    p.add_argument('--permitir-mais-ram',action='store_true',help='Somente validação funcional fora do limite de 1 GiB')
    args=p.parse_args()
    if sys.platform!='linux':p.error('Execute no Linux/WSL 2, não no Python Windows')
    if min(args.cargas_mib+[args.repeticoes,args.taxa])<1 or max(args.cargas_mib)>2048 or min(args.duracao,args.intervalo,args.baseline,args.timeout_inicializacao)<=0 or args.intervalo>args.baseline:
        p.error('Parâmetros inválidos: cargas 1..2048 MiB e tempos/contagens positivos')
    if args.semente<0 or args.semente>=2**64:p.error('Semente deve caber em uint64')
    env=ambiente()
    mem=env['meminfo']
    if mem['MemTotal']>1024*MIB and not args.permitir_mais_ram:
        p.error('Linux tem mais de 1 GiB. Configure o ambiente ou use --permitir-mais-ram apenas para validação funcional')
    if mem.get('SwapTotal',0)<2*1024*MIB:
        p.error('Este protocolo exige pelo menos 2 GiB de swap ativo')
    if max(args.cargas_mib)*MIB>mem['MemTotal']+mem['SwapTotal']-256*MIB:
        p.error('Carga não deixa reserva suficiente de RAM+swap')
    out=Path(args.saida).resolve();out.mkdir(parents=True,exist_ok=False)
    info=dict(inicio_utc=datetime.now(timezone.utc).isoformat(),parametros=vars(args),ambiente=env,status='em_execucao')
    salvar(out/'ambiente.json',info)
    binary=out/'carga'
    subprocess.run(['gcc','-O2','-std=c11','-Wall','-Wextra',str(HERE/'carga.c'),'-o',str(binary)],check=True)
    info['sha256_binario']=hashlib.sha256(binary.read_bytes()).hexdigest()
    info['compilador']=subprocess.check_output(['gcc','--version'],text=True).splitlines()[0]
    statuses=[]
    try:
        for rep in range(1,args.repeticoes+1):
            # Rotacionar cargas e padrões entre repetições, com a mesma semente.
            loads=args.cargas_mib[(rep-1)%len(args.cargas_mib):]+args.cargas_mib[:(rep-1)%len(args.cargas_mib)]
            patterns=args.padroes[(rep-1)%len(args.padroes):]+args.padroes[:(rep-1)%len(args.padroes)]
            for size in loads:
                for pattern in patterns:
                    print(f'Executando {size} MiB / {pattern} / repetição {rep}',flush=True)
                    statuses.append(executar_caso(args,binary,out,size,pattern,rep))
                    if statuses[-1]!='concluido':raise RuntimeError('Caso falhou: dados preservados; interrompendo série')
        info['status']='concluido'
    except BaseException as e:
        info['status']='interrompido';info['erro']=f'{type(e).__name__}: {e}'
        raise
    finally:
        info['fim_utc']=datetime.now(timezone.utc).isoformat()
        info['casos_concluidos']=statuses.count('concluido')
        salvar(out/'ambiente.json',info)


if __name__=='__main__':main()
