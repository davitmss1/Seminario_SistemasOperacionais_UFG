"""Retoma casos pendentes sem alterar os casos concluídos."""
import argparse
import json
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
from coletar import ambiente, executar_caso, salvar

p=argparse.ArgumentParser();p.add_argument('pasta',type=Path);root=p.parse_args().pasta.resolve()
info=json.loads((root/'ambiente.json').read_text(encoding='utf-8'))
args=SimpleNamespace(**info['parametros']);now=ambiente()
assert now['meminfo']['MemTotal']<=2**30 and now['meminfo']['SwapTotal']>=2**31
assert now['pagina_bytes']==info['ambiente']['pagina_bytes']
assert now['sha256']==info['ambiente']['sha256'],'Código da carga/coleta mudou'
info.setdefault('retomadas',[]).append({'utc':datetime.now(timezone.utc).isoformat(),'ambiente':now,'motivo':'Processo anterior deixou de executar; preservar concluídos e repetir pendentes.'})
info['status']='em_execucao';salvar(root/'ambiente.json',info)
try:
    for rep in range(1,args.repeticoes+1):
        loads=args.cargas_mib[(rep-1)%len(args.cargas_mib):]+args.cargas_mib[:(rep-1)%len(args.cargas_mib)]
        patterns=args.padroes[(rep-1)%len(args.padroes):]+args.padroes[:(rep-1)%len(args.padroes)]
        for size in loads:
            for pattern in patterns:
                folder=root/f'{size:04d}MiB_{pattern}_r{rep}'
                if (folder/'caso.json').exists():
                    case=json.loads((folder/'caso.json').read_text(encoding='utf-8'))
                    if case['status']=='concluido':continue
                    dest=root/'.interrompidos'/folder.name
                    assert folder.resolve().is_relative_to(root) and dest.resolve().is_relative_to(root)
                    dest.parent.mkdir(exist_ok=True);folder.rename(dest)
                print(f'Retomando {size} MiB / {pattern} / repetição {rep}',flush=True)
                if executar_caso(args,root/'carga',root,size,pattern,rep)!='concluido':raise RuntimeError('Caso falhou')
    info['status']='concluido';info['casos_concluidos']=len(list(root.glob('*/caso.json')))
except BaseException as exc:
    info['status']='interrompido';info['erro']=str(exc);raise
finally:
    info['fim_utc']=datetime.now(timezone.utc).isoformat();salvar(root/'ambiente.json',info)
