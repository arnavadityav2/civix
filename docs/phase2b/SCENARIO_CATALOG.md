# CIVIX — SCENARIO CATALOG
## All Supported Scenario Families

**Version**: 1.0 | **Date**: 2026-08-29

---

## Category 1: Identity Scenarios

| ID | Name | Description | Ground Truth | Difficulty |
|---|---|---|---|---|
| IDENT-01 | genuine_identity | Single person, consistent docs, normal activity | label=INNOCENT | LOW |
| IDENT-02 | duplicate_identity | Same person uses two different legal IDs | label=FRAUD | HIGH |
| IDENT-03 | alias_usage | Person uses AKA for legitimate reasons (actor, author) | label=INNOCENT | MEDIUM |
| IDENT-04 | alias_criminal | Person uses false name to evade investigation | label=SUSPECT | HIGH |
| IDENT-05 | spelling_variation | Transliteration variation of name (Rajesh/Rajesh Kumar/R. Kumar) | label=INNOCENT | MEDIUM |
| IDENT-06 | identity_collision | Two different people with same name/DOB in same area | label=AMBIGUOUS | VERY HIGH |
| IDENT-07 | deceased_reuse | Living person using deceased relative's identity | label=FRAUD | HIGH |
| IDENT-08 | shared_indicators | Multiple people use same address/phone (family) | label=INNOCENT | MEDIUM |

---

## Category 2: Telecom Scenarios

| ID | Name | Description | Ground Truth | Difficulty |
|---|---|---|---|---|
| TEL-01 | normal_caller | Regular person, predictable call patterns | label=INNOCENT | LOW |
| TEL-02 | high_freq_innocent | Customer support agent, calls 200+/day | label=INNOCENT | HIGH |
| TEL-03 | burner_sim | Short-lived SIM, minimal calls, discarded | label=SUSPICIOUS | MEDIUM |
| TEL-04 | sim_reassignment | Number recycled by operator to new subscriber | label=AMBIGUOUS | HIGH |
| TEL-05 | shared_device | Family shares one phone (common in rural India) | label=INNOCENT | HIGH |
| TEL-06 | shared_sim | Person uses another's SIM temporarily | label=SUSPICIOUS | HIGH |
| TEL-07 | device_reassignment | Device sold/gifted to new person | label=INNOCENT | MEDIUM |
| TEL-08 | cross_region | Person travels, pings distant towers | label=INNOCENT | MEDIUM |
| TEL-09 | geo_anomaly | Impossible location jump (100km/hour) | label=SUSPICIOUS | HIGH |
| TEL-10 | silent_then_burst | 2-week silence then 50 calls in one day | label=SUSPICIOUS | HIGH |
| TEL-11 | coordinated_comm | Group of 5 all call same number within 1 hour | label=SUSPICIOUS | VERY HIGH |
| TEL-12 | tower_hopping | Systematic movement through specific tower sequence | label=AMBIGUOUS | HIGH |

---

## Category 3: Financial Scenarios

| ID | Name | Description | Ground Truth | Difficulty |
|---|---|---|---|---|
| FIN-01 | salary_pattern | Regular monthly deposits from employer | label=INNOCENT | LOW |
| FIN-02 | recurring_bills | Regular outgoing payments (rent, utilities) | label=INNOCENT | LOW |
| FIN-03 | high_value_legit | Legal high-value transfer (property sale, inheritance) | label=INNOCENT | HIGH |
| FIN-04 | structuring | Repeated just-below-threshold deposits | label=FRAUD | HIGH |
| FIN-05 | transaction_burst | 30 transactions in 48 hours | label=SUSPICIOUS | MEDIUM |
| FIN-06 | circular_txn | A→B→C→A transaction loop | label=FRAUD | VERY HIGH |
| FIN-07 | mule_account | Account used to pass through laundered money | label=SUSPECT | HIGH |
| FIN-08 | joint_account | Legitimate joint account (spouses) | label=INNOCENT | LOW |
| FIN-09 | authorized_signatory | Business account with multiple signatories | label=INNOCENT | MEDIUM |
| FIN-10 | proxy_txn | Money transferred via intermediary to hide origin | label=FRAUD | HIGH |
| FIN-11 | dormant_reactivation | Account dormant 2 years then receives large sum | label=SUSPICIOUS | HIGH |
| FIN-12 | rapid_movement | Funds in-and-out within 24 hours | label=SUSPICIOUS | HIGH |
| FIN-13 | geo_txn_anomaly | Transaction from location inconsistent with residence | label=SUSPICIOUS | MEDIUM |
| FIN-14 | corruption_cycle | Regular payments from official to unknown private accounts | label=FRAUD | VERY HIGH |

---

## Category 4: Property Scenarios

| ID | Name | Description | Ground Truth | Difficulty |
|---|---|---|---|---|
| PROP-01 | normal_transfer | Legitimate property sale with proper documentation | label=INNOCENT | LOW |
| PROP-02 | repeated_ownership | Property transferred 3+ times in 1 year | label=SUSPICIOUS | HIGH |
| PROP-03 | suspicious_transfer | Transfer from elderly/vulnerable to unrelated party | label=SUSPICIOUS | HIGH |
| PROP-04 | rapid_resale | Bought and sold within 6 months (possible flip or fraud) | label=AMBIGUOUS | MEDIUM |
| PROP-05 | proxy_ownership | Property in spouse/relative name but suspect pays bills | label=SUSPICIOUS | HIGH |
| PROP-06 | adjacent_mutation | Single transaction covers adjacent properties | label=SUSPICIOUS | VERY HIGH |
| PROP-07 | multi_case_property | Same property appears in multiple cases | label=AMBIGUOUS | HIGH |
| PROP-08 | inconsistent_registry | Registry records conflict with CDR location data | label=SUSPICIOUS | VERY HIGH |
| PROP-09 | benami | Property in name of person with no known income source | label=SUSPICIOUS | HIGH |

