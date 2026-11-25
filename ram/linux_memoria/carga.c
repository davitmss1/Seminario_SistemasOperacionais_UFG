/* Carga real de páginas anônimas. Compilar: gcc -O2 -std=c11 carga.c -o carga */
#define _GNU_SOURCE
#include <errno.h>
#include <inttypes.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t parar = 0;
static void interrupcao(int sig) { (void)sig; parar=1; }
static double agora(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+t.tv_nsec/1e9; }
static uint64_t proximo(uint64_t *state) { *state=*state*UINT64_C(6364136223846793005)+UINT64_C(1442695040888963407); return *state; }
static uint64_t mistura(uint64_t *state) {
    uint64_t z=(*state+=UINT64_C(0x9e3779b97f4a7c15));
    z=(z^(z>>30))*UINT64_C(0xbf58476d1ce4e5b9);
    z=(z^(z>>27))*UINT64_C(0x94d049bb133111eb);
    return z^(z>>31);
}
int main(int argc, char **argv) {
    if(argc!=6) { fprintf(stderr,"Uso: carga MiB padrao segundos semente acessos_por_s\n"); return 2; }
    long mib=strtol(argv[1],NULL,10), pagina=sysconf(_SC_PAGESIZE);
    double duracao=strtod(argv[3],NULL), taxa=strtod(argv[5],NULL);
    const char *padrao=argv[2];
    if(mib<1 || mib>2048 || duracao<=0 || taxa<=0 || (strcmp(padrao,"sequencial") && strcmp(padrao,"localidade") && strcmp(padrao,"pseudoaleatorio"))) return 2;
    signal(SIGTERM,interrupcao); signal(SIGINT,interrupcao); setvbuf(stdout,NULL,_IOLBF,0);
    size_t bytes=(size_t)mib*1024*1024, paginas=bytes/(size_t)pagina;
    uint8_t *mem=mmap(NULL,bytes,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if(mem==MAP_FAILED) { perror("mmap"); return 3; }
    int advice=madvise(mem,bytes,MADV_NOHUGEPAGE);
    printf("{\"evento\":\"inicializacao\",\"pid\":%d,\"pagina_bytes\":%ld,\"paginas\":%zu,\"nohugepage_ok\":%s,\"monotonic_s\":%.9f}\n",getpid(),pagina,paginas,advice==0?"true":"false",agora());
    double inicio_init=agora();
    uint64_t init_state=12345;
    /* Escrever todos os bytes com dados pseudoaleatórios evita páginas zero e
       conteúdo trivialmente compressível. Todas as páginas são materializadas. */
    for(size_t i=0;i<bytes/8;i++) { ((uint64_t*)mem)[i]=mistura(&init_state); if(!(i%65536)&&parar) {munmap(mem,bytes); return 130;} }
    struct rusage antes, depois;
    getrusage(RUSAGE_SELF,&antes);
    printf("{\"evento\":\"acessos\",\"inicializacao_s\":%.9f,\"minflt_inicio\":%ld,\"majflt_inicio\":%ld,\"monotonic_s\":%.9f}\n",agora()-inicio_init,antes.ru_minflt,antes.ru_majflt,agora());
    uint64_t state=strtoull(argv[4],NULL,10), hash=UINT64_C(14695981039346656037), count=0, checksum=0;
    size_t hot=paginas/20; if(!hot)hot=1;
    double inicio=agora();
    while(!parar && agora()-inicio<duracao) {
        for(int batch=0;batch<256;batch++) {
            size_t p;
            if(!strcmp(padrao,"sequencial")) p=count%paginas;
            else { uint64_t r=proximo(&state); if(!strcmp(padrao,"localidade") && r%10<9) p=(r>>16)%hot; else p=(r>>16)%paginas; }
            volatile uint8_t *addr=mem+p*(size_t)pagina;
            uint8_t value=*addr; *addr=(uint8_t)(value+1); checksum+=value;
            hash=(hash^(uint64_t)p)*UINT64_C(1099511628211); count++;
            if(parar)break;
        }
        /* Teto igual de acessos oferecidos para todas as cargas. Se houver
           bloqueio por swap, a taxa efetiva pode ser inferior. */
        double esperar=inicio+(double)count/taxa-agora();
        if(esperar>0) { struct timespec ts={(time_t)esperar,(long)((esperar-(time_t)esperar)*1e9)}; nanosleep(&ts,NULL); }
    }
    double elapsed=agora()-inicio;
    getrusage(RUSAGE_SELF,&depois);
    printf("{\"evento\":\"fim\",\"interrompido\":%s,\"acessos\":%"PRIu64",\"duracao_real_s\":%.9f,\"hash_paginas\":\"%016"PRIx64"\",\"checksum\":%"PRIu64",\"minor_faults_acessos\":%ld,\"major_faults_acessos\":%ld,\"maxrss_kib\":%ld,\"monotonic_s\":%.9f}\n",parar?"true":"false",count,elapsed,hash,checksum,depois.ru_minflt-antes.ru_minflt,depois.ru_majflt-antes.ru_majflt,depois.ru_maxrss,agora());
    munmap(mem,bytes);
    return parar?130:0;
}
