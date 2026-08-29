"""
CIVIX Synthetic World V2: Latent Trait Assignment
civix_generator/v2/population.py

Assigns 14 latent traits to every person.

CRITICAL INVARIANT:
    Latent traits are NEVER written to output feature columns.
    They are internal generation parameters only.
    The ML pipeline must never see these values.

Latent traits are drawn from Beta/Gamma distributions with
scenario-conditional biases — but the distributions substantially overlap
across scenario classes. Some normal persons will have high criminal-profile
traits. Some criminals will have low-activity traits.
"""
from __future__ import annotations
import numpy as np
from typing import Any, Dict, List

from .config import V2ProfileConfig
from .seeds import V2SeedBank, make_uuid


# ── Occupation patterns ─────────────────────────────────────────────────────────
# 9am-5pm = standard office hours, shift = rotating hours, 24h = always on,
# irregular = random, business = business hours with peaks
OCCUPATION_PATTERNS = ["office", "shift", "irregular", "business", "retired"]
OCCUPATION_WEIGHTS  = [0.40,     0.20,    0.20,        0.15,       0.05]

# Income bands (0=very_low, 1=low, 2=middle, 3=high, 4=very_high)
INCOME_BANDS   = [0, 1, 2, 3, 4]
INCOME_WEIGHTS = [0.10, 0.25, 0.40, 0.20, 0.05]


def _sample_beta(rng: np.random.Generator, alpha: float, beta: float, n: int) -> np.ndarray:
    """Sample from Beta(alpha, beta). Clipped to [0.01, 0.99]."""
    return np.clip(rng.beta(alpha, beta, size=n), 0.01, 0.99)


