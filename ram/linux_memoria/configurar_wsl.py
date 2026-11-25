"""Aplica/restaura configuração WSL preservando arquivo original em backup local."""
import argparse
import base64
import configparser
import hashlib
import io
import json
import os
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
BACKUP=HERE/'backup_wslconfig.json'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('acao',choices=['aplicar','restaurar','status'])
    a=p.parse_args()
    if os.name!='nt':p.error('Execute este utilitário no Windows')
    config=Path.home()/'.wslconfig'
    if a.acao=='status':
        print(config)
        print(config.read_text(encoding='utf-8-sig') if config.exists() else '(sem arquivo)')
        print('Backup ativo:',BACKUP.exists())
        return
    if a.acao=='aplicar':
        if BACKUP.exists():raise RuntimeError('Já há backup ativo. Restaure antes de reaplicar.')
        original=config.read_bytes() if config.exists() else None
        parser=configparser.ConfigParser(interpolation=None,strict=False)
        parser.optionxform=str
        if original is not None:
            parser.read_string(original.decode('utf-8-sig'))
        if not parser.has_section('wsl2'):parser.add_section('wsl2')
        replacements={'memory':'1GB','swap':'2GB','processors':'2','guiApplications':'false'}
        for old in list(parser['wsl2']):
            if old.lower() in {k.lower() for k in replacements}:parser.remove_option('wsl2',old)
        for k,v in replacements.items():parser.set('wsl2',k,v)
        buf=io.StringIO();parser.write(buf)
        content=buf.getvalue().encode('utf-8')
        state=dict(path=str(config),original=None if original is None else base64.b64encode(original).decode(),applied_sha256=hashlib.sha256(content).hexdigest())
        BACKUP.write_text(json.dumps(state,indent=2),encoding='utf-8')
        config.write_bytes(content)
        print(f'Configurado: {config}. Limite 1 GiB, swap 2 GiB. Reinicie o WSL para aplicar.')
    else:
        state=json.loads(BACKUP.read_text(encoding='utf-8'))
        if Path(state['path']).resolve()!=config.resolve():raise RuntimeError('Caminho de backup não corresponde ao usuário atual')
        if not config.exists() or hashlib.sha256(config.read_bytes()).hexdigest()!=state['applied_sha256']:
            raise RuntimeError('A configuração mudou após o teste. Restaurar manualmente para não perder alterações.')
        if state['original'] is None:
            config.unlink()
        else:
            config.write_bytes(base64.b64decode(state['original']))
        BACKUP.rename(HERE/('backup_wslconfig_restaurado_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.json'))
        print('Configuração original restaurada. Reinicie o WSL para aplicar.')


if __name__=='__main__':main()
