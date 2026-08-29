"""
CIVIX Synthetic World V2: Deterministic Seeds
civix_generator/v2/seeds.py

Extends the V1 SeedBank architecture with V2-specific domains.
Each domain gets an independent PCG64 stream so that adding new domains
never shifts the sequence of existing ones.

UUID derivation is identical to V1 (MD5-based) for schema compatibility.
"""
from __future__ import annotations
import hashlib
import uuid as _uuid
from numpy.random import Generator, PCG64


def make_uuid(*parts) -> str:
    """Derive a stable UUID from one or more string/int parts."""
    key = "|".join(str(p) for p in parts)
    return str(_uuid.UUID(hashlib.md5(key.encode()).hexdigest()))


class V2SeedBank:
    """
    Central seed authority for V2.

    Each domain gets an independent PCG64 stream.
    The master seed is the only input — all domain streams are derived from it.
    Two V2SeedBank instances with the same master seed are identical.
    """

    DOMAIN_OFFSETS: dict[str, int] = {
        # Core entity domains (100–199)
        "meta":         100,
        "person":       101,
        "org":          102,
        "location":     103,
        "cell":         104,
        # Telecom domains (200–299)
        "device":       200,
        "sim":          201,
        "phone":        202,
        "cdr":          203,
        "cdr_reciprocal": 204,
        # Financial domains (300–399)
        "account":      300,
        "transaction":  301,
        # Community / network domains (400–499)
        "community":    400,
        "network":      401,
        "contact_pool": 402,
        # Temporal domains (500–599)
        "temporal":     500,
        "lifecycle":    501,
        # Adversarial / scenario domains (600–699)
        "scenario":     600,
        "adversarial":  601,
        "hard_negative": 602,
        "bridge_node":  603,
        # Latent trait domains (700–799)
        "latent":       700,
        "latent_comm":  701,
        "latent_fin":   702,
        "latent_mob":   703,
        "latent_social": 704,
        # Ground truth domains (800–899)
        "ground_truth": 800,
        "labels":       801,
        "split":        802,
        # Noise / misc (900–999)
        "noise":        900,
        "geography":    901,
    }

    def __init__(self, master_seed: int):
        self.master_seed = master_seed
        self._streams: dict[str, Generator] = {}

    def get(self, domain: str) -> Generator:
        """Return the shared RNG stream for a domain."""
        if domain not in self._streams:
            offset = self.DOMAIN_OFFSETS.get(domain, 999)
            self._streams[domain] = Generator(PCG64(self.master_seed + offset))
        return self._streams[domain]

    def entity_rng(self, domain: str, entity_index: int) -> Generator:
        """Return an independent RNG for a single entity (for parallel generation)."""
        offset = self.DOMAIN_OFFSETS.get(domain, 999)
        seed = (
            self.master_seed * 1_000_003
            + offset * 1_000_000
            + entity_index
        ) & 0xFFFF_FFFF_FFFF_FFFF
        return Generator(PCG64(seed))
