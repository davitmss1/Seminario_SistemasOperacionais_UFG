"""Aguarda a bateria terminar e produz resultados finais validados."""
import json
import subprocess
import sys
import time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folder=root/'resultados_linux/coleta_completa_20261118'
while True:
    env=json.loads((folder/'ambiente.json').read_text(encoding='utf-8'))
    if env['status']=='concluido':break
    if env['status']!='em_execucao':raise RuntimeError(env.get('erro',env['status']))
    time.sleep(10)
for script,args in [('analisar.py',[str(folder)]),('validar.py',[str(folder)]),('resumir_coleta.py',[str(folder)]),('graficos.py',[str(folder)]),('documentar_coleta.py',[]),('atualizar_roteiro_ram.py',[])]:
    print('Executando '+script,flush=True)
    subprocess.run([sys.executable,str(root/'linux_memoria'/script),*args],check=True,cwd=root)
print('FINALIZACAO_RAM_OK',flush=True)
