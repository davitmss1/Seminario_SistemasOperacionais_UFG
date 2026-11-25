"""Repete a validacao independente e exige a matriz completa."""
import argparse,json
from pathlib import Path
from analisar import analyze
p=argparse.ArgumentParser();p.add_argument('pasta',type=Path);a=p.parse_args();analyze(a.pasta);assert json.loads((a.pasta/'validacao.json').read_text())['completo'],'Bateria incompleta'
