"""
CIVIX Synthetic World V2: Community Structure Generator
civix_generator/v2/community.py

Generates the community graph that CDRs are later drawn from.

Communities represent real-world social structures:
- Family groups (2–8 members)
- Workplace groups (10–200 members)
- Social groups (5–50 members)
- Criminal networks (3–25 members, assigned to suspicious/confirmed persons)

A single person can belong to multiple communities.
This is the primary mechanism that creates non-trivial graph structure
with realistic clustering and community topology.

OUTPUTS:
    person_community_map:
        Dict[person_index → List[community_id]]
    community_catalog:
        Dict[community_id → {type, size, members, region, is_criminal}]
    contact_pools:
        Dict[person_index → List[person_index]]   (pre-built contact pool)
"""
from __future__ import annotations
import numpy as np
from typing import Any, Dict, List, Optional, Set, Tuple

from .config import V2ProfileConfig, CommunityParams
from .seeds import V2SeedBank

COMMUNITY_TYPES = ["family", "workplace", "social", "criminal"]


def _triangular_int(rng: np.random.Generator, lo: int, mode: int, hi: int) -> int:
    """Draw from a triangular distribution and return as int."""
    val = rng.triangular(lo, mode, hi)
    return max(lo, min(hi, int(round(val))))


def build_communities(
    population: List[Dict[str, Any]],
    config: V2ProfileConfig,
    seed_bank: V2SeedBank,
) -> Tuple[Dict[int, List[int]], Dict[int, Dict[str, Any]]]:
    """
    Build community memberships for the full population.

    Returns:
        contact_pools: person_index → list of person_indices they communicate with
        community_catalog: community_id → metadata dict
    """
    rng = seed_bank.get("community")
    cp  = config.community_params
    n   = len(population)

    # Index persons by scenario class
    normal_idx    = [p["person_index"] for p in population if p["scenario_class"] == "normal"]
    suspicious_idx = [p["person_index"] for p in population if p["scenario_class"] == "suspicious"]
    confirmed_idx = [p["person_index"] for p in population if p["scenario_class"] == "confirmed_pattern"]
    fp_idx        = [p["person_index"] for p in population if p["scenario_class"] == "false_positive"]
    all_idx       = list(range(n))

    # ── person_community_map[i] = list of community_ids this person belongs to
    person_comm_map: Dict[int, List[int]] = {i: [] for i in range(n)}
    community_catalog: Dict[int, Dict[str, Any]] = {}
    comm_id_counter = 0

    def add_community(
        members: List[int],
        comm_type: str,
        is_criminal: bool = False,
        region: int = 0,
    ) -> int:
        nonlocal comm_id_counter
        cid = comm_id_counter
        comm_id_counter += 1
        community_catalog[cid] = {
            "community_id":  cid,
            "type":          comm_type,
            "size":          len(members),
            "members":       members,
            "region":        region,
            "is_criminal":   is_criminal,
        }
        for m in members:
            person_comm_map[m].append(cid)
        return cid

    # ── 1. Family communities ─────────────────────────────────────────────────
    n_families = int(n * cp.family_fraction / 4)   # average family ≈ 4 members
    remaining_for_family = list(rng.permutation(all_idx))
    ptr = 0
    for _ in range(n_families):
        if ptr >= len(remaining_for_family):
            break
        size = _triangular_int(rng, cp.family_size[0], cp.family_size[1], cp.family_size[2])
        size = min(size, len(remaining_for_family) - ptr)
        members = remaining_for_family[ptr: ptr + size]
        ptr += size
        # Families share a home region
        region = int(population[members[0]]["home_region"])
        add_community(members, "family", is_criminal=False, region=region)

    # ── 2. Workplace communities ──────────────────────────────────────────────
    n_workers = int(n * cp.workplace_fraction)
    worker_pool = list(rng.permutation(all_idx)[:n_workers])
    ptr = 0
    while ptr < len(worker_pool):
        size = _triangular_int(rng, cp.workplace_size[0], cp.workplace_size[1], cp.workplace_size[2])
        size = min(size, len(worker_pool) - ptr)
        members = worker_pool[ptr: ptr + size]
        ptr += size
        region = int(rng.integers(0, 10))
        add_community(members, "workplace", is_criminal=False, region=region)

    # ── 3. Social group communities ───────────────────────────────────────────
    n_social_members = int(n * cp.social_group_fraction)
    social_pool = list(rng.permutation(all_idx)[:n_social_members])
    ptr = 0
    while ptr < len(social_pool):
        size = _triangular_int(rng, cp.social_size[0], cp.social_size[1], cp.social_size[2])
        size = min(size, len(social_pool) - ptr)
        members = social_pool[ptr: ptr + size]
        ptr += size
        region = int(rng.integers(0, 10))
        add_community(members, "social", is_criminal=False, region=region)

    # ── 4. Criminal networks ──────────────────────────────────────────────────
    # Only assigned to suspicious + confirmed_pattern persons
    # Criminal networks have multiple topology types:
    # hub-and-spoke, chain, ring, distributed, coordinator+peripherals
    criminal_pool_base = confirmed_idx + suspicious_idx
    n_criminal_members = int(len(criminal_pool_base) * cp.criminal_network_fraction)
    criminal_pool = list(rng.permutation(criminal_pool_base)[:n_criminal_members])

    network_types = ["hub_spoke", "chain", "ring", "distributed", "coordinator"]
    ptr = 0
    while ptr < len(criminal_pool):
        size = _triangular_int(rng, cp.criminal_size[0], cp.criminal_size[1], cp.criminal_size[2])
        size = min(size, len(criminal_pool) - ptr)
        if size < 2:
            break
        members = criminal_pool[ptr: ptr + size]
        ptr += size
        region = int(rng.integers(0, 10))
        net_type = str(rng.choice(network_types))
        cid = add_community(members, f"criminal_{net_type}", is_criminal=True, region=region)

    # ── 5. Bridge nodes ───────────────────────────────────────────────────────
    # Legitimate-looking persons who bridge between a criminal and a legitimate community
    ap = config.adversarial_params
    n_bridges = max(1, int(n * ap.bridge_node_rate))
    bridge_pool = list(rng.choice(normal_idx + fp_idx, size=min(n_bridges, len(normal_idx)), replace=False))
    for bridge_idx in bridge_pool:
        # Find a criminal community and a legitimate community
        criminal_comms = [
            cid for cid, meta in community_catalog.items()
            if meta["is_criminal"] and len(meta["members"]) > 0
        ]
        legit_comms = [
            cid for cid, meta in community_catalog.items()
            if not meta["is_criminal"] and len(meta["members"]) > 0
        ]
        if criminal_comms and legit_comms:
            crim_cid = int(rng.choice(criminal_comms))
            legit_cid = int(rng.choice(legit_comms))
            # Add bridge person to both communities
            community_catalog[crim_cid]["members"].append(bridge_idx)
            person_comm_map[bridge_idx].append(crim_cid)
            community_catalog[legit_cid]["members"].append(bridge_idx)
            person_comm_map[bridge_idx].append(legit_cid)
            # Mark bridge
            community_catalog[crim_cid]["has_bridge"] = True

    # ── Build contact pools ────────────────────────────────────────────────────
    contact_pools = _build_contact_pools(
        population, person_comm_map, community_catalog, config, rng
    )

    return contact_pools, community_catalog


