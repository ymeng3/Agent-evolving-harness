# CREDIT REGIME QUALIFICATION — v1 FROZEN 2026-09-21 11:40 CDT (funnel). Decides whether Credit V2 is worth designing. NOT a closed loop.
FUNNEL (sequential spending, frozen): P1a generation ($1-2) -> only if P1a passes: 1-seed screen of the 3-4 most coherent
compound candidates (~4-5 configs x 96 each, ~4-5 GPU-h) looking for an EXISTENCE proof of decomposition opportunity
(mixed sign, interaction, or whole-vs-component inheritance disagreement) -> only such candidates get seed 2 -> only
genuinely ambiguous, decision-relevant contrasts get seed 3. P2(ii) 'mechanism counters as prior' is REMOVED: the $0
archival test (sha 5ebc0fd040e8bffe) killed it and showed mechanism-PASS with negative outcome (fallback). P2 is now the
success-only decision-stability curve on whatever lattice P1b produces ($0 analysis).
Principle: prove that Credit has a solvable problem AND obtainable evidence before designing a more complex Credit.
P1  COMPOUND INHERITANCE OPPORTUNITY (is there a real compound problem that the proposer can expose?)
  Generation ($1-2, gpt-4o): from 6 real Loop-1 states (F0 + the naive/ours round states with their evidence blocks),
  4 candidates each = 24, under a NEW proposal instruction that permits and motivates coherent multi-unit mechanisms
  ("compound only when constituents implement one mechanism or address interacting failure modes; give the rationale
  linking the units"), never "at least 3 edits". Measures (frozen): P(|C|>=3); structural coherence = fraction of
  multi-unit candidates whose units are coupled (dependency closure non-singleton, shared state keys, or call chain),
  computed by the existing Stage-0 tooling, not by an LLM judge. Gate P1a: P(|C|>=3) >= 0.5 AND coherence >= 0.6.
  Execution (local, $0, ~1 night): the 6 most coherent |C|>=3 candidates, full LOO lattice at n = 3 seeds x 96 = 288
  paired episodes per contrast (the resolution P2 below says is needed for +/-8pp effects). Gate P1b: >= 2 of 6 show a
  decision-relevant mixed structure at delta=3pp/90%: (KEEP, DROP) present in the same candidate, or a unit whose effect
  is KEEP only with another unit present (interaction). If P1b fails: ALFWorld useful improvements are atomic here ->
  no Credit V2 on ALFWorld; change benchmark/regime.
P2  DECISION-RELEVANT IDENTIFIABILITY (can we tell keep/drop/uncertain at acceptable budget?)
  Criterion (frozen): a unit decision is keep if P(gamma > +3pp) >= 0.9, drop if P(gamma < -3pp) >= 0.9, else uncertain
  (game-bootstrap posterior). Budget question: how many paired episodes until the decision stabilises?
  Archival design analysis (2026-09-21, G_MECH07 = H+M+fallback lattice, 402 paired episodes, NOT a qualification result):
    fallback  -16.4pp -> DROP stable at n>=96 (97%)   |  H +8.5pp -> KEEP needs n~200-270 (87-97%)
    M -2.0pp / H-in-context +4.5pp -> UNCERTAIN, and stably so from n=64 (i.e. "do not act" is cheap to learn)
    C vs F0 -9.95pp -> DROP needs n~200 (87%).  => actionable contrasts of |effect| >= 8pp resolve at 200-270 episodes;
    |effect| >= 15pp at ~96; |effect| <= 4pp are correctly left as uncertain at ~64. Loop 1 spent 96 per unit, once.
  P2 test proper: on the P1b candidates, compare three evidence sources for the SAME decisions at matched budget:
    (i) success-only LOO (as V1); (ii) mechanism counters + trajectory-level consequences (hook fire rates, admissible
    rate, loop rate, steps) as a prior on |gamma| = 0 / sign; (iii) combined. Endpoint: episodes needed to reach the
    full-lattice decision (agreement >= 90%). Gate P2: some evidence source reaches the actionable decisions within
    <= 300 paired episodes per unit on median. If only (ii)/(iii) pass: Credit V2 must be mechanism-aware, not success-only.
  Sanity now in hand: mechanism counters are informative at zero cost (Loop-1 r4: parse_action fires 0.29/step in C,
  0.00 in C\parse; a unit that never fires cannot carry credit).
DECISIONS: P1 fail -> no V2 on ALFWorld. P1 pass, P2 fail -> Credit problem exists but success-only Credit is infeasible;
  design mechanism-aware Credit. Both pass -> prospective V2 loop, baseline = same compound variation + whole-candidate
  inheritance (not Loop-1 Naive); short horizon first (T=2-3) to show Credit changes hereditary decisions; T=5 only for reuse.
NOT DONE UNTIL USER GO: the P1 generation call and any execution. Nothing here revives Loop 1.

P1a OPERATOR TEXT (frozen verbatim; replaces the operator block in the Loop-1 prompt; everything else identical):
  "TRANSFORMATION: COMPOSE-COHERENT. Propose the intervention the evidence calls for. It MAY consist of several executable
   units (hooks/constants) ONLY when those units implement one coherent mechanism or address failure modes that interact;
   in that case add a line RATIONALE: stating how each unit depends on or interacts with the others. Do NOT bundle
   unrelated edits. There is no minimum or maximum number of units; a single-unit patch is correct when the evidence
   calls for one."
P1a STATES: 6 snapshots reconstructed from the Loop-1 state files: naive@r1 (F0, no history), naive@r3 (F=CL_N_r2_c4),
  naive@r5, ours@r2 (F0, 2 credit records), ours@r4 (F0, 9 records), ours@r6 (F=CL_O_r5_c4_S, 12 records). 4 proposals each
  = 24 (gpt-4o, T=1.0 as in the loop; validity gate = validate_patch + STATIC + smoke, all offline).
P1a METRICS (frozen): P(|C|>=3) over VALID proposals; structural coherence over VALID |C|>=2 proposals = fraction with at
  least one coupling between units, coupling := singleton removal of a unit is INVALID (dependency closure) OR two units
  reference the same state[...] key. Gate P1a: P(|C|>=3) >= 0.5 AND coherence >= 0.6. RATIONALE presence is recorded, not
  scored. Invalid-proposal rate reported.

## P1a' — STRUCTURED VARIATION (DEDICATED COMPOSE) TEST. FROZEN 2026-09-21 12:30 CDT BEFORE ANY NUMBER.
Why: P1a tested "natural proposer + textual encouragement", not structured variation. Credit was born inside a
Compose-heavy regime (A_ops: 9/10 Compose; A_ops08 = context + decoding + retry). This test asks whether a dedicated
Compose operator, given a mechanism pool with evidence, exposes compound inheritance problems on the SAME 6 states.
INPUTS per state: parent F (source); MECHANISM POOL = every candidate that arm validated before round t (source, validation
delta vs F_t, finalist/eliminated) plus the arm's Credit records (unit, gamma, kept/dropped) where they exist; the same
execution-evidence block as the loop. Pool sizes will be small at r1/r2 (that is the real regime, reported as-is).
OPERATOR (frozen verbatim): "TRANSFORMATION: COMPOSE. Select at least two source mechanisms from the MECHANISM POOL (or one
pool mechanism plus one mechanism you derive from a specific failure in the evidence) that have a reason to interact or
complement each other, and implement their composition as one patch. Each constituent must remain an identifiable
executable unit (a hook or constant). Do not add edits that are not part of the composition."
OUTPUT FORMAT (frozen; replaces the artifact block so the fields cannot be suppressed): DESIGN_INTENT, SOURCE_A, EVIDENCE_A,
SOURCE_B, EVIDENCE_B, [SOURCE_C, EVIDENCE_C], COMPOSITION_HYPOTHESIS, MECHANISM, NAME, ```python patch```.
METRICS (frozen): valid rate (validate_patch + STATIC + smoke); COMPOSITION RATE = fraction of valid proposals whose
SOURCE_A and SOURCE_B are distinct AND the patch realises >= 2 executable units; coupling as in P1a (dependency-closure
invalidity or shared state key); ARBITRARY-BUNDLE RATE = valid multi-unit proposals with no coupling AND a
COMPOSITION_HYPOTHESIS that does not name a shared state/flow (recorded by string check: mentions of state/memory/flag/
retry/fallback linkage; reported, secondary); |C| descriptive.
GATES: composition rate >= 0.5 among valid AND valid rate >= 0.5. PASS -> "Credit opportunity depends on the search
regime"; P1b screen (GPU) is then justified on the composed candidates. FAIL -> ALFWorld/current editable surface is the
wrong Credit host; benchmark audit next. Same 24-proposal budget ($~1), same states, same model/temperature as P1a.
