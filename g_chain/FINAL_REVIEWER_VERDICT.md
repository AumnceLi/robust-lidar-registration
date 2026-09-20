# FINAL REVIEWER #2 VERDICT — G-chain (mechanism → robust falsification → mitigation → deployable → cross-trajectory)

Date: 2026-09-10. All numbers below are read from the frozen result CSVs under each stage; no method was
re-tuned in this round, the B2-full predictor stayed frozen, and Dataset III was opened exactly once after a
SHA256 freeze manifest. Method development **stops** after this document.

## 1. Gate chain at a glance

| stage | question | result | key evidence (median GT-start e_t, mm) |
|---|---|---|---|
| G0 | is the biased optimum just a vanilla-LS artifact? | **G0_PASS_ATTENUATED** | LS→Huber→Trim: VI 161→149→145; IV 160→133→125; II 66→51→47; V 174→169→170; III 75→56→55; matched self-null ≈ 1e-13 mm (ratio 1e13–1e14); 100% in-support frames still >10 mm; every block >10 mm |
| G1 | is the frozen mismatch model physically actionable (oracle)? | **G1_PASS** | M0→M4 patch→M5 full: VI 161→117→**77**; IV 160→126→**83**; II 66→**42**(patch best)→69(full neutral, p=0.129); V 174→135→**118**; III 75→**41**(patch, p=0.0005, 99.5% frames)→51 |
| G2 | can it run from an *estimated* view, not GT? | **G2_PASS** | est warm pipeline retains 0.98–0.997 of oracle gain (Δ 0.3–1.4 mm); direction cosine 1.000; perturbation to 100 mm/2° moves e_t <0.5 mm (flat, no collapse) |
| E | does global/patch/full transfer? | **POST-HOC: patch yes, view-conditioning trajectory-dependent** | IV 0.42<0.63<0.84; II 0.72<**0.89 patch**>0.79 full; V(out) 0.03/0.51/0.90 |
| G3 | does it hold on a trajectory sealed until the end? | **CONFIRMED** (single-look III) | C1 robust-attenuates PASS; C2 patch mitigation PASS; C3 estimated-view PASS (0.997 retained) |
| G | is the mechanism specific to the EPOS geometry? | **GENERALITY_PASS (qualified)** | 3 non-EPOS synthetic geometries; coherent assembly displacement D1 monotone 0.9→81 mm, 3–28× equal-RMS noise, robust does NOT remove (39→43→51 mm); gross-outlier D2 is the regime robust DOES handle (300→12 mm) |

## 2. The six questions that set the paper's tier

**(1) How wide can Contribution 1 be written?** Write it as: *"systematically establishes and quantifies the
chain structured scan–model mismatch → objective non-stationarity at the ground-truth pose → GT-started biased
local optimum, shows it survives standard robust registration, and reproduces it across distinct target
geometries."* It is now supported on one development trajectory, three post-development held-out trajectories,
one prospectively sealed trajectory (five real trajectories, matched self-null each), **and three controlled
non-EPOS synthetic geometries (section G)**. The controlled study adds a sharp scope statement: the bias is
driven by **coherent, spatially-extensive** mismatch (assembly displacement/tilt: monotone dose–response,
3–28× equal-RMS noise, robust cannot remove it), whereas **independent/localized/gross** discrepancies (local
patch, wholly-unmodeled part) are exactly the regime standard robust ICP handles. It is still **not** writable
as "any mismatch biases ICP" (D3/D4/partial-D2 show the absorption boundary) nor as "ICP can leave GT" (known).
Width: broad across trajectories, formulations, and geometry-class *mechanism*; bounded to the coherent
structured-mismatch regime, with synthetic (not new-hardware) generality beyond EPOS.

**(2) Is robust registration a genuine falsification pass?** Yes — and it is the logically correct kind of pass.
A pre-registered primary (Huber, δ=1.345, MAD scale) and a fixed secondary (trim 0.80) both *attenuate* (paired
p≈0.0005, 72–100% of frames reduced) but never *eliminate* the bias: residual physical displacement stays
51–169 mm, ~10¹³× the matched self-null, in 100% of in-support frames and every temporal block. Because the
falsification was attempted honestly (robustness was given its best standard chance and the self-null proves the
solver is exact), "not a least-squares artifact" is now a defensible claim rather than an assertion. ATTENUATED
(rather than STRONG) is the truthful label and should be kept.

