import json,os,statistics as st,sys
sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag"); from p2_components import C
R="/net/scratch/ymeng3/bos_alfworld"; agree=0; n=0; fam={}
print(f"{'component':18s} {'kind':9s} {'global':>7s} {'CF32_s1':>8s} {'CF32_s2':>8s} sign")
for name,src,kind,cp,op,g in C:
    s="p2_"+name.replace(" ","_"); f2=f"{R}/results/PL_{s}_OFF_rep2_seed2.json"
    if not os.path.exists(f2): continue
    M=json.load(open(f"{R}/probeL/{s}_meta.json")); order=[l.strip() for l in open(f"{R}/probeL/{s}_manifest.txt") if l.strip()]
    def cf(f,B):
        d=json.load(open(f)); ga=d.get("games_actual") or d["games"]; off={x:(1 if w else 0) for x,w in zip(ga,d["won"])}
        diffs=[M[x]["won_on_original"]-off[x] for x in order[:B] if x in off]; return 100*st.mean(diffs) if diffs else float("nan")
    a=cf(f"{R}/results/PL_{s}_OFF_rep1_seed1.json",32); b=cf(f2,32); ok=(a>0)==(b>0) if a!=0 and b!=0 else (a==b)
    agree+=ok; n+=1; fam.setdefault(kind,[0,0]); fam[kind][0]+=ok; fam[kind][1]+=1
    print(f"{name:18s} {kind:9s} {g:+7.1f} {a:+8.1f} {b:+8.1f} {'same' if ok else 'FLIP'}")
print(f"sign agreement seed1 vs seed2 at B=32: {agree}/{n} | by family: " + ", ".join(f"{k} {v[0]}/{v[1]}" for k,v in fam.items()))
