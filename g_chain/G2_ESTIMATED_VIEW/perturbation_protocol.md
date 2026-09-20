# G2 perturbation_protocol.md — frozen sensitivity grid (D3)

Purpose: determine whether view-conditioned correction degrades **gradually** or fails **catastrophically** as
the initial pose/view estimate departs from GT. The grid is fixed before outcomes; it is not adjusted to results.

## Perturbation (applied to the GT pose that supplies the view z)
- Translation along each body axis: **10, 25, 50, 100 mm**
- Rotation about each body axis: **0.25°, 0.5°, 1°, 2°**
- Combined (translation + rotation, same axis): **(25 mm, 0.5°), (50 mm, 1°), (100 mm, 2°)**
- ε=0 is the oracle reference. These brackets span and exceed the observed T0 view gap (sub-degree / cm-scale).

## Procedure per frame
For each (type, magnitude, axis): form perturbed pose Rε=RδR_GT, tε=Rδt_GT+δt → zε → μ_j(zε) → corrected
model → frozen p2p LS registration. Record e_t(ε), e_R(ε), and the displacement-direction cosine
cos(Δt̂(zε), Δt*_oracle). Aggregate the median over the three axes and over a frozen ~150-frame in-support
subsample per trajectory (stride fixed by cap, not hand-picked); V uses an all-frame stride (out-of-support).

## Read-out
`perturbation_results.csv`: median e_t/e_R/direction-cosine per trajectory × type × magnitude, plus the oracle
line. **Gradual** = smooth, bounded rise in e_t with |ε| and direction cosine staying high; **catastrophic** =
an abrupt jump / cosine collapse within the grid. No retuning follows either outcome.