**(3) Is B2 information actionable?** Yes, and this is the paper's biggest upgrade from "diagnostic" to
"engineering". Primary outcomes are now **physical pose errors**, not cosines. The frozen historical mismatch
field reduces median translation error by 19–84 mm with block-bootstrap CIs excluding zero and sign-flip
p≤0.0015, without trading away rotation (full level improves eR on VI/IV; patch is rotation-neutral). The
objective–pose decoupling is demonstrated directly: 100% of raw frames lower the geometric objective yet stop
>25 mm from GT, while 69–80% of corrected frames are physically closer despite lowering the *raw* objective less
— the paper's central engineering thesis ("lower geometric objective ⇏ lower physical pose error") is now
backed by a scatter, not an argument. Honest qualification: the *full view-conditioned* level is the best level
on VI/IV/V but neutral on II and only median-positive on III; the **patch** level is positive on every single
trajectory. Actionability is established; universal view-specificity is not claimed.

**(4) Is the GT-view oracle problem substantively removed?** Largely yes. The one-pass pipeline
P,M→T0=Reg_raw→z(T0)→μ_j→M_corr→T̂ retains 98–99.7% of oracle mitigation; the pure view gap (same start, only z
switched) is 0.01–0.05 mm; correction-direction cosine oracle-vs-estimated is 1.000; and a frozen perturbation
grid to 100 mm + 2° (far beyond the real 0.27–2.28° / 20–61 mm T0 view gap) is essentially flat. Remaining
boundary (must be stated, not hidden): it assumes a baseline registration inside the local basin and an
in-domain frozen mismatch library; it is not global acquisition and not "fully autonomous". That is a fair,
publishable limitation, not a fatal one.

**(5) How far do spatial-patch structure and exact view conditioning each transfer?** The post-hoc hierarchy
gives a clean, internally consistent answer: **spatial patch structure transfers robustly** (positive on IV, II,
V and physically best on II/III), whereas **the marginal value of exact view conditioning is trajectory
dependent** (helps IV/V, redundant-to-harmful on II — which also explains the frozen Dataset-II shuffle
anomaly). Global-only is inadequate (collapses to 0.03 out-of-support on V). This is labelled post-development
explanatory analysis, never prospective confirmation.

**(6) Does the untouched confirmation hold?** Yes: **CONFIRMED**. III was chosen from pose-only metadata
(371 support frames, 6/6 orientation blocks, 4 deciles), byte-sealed until G0–G2/E were hash-frozen, downloaded
once with byte-size + per-entry CRC + pose-fingerprint verification, and the frozen support rule reproduced the
predicted 371 count exactly. The pre-registered C1/C2/C3 all pass on the first and only run, with no retuning,
frame removal, or second look. Dataset I stays sealed. This is a real prospective single-look — rare in this
literature — and it is what converts a collection of held-out results into a confirmatory claim.

## 3. Strict Reviewer #2 scores

| axis | score | justification |
|---|---:|---|
| novelty | **8/10** | ICP local minima and robust ICP are known; novel is the *end-to-end, quantified* chain from structured spacecraft mismatch → GT non-stationarity → biased optimum, its reproduction across distinct geometries with an explicit boundary against the gross-outlier regime robust ICP does handle, a physically-acting frozen mismatch-field correction, an estimated-view deployable form, and a genuinely prospective single-look. Not a new estimator; a new, rigorous mechanism-to-mitigation result. |
| technical depth | **8.5/10** | Unified hand-built weighted ICP (p2p/p2l × LS/Huber/trim), GT-started non-stationarity with finite-difference gradient, matched model-self null, block bootstrap + block sign-flip, oracle/estimated/warm arms, perturbation grid, frozen adaptive-Gaussian predictor. LS special cases reproduce the frozen baseline to ~1e-16; robust self-null is ~1e-13 mm. |
| experimental rigor | **9/10** | Dev/held-out/prospective separation; freeze manifest with SHA256; CRC + fingerprint checks; pre-registered C1/C2/C3; single-look discipline; negative results retained (II full neutral, V global collapse, out-of-support full degradation); no loss-shopping (one primary robust + one fixed secondary). Deductions: one sensor/target class; block bootstrap assumes local stationarity. |
| engineering relevance | **8.5/10** | Addresses a real on-orbit failure mode; correction needs no GT at run time; one extra registration pass; smooth to realistic init error; reports runtime/success/objective. Directly usable by a GNC/relative-navigation reader. |
| generalization | **7.5/10** | Strong across five real trajectories, three registration formulations, AND three controlled non-EPOS geometries with a matched-RMS noise control and an explicit regime boundary; exact view conditioning remains trajectory-dependent. Remaining limit: cross-geometry evidence is synthetic (known-GT sim, one sensor-noise model), still a single real LiDAR/target — hardware breadth, not mechanism breadth, is now the ceiling. |
| **overall** | **8/10** | A complete, honest, unusually disciplined mechanism→falsification→mitigation→deployment→cross-trajectory-confirmation paper with controlled geometry generality; the remaining ceiling is real-hardware breadth, not rigor. |

