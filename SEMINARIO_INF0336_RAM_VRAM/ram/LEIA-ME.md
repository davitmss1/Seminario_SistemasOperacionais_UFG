# Entrega de RAM: 45 testes

Material da apresentação de 19/11/2026. A próxima apresentação será de VRAM e comparação. VRAM ainda não foi executada.

## Conteúdo

- `linux_memoria/`: código efetivamente usado para carga, coleta, análise, validação, retomada e geração dos materiais. Arquivos reaproveitados continuam incluídos quando foram utilizados nesta bateria.
- `resultados_linux/coleta_completa_20261118/`: somente os 45 casos concluídos, resultados consolidados, configuração, binário Linux executado e gráfico científico `paginacao_real.png`.
- `imagens/slides/`: 14 imagens PNG da versão final dos slides, em 1920 x 1080, incluindo os gráficos editáveis renderizados na apresentação.
- `documentos/`: roteiro de sete minutos em PDF.
- Relatório técnico e roteiro em Markdown na raiz, preservando os links relativos aos resultados.
- `codigo_apresentacao/`: scripts utilizados para atualizar os slides e gerar o PDF do roteiro. O JavaScript requer a sessão da apresentação e o objeto D carregado de dados_apresentacao.json; não é um programa Node independente. O gerador do roteiro foi utilizado em tmp/pdfs e resolve caminhos conforme essa localização original.
- `MANIFESTO_SHA256.json`: inventário e hashes de integridade.

## Dados conferidos

45 casos completos, 5 cargas, 3 padrões, 3 repetições e 60 segundos de acessos. Teto de 50.000 acessos/s. 5.960 amostras, 121.940.224 referências e 270 simulações. Hashes das sequências conferidos, sem OOM nos casos. A configuração original do WSL foi restaurada.

Houve retomada após 41 casos: o caso parcial foi repetido integralmente e os três restantes executados. Essa ocorrência permanece registrada no ambiente.json e no relatório. Os dados do caso parcial não integram este pacote.

## Reproduzir uma coleta

No Windows, configurar o WSL com `python linux_memoria/configurar_wsl.py aplicar` e reiniciar o WSL. O limite é compartilhado pelas distribuições WSL 2: encerre sessões de trabalho antes de reiniciar. No Ubuntu, verificar Python 3 e gcc, e executar a partir desta pasta:

```bash
python3 linux_memoria/coletar.py --saida resultados_linux/nova_coleta --cargas-mib 256 512 768 1024 1536 --duracao 60 --repeticoes 3 --intervalo 0.5 --baseline 3 --taxa 50000
```

Após terminar, analisar offline:

```bash
python3 linux_memoria/analisar.py resultados_linux/nova_coleta
python3 linux_memoria/validar.py resultados_linux/nova_coleta
python3 linux_memoria/resumir_coleta.py resultados_linux/nova_coleta
python3 linux_memoria/graficos.py resultados_linux/nova_coleta
```

Gráficos exigem matplotlib conforme requirements.txt. Coleta e análise usam a biblioteca padrão. No Windows, restaurar com `python linux_memoria/configurar_wsl.py restaurar` e reiniciar o WSL. Os scripts documentar_coleta, atualizar_roteiro_ram e finalizar_ram usam o nome fixo desta bateria.

## Escopo do pacote

Não inclui coleta preliminar de 18 casos, ensaios antigos de Windows/VRAM, simulador didático antigo, backups de configuração, ambientes Python, caches nem medições interrompidas. Os 14 PNGs são imagens da apresentação final; não são arquivos PowerPoint editáveis. A apresentação editável permanece no visualizador do chat.
