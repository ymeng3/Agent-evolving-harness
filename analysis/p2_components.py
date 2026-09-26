# Phase-2 component list: (name, source C tag, kind, C patch, OFF patch, global point gamma)
P="/net/scratch/ymeng3/bos_alfworld"
C=[("r6 fallback","PV_r6_C","fallback",f"{P}/patches_p1b/P1B_ours_r6_strategic_fallback_with_.py",f"{P}/patches_p1b/P1B_ours_r6_strategic_fallback_with__loo_choose.py",-6.8),
("r6 retry","PV_r6_C","retry",f"{P}/patches_p1b/P1B_ours_r6_strategic_fallback_with_.py",f"{P}/patches_p1b/P1B_ours_r6_strategic_fallback_with__loo_retry_.py",0.0),
("r6 memory","PV_r6_C","history",f"{P}/patches_p1b/P1B_ours_r6_strategic_fallback_with_.py",f"{P}/patches_p1b/P1B_ours_r6_strategic_fallback_with__loo_memory.py",0.0),
("r6 HISTORY","PV_r6_C","history",f"{P}/patches_p1b/P1B_ours_r6_strategic_fallback_with_.py",f"{P}/patches_p1b/P1B_ours_r6_strategic_fallback_with__loo_HISTOR.py",3.1),
("L2c4 fallback","PV_L2c4_C","fallback",f"{P}/patches_loop2/L2_N_r1_c4.py",f"{P}/patches_loop2/L2_N_r1_c4_loo_choose.py",16.7),
("L2c4 retry","PV_L2c4_C","retry",f"{P}/patches_loop2/L2_N_r1_c4.py",f"{P}/patches_loop2/L2_N_r1_c4_loo_retry_.py",1.0),
("L2c4 HISTORY","PV_L2c4_C","history",f"{P}/patches_loop2/L2_N_r1_c4.py",f"{P}/patches_loop2/L2_N_r1_c4_loo_HISTOR.py",11.5),
("r4 retry","PV_r4_C","retry",f"{P}/patches_p1b/P1B_ours_r4_structured_reasoning_wit.py",f"{P}/patches_p1b/P1B_ours_r4_structured_reasoning_wit_loo_retry_.py",13.0),
("r4 HISTORY","PV_r4_C","history",f"{P}/patches_p1b/P1B_ours_r4_structured_reasoning_wit.py",f"{P}/patches_p1b/P1B_ours_r4_structured_reasoning_wit_loo_HISTOR.py",-0.5),
("r4 memory","PV_r4_C","history",f"{P}/patches_p1b/P1B_ours_r4_structured_reasoning_wit.py",f"{P}/patches_p1b/P1B_ours_r4_structured_reasoning_wit_loo_memory.py",0.0),
("r4 format","PV_r4_C","history",f"{P}/patches_p1b/P1B_ours_r4_structured_reasoning_wit.py",f"{P}/patches_p1b/P1B_ours_r4_structured_reasoning_wit_loo_format.py",2.1),
("ctrl21 retry","XS_ctrl21_C","retry",f"{P}/patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py",f"{P}/patches_v1/V1_loo_retry_.py",8.2),
("ctrl21 format","XS_ctrl21_C","history",f"{P}/patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py",f"{P}/patches_v1/V1_loo_format.py",-3.7),
("ctrl21 parse","XS_ctrl21_C","parse",f"{P}/patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py",f"{P}/patches_v1/V1_loo_parse_.py",-3.0),
("ctrl21 memory","XS_ctrl21_C","history",f"{P}/patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py",f"{P}/patches_v1/V1_loo_memory.py",3.0),
("ctrl21 HISTORY","XS_ctrl21_C","history",f"{P}/patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py",f"{P}/patches_v1/V1_loo_HISTOR.py",0.8),
("MECH07 fallback","XS_MECH07_C","fallback",f"{P}/patches_formB/mech_diag_gaps/MECH07_plan_sub_goal_completion.py",f"{P}/patches_salvage/SV_HM.py",-16.4),
("MECH07 HISTORY","XS_MECH07_C","history",f"{P}/patches_formB/mech_diag_gaps/MECH07_plan_sub_goal_completion.py",f"{P}/patches_salvage/SV_CM.py",4.5),
("r3 TEMPERATURE","XS_r3_C","history",f"{P}/patches_loop/CL_O_r3_c4.py",f"{P}/patches_loop/CL_O_r3_c4_loo_TEMPER.py",-4.2),
("r3 format","XS_r3_C","history",f"{P}/patches_loop/CL_O_r3_c4.py",f"{P}/patches_loop/CL_O_r3_c4_loo_format.py",6.2),
("r3 HISTORY","XS_r3_C","history",f"{P}/patches_loop/CL_O_r3_c4.py",f"{P}/patches_loop/CL_O_r3_c4_loo_HISTOR.py",1.0),
("naive r5 retry","XS_naiver5_C","retry",f"{P}/patches_p1b/P1B_naive_r5_goal_focused_retries_wit.py",f"{P}/patches_p1b/P1B_naive_r5_goal_focused_retries_wit_loo_retry_.py",13.5),
("naive r3 retry","P2C_naiver3","retry",f"{P}/patches_p1b/P1B_naive_r3_retry_with_memory_update.py",f"{P}/patches_p1b/P1B_naive_r3_retry_with_memory_update_loo_retry_.py",11.5),
("naive r3 memory","P2C_naiver3","history",f"{P}/patches_p1b/P1B_naive_r3_retry_with_memory_update.py",f"{P}/patches_p1b/P1B_naive_r3_retry_with_memory_update_loo_memory.py",7.3),
("L1r2 retry","P2C_l1r2","retry",f"{P}/patches_loop/CL_O_r2_c4.py",f"{P}/patches_loop/CL_O_r2_c4_loo_retry_.py",11.5),
("L1r2 memory","P2C_l1r2","history",f"{P}/patches_loop/CL_O_r2_c4.py",f"{P}/patches_loop/CL_O_r2_c4_loo_memory.py",0.0),
("L1r2 HISTORY","P2C_l1r2","history",f"{P}/patches_loop/CL_O_r2_c4.py",f"{P}/patches_loop/CL_O_r2_c4_loo_HISTOR.py",13.5),
("N01 parser","P2C_N01","parse",f"{P}/patches/N01_refine_action_extraction.py","none",4.9),
("N03 retry","P2C_N03","retry",f"{P}/patches/N03_retry_with_reasoning.py","none",4.1),
("N04 history","P2C_N04","history",f"{P}/patches/N04_optimize_history_length.py","none",6.3),
("N05 retry-temp","P2C_N05","retry",f"{P}/patches/N05_adjust_retry_temperature.py","none",1.5),
("N07 temp+prompt","P2C_N07","history",f"{P}/patches/N07_adjust_temperature_and_prompt_on_retry.py","none",6.3),
("E1_T temp","P2C_E1T","history",f"{P}/patches_exp1/E1_T_temp05.py","none",-1.1),
("E1_HR retry+hist","P2C_E1HR","retry",f"{P}/patches_exp1/E1_HR_hist10_retry_basetemp.py","none",16.4)]
NEWC={"P2C_naiver3":f"{P}/patches_p1b/P1B_naive_r3_retry_with_memory_update.py","P2C_l1r2":f"{P}/patches_loop/CL_O_r2_c4.py","P2C_N01":f"{P}/patches/N01_refine_action_extraction.py","P2C_N03":f"{P}/patches/N03_retry_with_reasoning.py","P2C_N04":f"{P}/patches/N04_optimize_history_length.py","P2C_N05":f"{P}/patches/N05_adjust_retry_temperature.py","P2C_N07":f"{P}/patches/N07_adjust_temperature_and_prompt_on_retry.py","P2C_E1T":f"{P}/patches_exp1/E1_T_temp05.py","P2C_E1HR":f"{P}/patches_exp1/E1_HR_hist10_retry_basetemp.py"}
if __name__=="__main__":
    import sys
    if sys.argv[1]=="newc": print("".join(f"{t} {p} 1 48\n" for t,p in NEWC.items()))
    elif sys.argv[1]=="list": print("".join(f"{n}|{src}|{k}|{cp}|{op}|{g}\n" for n,src,k,cp,op,g in C))
