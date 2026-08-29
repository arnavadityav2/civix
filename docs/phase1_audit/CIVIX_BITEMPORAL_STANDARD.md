# CIVIX BITEMPORAL STANDARD

## 1. Temporal Axis Definitions
- **Valid Time (`valid_from`, `valid_to`)**: The real-world interval during which a fact is claimed to be true. Controlled by investigators/data.
- **Transaction Time (`tx_start`, `tx_end`)**: The database system time when the record was known to CIVIX. Controlled by `now()`.

## 2. Standardized Table Columns
Required on: `hypothesis_support`, `case_access`, `case_entity_role`, `person_device_use`, `financial_account_role`.
```sql
valid_from TIMESTAMPTZ NULL,
valid_to TIMESTAMPTZ NULL,
tx_start TIMESTAMPTZ NOT NULL DEFAULT now(),
tx_end TIMESTAMPTZ NOT NULL DEFAULT 'infinity'
```

## 3. Second-Order Finding: Historical Correction [HIGH]
If an investigator corrects a typo in an active `hypothesis_support` row, an UPDATE destroys the transaction history.
**Resolution**: Append-only triggers MUST be implemented on all bitemporal tables. Any UPDATE is intercepted, the old row's `tx_end` is set to `now()`, and a new row is inserted.

**Verdict**: PASS with trigger requirement.\n