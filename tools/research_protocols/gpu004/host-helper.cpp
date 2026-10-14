
#include <cstdint>
#include <cstring>
#include <cmath>
#include <cfenv>
#include <dlfcn.h>
#if defined(__x86_64__)
#include <xmmintrin.h>
#endif
static void fp_mode() {
    std::fesetround(FE_TONEAREST);
#if defined(__x86_64__)
    _mm_setcsr(_mm_getcsr() & ~(unsigned((1u<<15)|(1u<<6))));
#endif
}
static float mul(float a,float b){volatile float r=a*b;return r;}
static float add(float a,float b){volatile float r=a+b;return r;}
extern "C" void make_data(float *a,int n,uint32_t seed,int transpose) {
    fp_mode();uint32_t x=seed?seed:1;
    const uint32_t special[]={0,0x80000000,1,0x80000001,0x007fffff,0x00800000,
        0x80800000,0x3f800001,0xbf800001,0x3f7fffff,0x33800000,0xb3800000};
    for(int i=0;i<n;++i){x^=x<<13;x^=x>>17;x^=x<<5;
        uint32_t bits=(x&0x807fffffu) | (uint32_t(120+(x%8))<<23);
        if(i%13==0)bits=special[(i/13+seed)%12];
        if(transpose && i%37==0)bits=x; // transpose copies all bit patterns.
        std::memcpy(a+i,&bits,4);
    }
}
extern "C" void reference(int task,const float*a,const float*b,float*c,int M,int N,int K){
    fp_mode();
    if(task==0){for(int i=0;i<M*N;++i)c[i]=add(mul(1.25f,a[i]),b[i]);}
    else if(task==1){for(int i=0;i<M;++i)for(int j=0;j<N;++j)std::memcpy(c+j*M+i,a+i*N+j,4);}
    else {for(int i=0;i<M;++i)for(int j=0;j<N;++j){float v=0.0f;
        for(int k=0;k<K;++k)v=add(v,mul(a[i*K+k],b[k*N+j]));c[i*N+j]=v;}}
}
extern "C" int cuda_batch(void*func,uint64_t A,uint64_t B,uint64_t C,int M,int N,int K,
                        unsigned gx,unsigned gy,unsigned bx,unsigned by,int count,void*start,void*stop,float*out) {
    using Launch=int(*)(void*,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,void*,void**,void**);
    using Record=int(*)(void*,void*);using Sync=int(*)(void*);using Elapsed=int(*)(float*,void*,void*);
    auto launch=(Launch)dlsym(RTLD_DEFAULT,"cuLaunchKernel");
    auto record=(Record)dlsym(RTLD_DEFAULT,"cuEventRecord");
    auto sync=(Sync)dlsym(RTLD_DEFAULT,"cuEventSynchronize");
    auto elapsed=(Elapsed)dlsym(RTLD_DEFAULT,"cuEventElapsedTime");
    if(!launch||!record||!sync||!elapsed)return -999;
    void*params[]={&A,&B,&C,&M,&N,&K};int rc=record(start,nullptr);if(rc)return rc;
    for(int i=0;i<count;++i){rc=launch(func,gx,gy,1,bx,by,1,0,nullptr,params,nullptr);if(rc)return rc;}
    if((rc=record(stop,nullptr)))return rc;if((rc=sync(stop)))return rc;
    return elapsed(out,start,stop);
}
extern "C" void suite_init(int t,float*a,float*b,float*c,float*d,float*e,int m,int n,int k,int seed){
 fp_mode();
 if(t==1){for(int i=0;i<m;++i){c[i]=0.0f;e[i]=0.0f;}}
 if(seed!=0)return;
 if(t==0){for(int i=0;i<m;++i)for(int j=0;j<k;++j)a[i*k+j]=float(i*j)/float(m);
 for(int i=0;i<k;++i)for(int j=0;j<n;++j)b[i*n+j]=float(i*j)/float(m);
 for(int i=0;i<m;++i)for(int j=0;j<n;++j)c[i*n+j]=float(i*j)/float(m);}
 if(t==1){for(int i=0;i<m;++i){d[i]=float(i)/float(m);for(int j=0;j<m;++j){a[i*m+j]=float(i*j)/float(m);b[i*m+j]=float(i*j)/float(m);}}}
 if(t==2||t==3){for(int i=0;i<m;++i)for(int j=0;j<n;++j){a[i*n+j]=float(i*j)/float(m);if(t==3)b[i*n+j]=float(i*j)/float(m);}
 float*out=t==2?b:c;for(int i=0;i<m;++i)for(int j=0;j<m;++j)out[i*m+j]=float(i*j)/float(m);}
 if(t==4){uint32_t x=17;for(int i=0;i<m*n;++i){x=x*1664525u+1013904223u;a[i]=float(x>>8)/16777216.0f;b[i]=0.25f;}}
 if(t==5){for(int i=0;i<m;++i)for(int j=0;j<n;++j)for(int z=0;z<k;++z){a[(i*n+j)*k+z]=float(i%12+2*(j%7)+3*(z%13));b[(i*n+j)*k+z]=0.25f;}}
}
extern "C" void suite_ref(int t,const float*a,float*b,float*c,float*d,float*e,int m,int n,int k,float al,float be){
 fp_mode();
 if(t==0){for(int i=0;i<m;++i)for(int j=0;j<n;++j){float v=mul(c[i*n+j],be);for(int z=0;z<k;++z)v=add(v,mul(mul(al,a[i*k+z]),b[z*n+j]));c[i*n+j]=v;}}
 if(t==1){for(int i=0;i<m;++i){float v=c[i],w=e[i];for(int j=0;j<m;++j){v=add(v,mul(a[i*m+j],d[j]));w=add(w,mul(b[i*m+j],d[j]));}c[i]=v;e[i]=add(mul(al,v),mul(be,w));}}
 if(t==2){for(int i=0;i<m;++i)for(int j=0;j<m;++j){float v=mul(b[i*m+j],be);for(int z=0;z<n;++z)v=add(v,mul(mul(al,a[i*n+z]),a[j*n+z]));b[i*m+j]=v;}}
 if(t==3){for(int i=0;i<m;++i)for(int j=0;j<m;++j){float v=mul(c[i*m+j],be);for(int z=0;z<n;++z){float x=mul(mul(al,a[i*n+z]),b[j*n+z]);float y=mul(mul(al,b[i*n+z]),a[j*n+z]);v=add(v,add(x,y));}c[i*m+j]=v;}}
 if(t==4){const float coef[]={.2f,.5f,-.8f,-.3f,.6f,-.9f,.4f,.7f,.10f};
 for(int i=1;i<m-1;++i)for(int j=1;j<n-1;++j){float v=mul(coef[0],a[(i-1)*n+j-1]);for(int z=1;z<9;++z)v=add(v,mul(coef[z],a[(i+z/3-1)*n+(j+z%3-1)]));b[i*n+j]=v;}}
 if(t==5){const float coef[]={2,4,5,7,-8,10,-3,6,-9,2,4,5,7,-8,10};
 const int di[]={-1,1,-1,1,-1,1,0,0,0,-1,1,-1,1,-1,1};
 const int dj[]={-1,-1,-1,-1,-1,-1,-1,0,1,-1,-1,0,0,1,1};
 const int dk[]={-1,-1,-1,-1,-1,-1,0,0,0,1,1,1,1,1,1};
 for(int i=1;i<m-1;++i)for(int j=1;j<n-1;++j)for(int z=1;z<k-1;++z){float v=mul(coef[0],a[((i+di[0])*n+j+dj[0])*k+z+dk[0]]);
 for(int q=1;q<15;++q)v=add(v,mul(coef[q],a[((i+di[q])*n+j+dj[q])*k+z+dk[q]]));b[(i*n+j)*k+z]=v;}}
}
// All data restoration precedes the event interval on each invocation.
// A 3D stencil invocation consists of all original i-slice launches, not one plane.
extern "C" int suite_time(void*fn,void**args,int gx,int gy,int bx,int by,int count,int slices,int*slice,
 int nout,const uint64_t*dst,const uint64_t*src,const uint64_t*bytes,void*start,void*stop,float*out){
 using Launch=int(*)(void*,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,void*,void**,void**);
 using Copy=int(*)(uint64_t,uint64_t,size_t);using Record=int(*)(void*,void*);using Sync=int(*)(void*);using Elapsed=int(*)(float*,void*,void*);
 auto launch=(Launch)dlsym(RTLD_DEFAULT,"cuLaunchKernel");auto copy=(Copy)dlsym(RTLD_DEFAULT,"cuMemcpyDtoD_v2");
 auto record=(Record)dlsym(RTLD_DEFAULT,"cuEventRecord");auto sync=(Sync)dlsym(RTLD_DEFAULT,"cuEventSynchronize");auto elapsed=(Elapsed)dlsym(RTLD_DEFAULT,"cuEventElapsedTime");
 if(!launch||!copy||!record||!sync||!elapsed)return -999;
 if(count<1||count>128||slices==0)return -998;
 double total=0;int rc=0;
 for(int r=0;r<count;++r){
  for(int i=0;i<nout;++i)if((rc=copy(dst[i],src[i],bytes[i])))return rc;
  if((rc=record(start,nullptr)))return rc;
  for(int s=1;s<=(slices<0?1:slices);++s){*slice=s;if((rc=launch(fn,gx,gy,1,bx,by,1,0,nullptr,args,nullptr)))return rc;}
  if((rc=record(stop,nullptr)))return rc;if((rc=sync(stop)))return rc;
  float ms=0;if((rc=elapsed(&ms,start,stop)))return rc;if(!(ms>0))return -997;total+=ms;
 }
 *out=float(total);return 0;
}