def assign_population(
    config: V2ProfileConfig,
    seed_bank: V2SeedBank,
) -> List[Dict[str, Any]]:
    """
    Build the full population index with latent traits.

    Returns a list of dicts, one per person.
    This entire list fits in RAM (~200 bytes × n_persons = ~50 MB for 250k).

    Latent traits in this dict are used during generation but must never
    be written to the observable Parquet output columns.
    """
    n = config.persons
    rng_scenario  = seed_bank.get("scenario")
    rng_latent    = seed_bank.get("latent")
    rng_latent_c  = seed_bank.get("latent_comm")
    rng_latent_f  = seed_bank.get("latent_fin")
    rng_latent_m  = seed_bank.get("latent_mob")
    rng_latent_s  = seed_bank.get("latent_social")
    rng_person    = seed_bank.get("person")

    dist = config.scenario_dist
    lp   = config.latent_params

    # ── Scenario class assignment ────────────────────────────────────────────
    classes  = ["normal", "suspicious", "confirmed_pattern", "false_positive"]
    weights  = [dist.normal, dist.suspicious, dist.confirmed_pattern, dist.false_positive]
    sc_arr   = rng_scenario.choice(classes, size=n, p=weights)

    # ── Batch-sample all latent traits per class ─────────────────────────────
    # We sample each trait for all n persons using their scenario class.
    # Because distributions overlap, we can't just concatenate class-specific arrays —
    # we sample class-by-class then assemble.

    comm_activity    = np.zeros(n, dtype=np.float32)
    fin_activity     = np.zeros(n, dtype=np.float32)
    mobility         = np.zeros(n, dtype=np.float32)
    social           = np.zeros(n, dtype=np.float32)
    night_activity   = np.zeros(n, dtype=np.float32)
    device_stability = np.zeros(n, dtype=np.float32)
    centrality       = np.zeros(n, dtype=np.float32)

    for sc in classes:
        mask = (sc_arr == sc)
        count = int(mask.sum())
        if count == 0:
            continue

        a, b = lp.comm_activity[sc]
        comm_activity[mask]    = _sample_beta(rng_latent_c, a, b, count)

        a, b = lp.fin_activity[sc]
        fin_activity[mask]     = _sample_beta(rng_latent_f, a, b, count)

        a, b = lp.mobility[sc]
        mobility[mask]         = _sample_beta(rng_latent_m, a, b, count)

        a, b = lp.social[sc]
        social[mask]           = _sample_beta(rng_latent_s, a, b, count)

        a, b = lp.night[sc]
        night_activity[mask]   = _sample_beta(rng_latent, a, b, count)

        a, b = lp.device_stability[sc]
        device_stability[mask] = _sample_beta(rng_latent, a, b, count)

        a, b = lp.centrality[sc]
        centrality[mask]       = _sample_beta(rng_latent, a, b, count)

    # ── Other scalar traits ──────────────────────────────────────────────────
    income_bands = rng_person.choice(INCOME_BANDS, size=n, p=INCOME_WEIGHTS)
    occupations  = rng_person.choice(OCCUPATION_PATTERNS, size=n, p=OCCUPATION_WEIGHTS)
    # geographic_radius: Gamma(k=2, θ=50) → mean 100km, heavy tail
    geo_radius   = np.clip(rng_person.gamma(shape=2.0, scale=50.0, size=n), 5.0, 1500.0)
    # business_activity: Bernoulli
    is_business  = rng_person.random(n) < (
        0.08 + 0.12 * fin_activity   # higher financial activity → more likely business
    )
    # phone_churn: Beta(1.5, 5) → mean ≈ 0.23
    phone_churn  = _sample_beta(rng_person, 1.5, 5.0, n)
    # Adjust: low device_stability → higher phone_churn
    phone_churn  = np.clip(phone_churn + (1.0 - device_stability) * 0.2, 0.01, 0.99)
    # transaction_frequency: Gamma(k=1.5, θ=0.8) → typical is ~1.2 txns/day
    txn_freq     = np.clip(rng_person.gamma(shape=1.5, scale=0.8, size=n), 0.05, 20.0)
    # risk_exposure: internal hidden score — this MUST NEVER flow to feature columns
    # Biased by scenario but substantially overlapping
    risk_exposure = np.zeros(n, dtype=np.float32)
    for sc in classes:
        mask = (sc_arr == sc)
        count = int(mask.sum())
        if count == 0:
            continue
        a_map = {"normal": (1.5, 5.0), "suspicious": (2.5, 3.5),
                 "confirmed_pattern": (4.0, 2.5), "false_positive": (2.0, 4.0)}
        a, b = a_map[sc]
        risk_exposure[mask] = _sample_beta(rng_latent, a, b, count)

    # ── Geography: home region ─────────────────────────────────────────────────
    n_regions = 10
    home_regions = rng_person.integers(0, n_regions, size=n)

    # ── Active window ─────────────────────────────────────────────────────────
    total_days = config.total_days
    # Most persons are active from near the start; some join later
    active_starts = rng_person.integers(0, total_days // 6, size=n)
    active_ends   = np.clip(
        rng_person.integers(total_days * 2 // 3, total_days, size=n),
        active_starts + 30,
        total_days - 1,
    )

    # ── Assemble population ───────────────────────────────────────────────────
    population: List[Dict[str, Any]] = []
    for i in range(n):
        population.append({
            # Identity
            "person_index":        i,
            "person_id":           make_uuid("civix-v2-person", config.seed, i),
            # Scenario (hidden ground truth — not the same as the label)
            "scenario_class":      str(sc_arr[i]),

            # ── LATENT TRAITS — NEVER WRITE THESE TO FEATURE COLUMNS ──────────
            "_comm_activity":      float(comm_activity[i]),
            "_fin_activity":       float(fin_activity[i]),
            "_mobility":           float(mobility[i]),
            "_social":             float(social[i]),
            "_night_activity":     float(night_activity[i]),
            "_income_band":        int(income_bands[i]),
            "_device_stability":   float(device_stability[i]),
            "_phone_churn":        float(phone_churn[i]),
            "_geo_radius_km":      float(geo_radius[i]),
            "_is_business":        bool(is_business[i]),
            "_occupation":         str(occupations[i]),
            "_centrality_tendency": float(centrality[i]),
            "_txn_freq_per_day":   float(txn_freq[i]),
            "_risk_exposure":      float(risk_exposure[i]),   # STRICTLY INTERNAL

            # Geography / activity window
            "home_region":         int(home_regions[i]),
            "active_start_day":    int(active_starts[i]),
            "active_end_day":      int(active_ends[i]),
        })

    return population