def _build_contact_pools(
    population: List[Dict[str, Any]],
    person_comm_map: Dict[int, List[int]],
    community_catalog: Dict[int, Dict[str, Any]],
    config: V2ProfileConfig,
    rng: np.random.Generator,
) -> Dict[int, List[int]]:
    """
    Build each person's contact pool: the set of persons they will call.

    Contact pool = community members (in-community calls) + weak-tie random contacts.
    Weak ties prevent communities from being completely closed structures.
    """
    cp = config.community_params
    n  = len(population)
    within_frac = cp.within_community_call_fraction
    max_weak_ties = 30   # cap on random contacts per person

    contact_pools: Dict[int, List[int]] = {}

    for person in population:
        i = person["person_index"]
        comm_ids = person_comm_map[i]

        # Gather all community members (exclude self)
        in_comm: Set[int] = set()
        for cid in comm_ids:
            members = community_catalog[cid]["members"]
            for m in members:
                if m != i:
                    in_comm.add(m)

        # Add weak-tie random contacts from rest of population
        n_weak = int(rng.integers(2, max_weak_ties + 1))
        weak_pool = rng.integers(0, n, size=n_weak * 3)
        weak = [int(w) for w in weak_pool if w != i and w not in in_comm][:n_weak]

        # Combine: in-community first (prioritized during CDR sampling)
        pool = list(in_comm) + weak
        if not pool:
            # Fallback: random persons
            pool = [int(rng.integers(0, n)) for _ in range(5) if rng.integers(0, n) != i]
            pool = pool or [0]

        contact_pools[i] = pool

    return contact_pools
