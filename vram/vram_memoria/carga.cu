// CUDA application-managed cache; one byte read/modified per block reference.
#include <cuda_runtime.h>
#include <chrono>
#include <thread>
#include <vector>
#include <list>
#include <iterator>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <inttypes.h>
#include <algorithm>
#include <signal.h>
using Clock=std::chrono::steady_clock;
static double now(){return std::chrono::duration<double>(Clock::now().time_since_epoch()).count();}
static volatile sig_atomic_t stop=0;
static void interrupt(int){stop=1;}
#define CHECK(x) do {cudaError_t e=(x); if(e!=cudaSuccess){fprintf(stderr,"%s: %s\n",#x,cudaGetErrorString(e));exit(3);}}while(0)
constexpr size_t B=4*1024*1024;
constexpr int CAP=256;
static uint64_t mix(uint64_t &s){uint64_t z=(s+=UINT64_C(0x9e3779b97f4a7c15));z=(z^(z>>30))*UINT64_C(0xbf58476d1ce4e5b9);z=(z^(z>>27))*UINT64_C(0x94d049bb133111eb);return z^(z>>31);}
__global__ void touch(uint8_t *p){volatile uint8_t *q=p;uint8_t v=*q;*q=(uint8_t)(v+1);}
struct Stats{uint64_t n=0,hits=0,miss=0,evict=0,h2d=0,d2h=0,hash=UINT64_C(14695981039346656037);double htime=0,dtime=0,ktime=0;};
static void emit(const char *kind,const Stats &s,int resident,double elapsed){
 printf("{\"evento\":\"%s\",\"monotonic_s\":%.9f,\"duracao_real_s\":%.9f,\"acessos\":%" PRIu64 ",\"acertos\":%" PRIu64 ",\"faltas\":%" PRIu64 ",\"substituicoes\":%" PRIu64 ",\"h2d_bytes\":%" PRIu64 ",\"d2h_bytes\":%" PRIu64 ",\"h2d_s\":%.9f,\"d2h_s\":%.9f,\"kernel_sync_s\":%.9f,\"residentes\":%d,\"hash_blocos\":\"%016" PRIx64 "\"}\n",kind,now(),elapsed,s.n,s.hits,s.miss,s.evict,s.h2d,s.d2h,s.htime,s.dtime,s.ktime,resident,s.hash);
}
int main(int argc,char **argv){
 if(argc!=8){fprintf(stderr,"Uso: carga MiB padrao segundos semente taxa FIFO|LRU intervalo\n");return 2;}
 int mib=atoi(argv[1]);const char *pat=argv[2];double duration=atof(argv[3]),rate=atof(argv[5]),interval=atof(argv[7]);uint64_t state=strtoull(argv[4],nullptr,10);bool lru=!strcmp(argv[6],"LRU");
 if(mib<4||mib>2048||mib%4||duration<=0||rate<=0||interval<=0||(!lru&&strcmp(argv[6],"FIFO"))||(strcmp(pat,"sequencial")&&strcmp(pat,"localidade")&&strcmp(pat,"pseudoaleatorio")))return 2;
 signal(SIGINT,interrupt);signal(SIGTERM,interrupt);setvbuf(stdout,nullptr,_IOLBF,0);
 Stats s; emit("inicializacao",s,0,0);
 int blocks=mib/4,used=0,hot=std::max(1,blocks/20);size_t bytes=(size_t)blocks*B;
 std::vector<uint64_t> host(bytes/8);uint8_t *ram=reinterpret_cast<uint8_t*>(host.data());uint64_t init=12345;
 for(auto &v:host){v=mix(init);if(stop)return 130;}
 std::vector<uint8_t> expected(blocks);for(int p=0;p<blocks;p++)expected[p]=ram[(size_t)p*B];
 uint8_t *gpu=nullptr;CHECK(cudaSetDevice(0));size_t avail,total;CHECK(cudaMemGetInfo(&avail,&total));if(avail<CAP*B){fprintf(stderr,"VRAM insuficiente\n");return 3;}CHECK(cudaMalloc(&gpu,CAP*B));
 std::vector<int> slot(blocks,-1);std::list<int> order;std::vector<std::list<int>::iterator> where(blocks);
 double start=now(),next=start+interval;emit("acessos",s,used,0);
 while(!stop&&now()-start<duration){
  int p;if(!strcmp(pat,"sequencial"))p=s.n%blocks;else{state=state*UINT64_C(6364136223846793005)+UINT64_C(1442695040888963407);p=(state>>16)%((!strcmp(pat,"localidade")&&state%10<9)?hot:blocks);}
  int j=slot[p];if(j>=0){s.hits++;if(lru)order.splice(order.end(),order,where[p]);}
  else{ s.miss++; if(used==CAP){int victim=order.front();order.pop_front();j=slot[victim];double t=now();CHECK(cudaMemcpy(ram+(size_t)victim*B,gpu+(size_t)j*B,B,cudaMemcpyDeviceToHost));s.dtime+=now()-t;s.d2h+=B;s.evict++;slot[victim]=-1;}else j=used++;
   double t=now();CHECK(cudaMemcpy(gpu+(size_t)j*B,ram+(size_t)p*B,B,cudaMemcpyHostToDevice));s.htime+=now()-t;s.h2d+=B;slot[p]=j;order.push_back(p);where[p]=std::prev(order.end());}
  double t=now();touch<<<1,1>>>(gpu+(size_t)j*B);CHECK(cudaGetLastError());CHECK(cudaDeviceSynchronize());s.ktime+=now()-t;expected[p]++;s.hash=(s.hash^(uint64_t)p)*UINT64_C(1099511628211);s.n++;
  // Same offered-rate ceiling as RAM; pacing by individual reference avoids long batches of transfers.
  double wait=start+(double)s.n/rate-now();if(wait>0&&s.n%32==0)std::this_thread::sleep_for(std::chrono::duration<double>(wait));
  double current=now();if(current>=next){emit("amostra",s,used,current-start);next=current+interval;}
 }
 double wait=start+(double)s.n/rate-now();if(wait>0&&!stop)std::this_thread::sleep_for(std::chrono::duration<double>(wait));
 double elapsed=now()-start;emit("fim",s,used,elapsed);
 // Outside timed phase: flush all resident dirty blocks, check modified byte of every block.
 double t=now();for(int p:order)CHECK(cudaMemcpy(ram+(size_t)p*B,gpu+(size_t)slot[p]*B,B,cudaMemcpyDeviceToHost));double flush=now()-t;
 bool ok=true;for(int p=0;p<blocks;p++)if(ram[(size_t)p*B]!=expected[p])ok=false;
 CHECK(cudaFree(gpu));printf("{\"evento\":\"validacao_dados\",\"ok\":%s,\"flush_final_bytes\":%zu,\"flush_final_s\":%.9f}\n",ok?"true":"false",(size_t)used*B,flush);
 return stop?130:ok?0:4;
}
