from src.factory import get_bitpacker
from src.benchmark import benchmark_dataset, save_results_csv

import random,time

def sample_datasets():
    d={}
    d["random_small"]=[random.getrandbits(12) for _ in range(1000)]
    d["small_values"]=[random.randrange(0,16) for _ in range(5000)]
    a=[random.randrange(0,32) for _ in range(4900)]
    a+=[2**p for p in range(20,30)]
    d["outliers"]=a
    d["random_32"]=[random.getrandbits(32) for _ in range(20000)]
    return d

def latency(un,co,ct,bw):
    return (un-co)/bw-ct

def run(repeats=5,save_csv=True):
    ds=sample_datasets(); res=[]
    print("Running benchmarks...")
    for name,arr in ds.items():
        print(f"\nDataset {name} n={len(arr)}")
        for k in ("noncrossing","crossing"):
            r=benchmark_dataset(arr,k,repeats)
            res.append(r)
            print(f"{k:11s}: ratio={r['compression_ratio']:.3f}, comp={r['compress']['mean']:.5f}s, decomp={r['decompress']['mean']:.5f}s, get={r['get']['mean']:.5f}s")
            for bw in (1e6,10e6,100e6):
                t=latency(r['uncompressed_bits'],r['compressed_bits'],r['compress']['mean'],bw)
                print(f"  bw={int(bw/1e6)}Mbps => latency threshold={t:.6f}s")
    if save_csv:
        save_results_csv(res,f"output_benchmark_{int(time.time())}.csv")
        print("\nCSV saved.")
    return res

if __name__=="__main__":
    run()
