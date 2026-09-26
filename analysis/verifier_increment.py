"""Verifier increment test: paired ON (C) vs OFF (C\\fallback) step-logged passes; goal-atom trajectories; P1-P3."""
import json, re, sys, os, statistics as st
sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag"); from probeV_trace import atoms, witness
R="/net/scratch/ymeng3/bos_alfworld/results"; ORDER=json.load(open("/net/scratch/ymeng3/bos_screens/hag/game_order_train96_seed1.json"))["games_actual"]
def atom_traj(t, A):
    ev=[]
    for x in t:
        m=re.search(r"<action>(.*?)</action>",x["action"]); a=m.group(1) if m else x["action"]
        w,k=witness(x.get("obs",""),a,A)
        if w: ev.append((x["step"],k,w))
    return ev
def analyse(on_tag, off_tag, label):
    on=json.load(open(f"{R}/{on_tag}_seed1.json")); off=json.load(open(f"{R}/{off_tag}_seed1.json"))
    g_on=on.get("games_actual") or ORDER; g_off=off.get("games_actual") or ORDER; assert g_on==g_off, "slot permutation differs"
    N=len(g_on); disc=0; atomdiff=0; disc_and_atom=0; timing_ok=0; leads=[]; dir_ok=0; dir_n=0; net=0
    for i in range(N):
        A=atoms(g_on[i])[1]; eon=atom_traj(on["traj"][i],A); eoff=atom_traj(off["traj"][i],A)
        won_on=1 if on["won"][i] else 0; won_off=1 if off["won"][i] else 0; d=(won_on!=won_off)
        # first atom divergence: compare sequences of (atom,kind); earliest index where they differ or one side has an extra event
        k=0
        while k<min(len(eon),len(eoff)) and eon[k][1:]==eoff[k][1:]: k+=1
        diverged = k<max(len(eon),len(eoff))
        if diverged:
            atomdiff+=1
            # which side leads: the side with the earlier next positive event (or fewer destructions)
            def score(ev,k): 
                nxt=[e for e in ev[k:]]; return (sum(1 for e in nxt if e[2]>0)-sum(1 for e in nxt if e[2]<0), -(nxt[0][0] if nxt else 999))
            s_on,s_off=score(eon,k),score(eoff,k); lead = "ON" if s_on>s_off else "OFF" if s_off>s_on else None
            if d:
                disc_and_atom+=1; L=min(len(on["traj"][i]),len(off["traj"][i])); t_div=min([e[0] for e in eon[k:]]+[e[0] for e in eoff[k:]]+[L]); leads.append(L-t_div)
                if t_div<L: timing_ok+=1
                if lead: dir_n+=1; winner="ON" if won_on else "OFF"; dir_ok+=(lead==winner); net+=(1 if lead=="ON" else -1)
        disc+=d
    base=disc/N; enr=(disc_and_atom/atomdiff) if atomdiff else 0
    out=[f"{label}: N={N} | outcome discordant {disc} ({100*base:.1f}%) | atom-trajectory divergent {atomdiff} | discordant&divergent {disc_and_atom}",
         f"  P1 enrichment: P(discordant|atom-divergent)={100*enr:.1f}% vs base {100*base:.1f}% -> ratio {enr/base if base else 0:.2f} ({'PASS' if base and enr>=2*base else 'FAIL'})",
         f"  P2 timing: atom divergence before episode end in {timing_ok}/{disc} discordant pairs ({100*timing_ok/max(disc,1):.0f}%; rule>=70%: {'PASS' if disc and timing_ok/disc>=.7 else 'FAIL'}); median lead {st.median(leads) if leads else 'n/a'} steps",
         f"  P3 direction: lead side == winner in {dir_ok}/{dir_n} ({100*dir_ok/max(dir_n,1):.0f}%; rule>=75%: {'PASS' if dir_n and dir_ok/dir_n>=.75 else 'FAIL'}); pooled lead direction net {net:+d} (ON=fallback kept)"]
    return "\n".join(out)
res=[analyse("PV_r6_C","PVA_r6_nofb","r6 fallback (gamma -6.8)"), analyse("PV_L2c4_C","PVA_L2c4_nofb","L2c4 fallback (gamma +16.7)")]
txt="\n".join(res); print(txt); open("/net/scratch/ymeng3/bos_screens/hag/verifier_increment_result.txt","w").write(txt+"\n")
