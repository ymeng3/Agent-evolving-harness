import sys; sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag"); from xs_score import S, T
out=["=== NEW PASSES (48 games): frozen predictions ==="]
for tag,key,lab,loo,pred in (("XS_MECH07_C","fb","MECH07 fallback",-16.4,"S<0 (firm)"),("XS_naiver5_C","retry_chg","naive r5 retry",13.5,"S>0 (firm)"),("XS_ctrl21_C","retry_chg","ctrl21 retry",8.2,"S>0 (firm)"),("XS_MECH07_C","retry_chg","MECH07 retry (no LOO)",0,"-"),("XS_r3_C","retry_chg","r3 retry (no LOO)",0,"-")):
    n,s,v,k=S(tag,key); nb,sb,vb,kb=S(tag,key,"B"); ok=("PASS" if (("S<0" in pred and s<-.05) or ("S>0" in pred and s>.05)) else "FAIL" if pred!="-" else "-"); okb=("PASS" if (("S<0" in pred and sb<-.05) or ("S>0" in pred and sb>.05)) else "FAIL" if pred!="-" else "-"); out.append(f"  {lab:22s} n={n:4d} A: S={s:+.3f} {v:9s} {ok:4s} | B: S={sb:+.3f} {vb:9s} {okb:4s} | LOO {loo:+.1f} pred {pred} | A {k}")
for on,off,lab,loo,pred in (("XS_r3_C","XS_r3_noTEMP","r3 TEMPERATURE",-4.2,"T<=0 expected"),("XS_ctrl21_C","XS_ctrl21_noretry","ctrl21 retry (T view)",8.2,"T>0"),("XS_MECH07_C","XS_MECH07_nofb","MECH07 fallback (T view)",-16.4,"T<0")):
    t,v,a,b=T(on,off); out.append(f"  {lab:22s} T={t:+.3f} -> {v:9s} | LOO {loo:+.1f} | {pred} | ON seen/hold/core {a[0]:.2f}/{a[1]:.2f}/{a[2]:.2f} OFF {b[0]:.2f}/{b[1]:.2f}/{b[2]:.2f}")
try:
    import json; R="/net/scratch/ymeng3/bos_alfworld/results"
    t,v,a,b=T("XS_F0","XS_F0"); out.append("  N04 history: needs a step-logged N04 C pass (not in this batch) -> T not computable; F0 logged pass kept for later.")
except Exception as e: out.append(f"  N04: {e}")
txt="\n".join(out); print(txt); open("/net/scratch/ymeng3/bos_screens/hag/xs_new_result.txt","w").write(txt+"\n")
