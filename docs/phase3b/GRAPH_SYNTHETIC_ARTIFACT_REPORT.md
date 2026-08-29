# CIVIX Phase 3B — Graph Synthetic Artifact Report

## Degree Distribution by Scenario Class

| scenario_class    |   n_persons |   mean_out_degree |   std_out_degree |   min_out_degree |   max_out_degree |   mean_unique_contacts |
|:------------------|------------:|------------------:|-----------------:|-----------------:|-----------------:|-----------------------:|
| confirmed_pattern |       24920 |           433.167 |          282.9   |               79 |             2250 |                257.388 |
| false_positive    |       12612 |           480.038 |          301.978 |               76 |             2199 |                278.79  |
| normal            |      175161 |           434.413 |          393.341 |               59 |             2300 |                250.95  |
| suspicious        |       37307 |           423.816 |          265.811 |               85 |             2170 |                254.211 |

## Artifact Assessment

✅ No near-zero within-class variance found in degree features.
Graph features do not show the same hardcoded-constant pattern as Phase 3A behavioral features.
