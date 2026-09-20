# G1 protocol — B2-informed mismatch mitigation (ORACLE view)

## Scientific question
Does the **frozen historical mismatch model** have *actionable* value — can it move the final registration
closer to physical GT, not merely predict bias direction? No correction network / fusion / new model is
allowed; only the frozen μ_j(z) is used to build a corrected nominal geometry.

## Frozen correction (math + implementation)
For every nominal model point i with frozen patch label j(i)∈0..23:
`m_i^corr = m_i + μ_{j(i)}(z)` (mathematically equivalent to correcting residuals `r_i^corr = r_i − μ_{j(i)}`).
Three spatial levels are taken from the same frozen library and were verified to reproduce the frozen VI
global/patch/full direction cosines (0.385/0.824/0.938 ≈ 0.391/0.824/0.940):
- **M3 global**: one pooled 3-vector (no patch, no view);
- **M4 patch**: per-patch vector pooled over all VI scans (spatial structure, no exact view conditioning);
- **M5 full**: per-patch k=16 view-conditioned vector μ_j(z).

## View mode
ORACLE only: z = z(T_GT). It is the mechanistic upper bound ("if viewing geometry were known, does
historical mismatch correction re-center the objective on physical GT?"). Estimated view is G2 and is
deliberately not mixed in. μ is never relearned on IV/II/V; external trajectories keep the frozen VI definition.

## Methods (all GT-started, identical basin/correspondence/stopping)
M0 raw p2p LS · M1 raw p2l LS · M2 frozen Huber robust on raw model · M3 global-corr p2p · M4 patch-corr p2p ·
M5 full-corr p2p (oracle). Every method's final pose is additionally scored against the **common raw nominal
objective** so objective change and physical-pose change can be compared on one yardstick.

## Outcomes
Primary = physical **e_t (mm)** and **e_R (deg)** vs GT (NOT cosine). Secondary = corrected GT gradient
‖∇J_corr(T_GT)‖, corrected GT-started displacement, objective/success/runtime. The dedicated
objective-vs-pose scatter tests the paper's engineering thesis: *lower geometric objective does not imply
lower physical pose error*.

## Decision rule (block-level, not single-frame wins)
G1_PASS requires direction-consistent physical improvement over multiple blocks/held-out trajectories;
translation gain without systematic rotation degradation; not driven by a few frames; block sign-flip/CI
support; and stable mitigation for at least patch or full. M5 need not beat every robust baseline; if M4≈M5
that is reported as-is. If e_corr ≥ e_raw or rotation systematically worsens → G1_FAIL_MITIGATION, stop with
no new model.
