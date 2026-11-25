"""Formato determinístico de acessos compartilhado com carga.c."""
from collections import OrderedDict, deque

MASK=(1<<64)-1
FNV_OFFSET=14695981039346656037
FNV_PRIME=1099511628211


def acessos(padrao, paginas, quantidade, seed=336):
    if paginas<1 or quantidade<0 or padrao not in ('sequencial','localidade','pseudoaleatorio'):
        raise ValueError('Parâmetros de sequência inválidos')
    state=seed
    hot=max(1,paginas//20)
    for i in range(quantidade):
        if padrao=='sequencial':
            yield i%paginas
        else:
            state=(state*6364136223846793005+1442695040888963407)&MASK
            yield (state>>16)%(hot if padrao=='localidade' and state%10<9 else paginas)


def resumo_politicas(seq, capacidades):
    """O(1) amortizado por referência; não armazena snapshots dos quadros."""
    if not capacidades or min(capacidades)<1:
        raise ValueError('Capacidades devem ser positivas')
    states={n:dict(fila=deque(),presentes=set(),lru=OrderedDict(),fifo_faltas=0,lru_faltas=0) for n in capacidades}
    total=0
    hash_value=FNV_OFFSET
    for page in seq:
        total+=1
        hash_value=((hash_value^page)*FNV_PRIME)&MASK
        for capacity,s in states.items():
            if page not in s['presentes']:
                s['fifo_faltas']+=1
                if len(s['fila'])==capacity:
                    s['presentes'].remove(s['fila'].popleft())
                s['fila'].append(page)
                s['presentes'].add(page)
            if page in s['lru']:
                s['lru'].move_to_end(page)
            else:
                s['lru_faltas']+=1
                if len(s['lru'])==capacity:
                    s['lru'].popitem(last=False)
                s['lru'][page]=None
    return states,total,f'{hash_value:016x}'
