# Table 3 → Supplementary Table S1 Migration Note

## Action
Table 3 (Matched-RMS controlled mismatch cases) has been moved from the main text to Supplementary Material as **Table S1**.

## Rationale
- Figure 4(c) now directly visualizes the four matched-RMS cases as paired dot plots with per-case ratio labels.
- The full condition details (geometry family, dose type, magnitude, RMS, e_t, ratio) are preserved in Table S1 for reference.
- In-text references previously citing "Table 3" now read "Figure 4(c) and Table S1".

## Four cases (published medians from PDF Table 3, p.8)
| # | Geometry | Condition A | RMS_A | e_t_A | Condition B | RMS_B | e_t_B | Ratio |
|---|----------|-------------|-------|-------|-------------|-------|-------|-------|
| 1 | GA | D1 coherent displacement @10mm | 7.95 | 8.930 | D3 local mismatch @50mm | 7.70 | 0.900 | 9.9 |
| 2 | GB | D4 span growth @0.025 | 4.06 | 0.058 | D3 local mismatch @10mm | 3.97 | 0.621 | 10.6 |
| 3 | GB | D4 span growth @0.05 | 5.33 | 0.184 | D5 coherent tilt @0.5° | 5.08 | 1.528 | 8.3 |
| 4 | GC | D3 local mismatch @2mm | 3.75 | 0.988 | D4 span growth @0.1 | 3.80 | 0.116 | 8.5 |

## Verification
e_t values verified against `dose_response.csv` with max deviation ≤0.002 mm. RMS values are not stored in raw CSVs; they are the published frozen-experiment medians from the PDF, recorded as such in `checks/figure4_table3_verification.md`.

## Mapping口径
- 60 directed / 36 unique undirected matched pairs remain the full set (Table S1); Figure 4(c) shows 4 representative cases.
- V1's incorrect 2347×/3151×/237×/186× labels (from extreme divergent dose points) have been removed entirely.
