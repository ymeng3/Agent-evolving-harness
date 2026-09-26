# LOCAL SAMPLING DIAGNOSTIC — FROZEN 2026-09-20 BEFORE ANY RESULT
Post-failure diagnostic only. Original A1 remains FAIL. This experiment does not replace, amend, or rerun the frozen
equivalence criterion (hag/LOCAL_BACKEND_QUALIFICATION.md). It is the LAST backend diagnostic: no seed 4, no threshold
change, no further equivalence chasing afterwards.
FINDING THAT MOTIVATES IT: the harness sends only temperature=0.4 and max_tokens. vLLM silently fills top_k=20 /
top_p=0.8 from the checkpoint's generation_config.json; the OpenAI-convention default on the API path is top_p=1, no top_k.
INTERVENTION: local F0, validation_train96, seeds 1/2/3, explicit temperature=0.4, top_p=1.0, top_k=-1; nothing else changes.
  H1: the +5.6pp shift comes mainly from the implicit sampling truncation  -> diagnostic mean returns near 0.32.
  H2: local/API remain shifted after matching sampling                    -> diagnostic mean stays near 0.38.
DECISION (fixed now, independent of outcome): the explicit protocol {T=0.4, top_p=1, top_k=-1} is FROZEN as the
"Local-v2" decoding protocol; the three diagnostic passes ARE F0^{local-v2} (tags LQD_F0 seeds 1-3) and anchor the closed
loop, Credit-only and reuse ablations. Historical API numbers are prior mechanism evidence only, never the same regime as
local headline numbers. Only a protocol error or instability revealed by the diagnostic stops the local loop.
