# GATE 3: BITEMPORAL ENFORCEMENT STANDARD
Date: 2026-08-29

## Policy
1. No `DELETE` allowed on bitemporal tables.
2. No manual `UPDATE` of historical data.
3. Every bitemporal table gets the `civix_bitemporal_trigger`.

## Trigger Logic
When `UPDATE table SET col = new_val WHERE id = X AND tx_end = 'infinity'`:
1. Intercept UPDATE.
2. Set `NEW.tx_end = now()` on current row (closing it).
3. Insert cloned row with `col = new_val`, `tx_start = now()`, `tx_end = 'infinity'`.
4. Return NULL to cancel original UPDATE.\n