---

## Category 5: Crime / Case Scenarios

| ID | Name | Description | Difficulty |
|---|---|---|---|
| CRIME-01 | theft | Single-incident theft with known victim | LOW |
| CRIME-02 | robbery | Armed robbery, multiple suspects | MEDIUM |
| CRIME-03 | burglary | Breaking and entering, property evidence | MEDIUM |
| CRIME-04 | fraud | Multi-victim financial fraud | HIGH |
| CRIME-05 | cyber_fraud | Online fraud, VPN usage | HIGH |
| CRIME-06 | organized_financial | Organized financial crime network | VERY HIGH |
| CRIME-07 | kidnapping | Kidnapping with ransom demand CDRs | HIGH |
| CRIME-08 | missing_person | Person missing, no crime confirmed | MEDIUM |
| CRIME-09 | assault | Physical assault, witness testimony | LOW |
| CRIME-10 | organized_crime | Multi-network organized crime | VERY HIGH |
| CRIME-11 | trafficking | Human trafficking network | VERY HIGH |
| CRIME-12 | extortion | Extortion pattern with financial evidence | HIGH |
| CRIME-13 | illegal_property | Illegal property mutation | HIGH |
| CRIME-14 | vehicle_crime | Vehicle-related crime (theft, hit-and-run) | MEDIUM |
| CRIME-15 | identity_fraud | Large-scale identity fraud operation | VERY HIGH |
| CRIME-16 | suspicious_death | Death with suspicious circumstances | HIGH |
| CRIME-17 | gang_activity | Local gang with clear network structure | HIGH |
| CRIME-18 | repeat_offender | Person with prior cases opens new case | MEDIUM |

---

## Category 6: Adversarial Scenarios (Designed to Fool ML)

| ID | Name | What the ML Must Learn |
|---|---|---|
| ADV-01 | identity_collision | Two innocent people look like one criminal |
| ADV-02 | sim_reassignment | Old criminal pattern on new innocent subscriber |
| ADV-03 | shared_device_family | Family phone looks like coordinated criminal comm |
| ADV-04 | shared_account_couple | Joint account looks like money laundering front |
| ADV-05 | false_positive_network | Close friends look like criminal network |
| ADV-06 | innocent_high_freq | Call center agent looks like network coordinator |
| ADV-07 | cross_case_evidence | Same evidence used in two different cases (legit) |
| ADV-08 | stale_graph_edge | Relationship expired (divorced, fired) but still in graph |
| ADV-09 | contradictory_evidence | Alibi CDR contradicts surveillance observation |
| ADV-10 | delayed_evidence | Key evidence arrives 6 months after events |
| ADV-11 | multi_hop_hidden | Criminal connected to victim via 5 innocent intermediaries |
| ADV-12 | temporal_reversal | Effect appears in CDRs before cause (timestamp error) |
| ADV-13 | property_mutation_decoy | Legitimate adjacent property mutation looks like H4 |
| ADV-14 | coordinated_finance_innocent | Business partners split large payment looks like structuring |
| ADV-15 | geographic_anomaly_innocent | Truck driver pings far-apart towers legitimately |
| ADV-16 | decoy_suspect | Innocent person with all hallmarks of guilt |
| ADV-17 | missing_evidence | Criminal leaves no digital trace |
| ADV-18 | corrupt_source_record | Telecom data has systematic timestamp errors |
| ADV-19 | duplicate_evidence | Same CDR reported by two operators |
| ADV-20 | alias_collision | Two different criminals use same alias |
| ADV-21 | expired_access | Analyst reviews case after access expired |
| ADV-22 | revoked_access | Evidence seen before access was revoked |
| ADV-23 | ai_false_assertion | AI generates incorrect assertion (confidence < 0.7) |
| ADV-24 | sleeper_network | Criminal network dormant for 1 year then active |
| ADV-25 | decentralized_payment | Payment split across 50 small accounts |

---

## Scenario-to-Golden-World Mapping

These Golden World signals must survive into the large-scale world as required regression tests:

| Golden Signal | Large World Equivalent | Regression Test |
|---|---|---|
| SIG-03 (Suresh geo anomaly) | TEL-09 (geo_anomaly) x N instances | verify_phase2b.py L-SIG-03 |
| SIG-05 (Dinesh periodic deposits) | FIN-14 (corruption_cycle) x N instances | verify_phase2b.py I04 |
| SIG-06 (Deepak ₹75K transfer) | FIN-04 (structuring) with low threshold | verify_phase2b.py I05 |
| SIG-08 (periodic comms) | TEL-11 (coordinated_comm) periodic variant | verify_phase2b.py L-SIG-08 |
| FL-06 (Rekha false positive) | ADV-06 (innocent_high_freq) | verify_phase2b.py L-FL-06 |
| H4 (multi-property mutation) | PROP-06 (adjacent_mutation) | verify_phase2b.py K01-K05 |
