import sys
from coletar import main
if len(sys.argv)!=2:raise SystemExit('Uso: python3 vram_memoria/retomar_coleta.py PASTA')
sys.argv=[sys.argv[0],'--saida',sys.argv[1],'--retomar'];main()
