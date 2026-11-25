# INF0336 - VRAM: 90 testes
Adaptacao da entrega RAM (45 casos), sem resultados pre-gerados. Execute no WSL com CUDA 13.5, RTX 5060 (sm_120). Nao aplique o limite de RAM do WSL usado na etapa anterior. O cache da aplicacao reserva 1 GiB de VRAM para dados; contexto CUDA e outros processos podem consumir memoria adicional. Cada bloco tem 4 MiB. RAM de apoio normal, inicializada com o mesmo SplitMix64 do original. Cache vazio no inicio; cada referencia altera o primeiro byte do bloco. FIFO e LRU reais; cada falta carrega um bloco inteiro; cada vitima foi alterada e retorna integralmente a RAM. Copias sincrônicas com cudaMemcpy; um kernel sincronizado por referencia. Tempos de kernel incluem lancamento e sincronizacao no host, nao apenas tempo de GPU. Flush final e verificacao dos bytes modificados ficam fora da fase medida, registrados separadamente. A ocupacao logica mede blocos validos, nao a alocacao fisica do driver. Nao se trata de paginacao automatica. O teto de 50 mil/s e aplicado em pequenos lotes de 32; resultados nao medem throughput maximo da GPU. A coleta amostra os contadores da aplicacao a cada aproximadamente 0,5 s durante acessos; baseline registra cache vazio, nao telemetria global da GPU. A duracao pode exceder ligeiramente 60 s pela ultima referencia.

## Piloto (2 cargas x 1 padrao x 2 algoritmos)
```bash
python3 vram_memoria/coletar.py --saida resultados_vram/piloto --cargas-mib 256 1536 --padroes sequencial --repeticoes 1 --duracao 5 --baseline 1
python3 vram_memoria/validar.py resultados_vram/piloto
```
Verifique faltas e substituicoes: 256 MiB nao substitui; 1536 MiB sequencial excede capacidade e deve substituir se mais de 256 referencias ocorrerem. Nao combine piloto com bateria principal.

## Bateria principal
```bash
python3 vram_memoria/coletar.py --saida resultados_vram/coleta_completa --cargas-mib 256 512 768 1024 1536 --duracao 60 --repeticoes 3 --intervalo 0.5 --baseline 3 --taxa 50000
python3 vram_memoria/validar.py resultados_vram/coleta_completa
python3 vram_memoria/resumir_coleta.py resultados_vram/coleta_completa
```
validar.py executa a analise e gera resumo_real.csv e fifo_lru.csv (duas simulacoes de capacidade 1024 MiB por caso, ambas sobre o mesmo prefixo real), alem de validacao.json. Como FIFO e LRU podem executar quantidades diferentes em 60 s, compare taxas reais e as simulacoes sobre um mesmo prefixo; nao compare totais de faltas sem considerar numero de acessos. O gerador e simulador comum.py sao copias do original RAM. Os blocos de 4 MiB nao equivalem as paginas de 4 KiB, e a limitacao logica de 1 GiB nao equivale ao limite global da VM. Nao equiparar latencias de kernels/copias sincronas com faltas maiores do Linux.

## Graficos
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 vram_memoria/graficos.py resultados_vram/coleta_completa
```
Se venv nao estiver disponivel: sudo apt install python3-venv. A coleta e validacao usam somente biblioteca padrao Python.

## Retomada
```bash
python3 vram_memoria/retomar_coleta.py resultados_vram/coleta_completa
```
Preserva casos completos e move incompletos para .interrompidos antes de repetir. Mantem parametros e verifica o binario compilado. Nao execute duas coletas na mesma pasta. Use pasta nova se a compilacao inicial falhar antes de criar ambiente.json. Feche jogos e outras cargas GPU; mantenha alimentacao e modo de energia constantes. Nao suspender a maquina durante a coleta.

## Limitacoes de validacao desta entrega
Scripts Python verificados sintaticamente; codigo CUDA requer compilacao e piloto na maquina do usuario. Nao ha medicoes reais incluidas. Os resultados do piloto e da bateria devem ser analisados antes de elaborar conclusoes.
