import time,statistics,csv,random
from .factory import get_bitpacker

def time_function(fn,repeats=20):
    for _ in range(3):
        try: fn()
        except: pass
    t=[]
    for _ in range(repeats):
        a=time.perf_counter(); fn(); b=time.perf_counter(); t.append(b-a)
    return {"mean":statistics.mean(t),"median":statistics.median(t),"stdev":statistics.stdev(t) if len(t)>1 else 0}

def benchmark_dataset(arr,kind="noncrossing",repeats=20,choose_overflow=True):
    p=get_bitpacker(kind,choose_overflow)
    def c(): p.compress(arr)
    cstats=time_function(c,repeats)
    p.compress(arr)
    comp_bits=p.size_bits(); uncomp=len(arr)*32
    def d(): p.decompress()
    dstats=time_function(d,repeats)
    pos=[random.randrange(0,len(arr)) for _ in range(min(100,max(1,len(arr))))]
    def g():
        for x in pos: p.get(x)
    gstats=time_function(g,repeats)
    return {"kind":kind,"n":len(arr),
            "compressed_bits":comp_bits,"uncompressed_bits":uncomp,
            "compression_ratio":comp_bits/uncomp if uncomp else 0,
            "compress":cstats,"decompress":dstats,"get":gstats}

def save_results_csv(results,fname="output_benchmark.csv"):
    fields=["kind","n","compressed_bits","uncompressed_bits","compression_ratio",
            "compress_mean","decompress_mean","get_mean"]
    with open(fname,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in results:
            w.writerow({"kind":r["kind"],"n":r["n"],
                        "compressed_bits":r["compressed_bits"],
                        "uncompressed_bits":r["uncompressed_bits"],
                        "compression_ratio":r["compression_ratio"],
                        "compress_mean":r["compress"]["mean"],
                        "decompress_mean":r["decompress"]["mean"],
                        "get_mean":r["get"]["mean"]})