## 4. Journal positioning (one decision)

- **READY_ACTA (Acta Astronautica) — safe primary, high acceptance probability.** Spacecraft relative-
  navigation failure mechanism + physical mitigation + deployable form + prospective single-look + controlled
  geometry generality are exactly Acta's engineering-science sweet spot; the honest trajectory-dependence and
  regime-boundary read as maturity.
- **READY_AST (Aerospace Science and Technology) — now a genuine co-primary.** The section G controlled
  cross-geometry study (three non-EPOS geometries, dose–response, matched-RMS noise control, robust-regime
  boundary) removes the single biggest "one target geometry" objection. Lead with AST if the venue's methods-
  breadth emphasis is preferred; the evidence is already in hand.
- **IEEE TAES — submittable, realistic major-revision risk.** Rigor and the prospective confirmation meet the
  bar, but TAES weights multi-target/multi-sensor *hardware* breadth most; the cross-geometry evidence is
  synthetic and the real data still come from one LiDAR. Lead there only if a second real sensor/target can be
  added; otherwise expect a revision asking for it.
- NOT_READY is not warranted: no gate failed, the confirmatory trajectory passed prospectively, the mechanism
  generalizes beyond EPOS in controlled geometry, and every claim has a pre-specified evidentiary home.

**Bottom line: READY_ACTA / READY_AST — submit now to either (Acta the safer choice, AST the slightly more
ambitious one now enabled by section G); TAES needs additional real-hardware breadth. No further method work is
required; do not reopen tuning.**

## 5. Section H claim audit (wording that must appear / must not)

Forbidden → required replacement:
- ✗ "first discovery that ICP can move away from GT" → ✓ "systematically establishes and quantifies the chain
  from structured spacecraft scan–model mismatch to objective non-stationarity and biased local optima."
- ✗ "B1 and B2 provide complementary information" (no frozen fusion was done) → ✓ "their relative performance is
  trajectory dependent."
- ✗ "external validation / independent external validation / prospective" for IV/II/V → ✓ "held-out / unseen /
  cross-trajectory evaluation / cross-trajectory transfer". Only **III** may be called a prospective single-look.
- ✗ "view-conditioned mismatch mapping transfers universally" → ✓ "spatial patch structure transfers more
  consistently than exact view conditioning; mapping specificity is trajectory dependent" (II shuffle + II/III
  hierarchy enforce this).
- Permitted because G1 passed: "historically learned structured mismatch can be used to mitigate physical pose
  bias." Permitted because G2 passed: "the mitigation can operate using viewing geometry obtained from an
  initial pose estimate rather than ground truth." Add: it assumes an in-basin baseline and an in-domain frozen
  library; do not write "fully autonomous".
- Robust-registration wording must say **attenuates, does not eliminate** (G0_PASS_ATTENUATED), never "robust
  ICP fails" and never "robust ICP solves it".

## 6. STOP RULE

No B2-v3/B3, no neural correction, no learned/B1+B2 fusion, no new shrinkage/damping, no cosine-driven
hyperparameter search, no robust-loss shopping, no opening of Dataset I, no re-look at III. **STOP METHOD
DEVELOPMENT — enter manuscript writing.**
