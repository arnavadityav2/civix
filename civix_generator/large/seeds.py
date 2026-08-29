"""
CIVIX Large-Scale Generator: Deterministic Seeds
civix_generator/large/seeds.py

Provides hierarchical, deterministic seeding so that the same
profile + seed + generator_version always produce identical UUIDs.
"""
import hashlib
import uuid as _uuid
from numpy.random import Generator, PCG64


# ─── UUID derivation ─────────────────────────────────────────────────────────

def make_uuid(*parts) -> str:
    """Derive a stable UUID from one or more string/int parts.

    make_uuid("civix-large-person", 20260829, 42)
    → always the same UUID for profile + seed + index 42
    """
    key = "|".join(str(p) for p in parts)
    return str(_uuid.UUID(hashlib.md5(key.encode()).hexdigest()))


# ─── RNG factory ─────────────────────────────────────────────────────────────

class SeedBank:
    """Central seed authority.

    Keeps one independent PCG64 stream per domain so that adding
    a new generator stage never shifts the sequence of existing stages.
    """

    DOMAIN_OFFSETS = {
        "meta":         0,
        "person":       1,
        "org":          2,
        "device":       3,
        "sim":          4,
        "phone":        5,
        "account":      6,
        "property":     7,
        "vehicle":      8,
        "location":     9,
        "case":        10,
        "cdr":         11,
        "transaction": 12,
        "event":       13,
        "observation": 14,
        "extraction":  15,
        "assertion":   16,
        "hypothesis":  17,
        "lead":        18,
        "scenario":    19,
        "noise":       20,
    }

    def __init__(self, master_seed: int):
        self.master_seed = master_seed
        self._streams: dict[str, Generator] = {}

    def get(self, domain: str) -> Generator:
        if domain not in self._streams:
            offset = self.DOMAIN_OFFSETS.get(domain, 99)
            self._streams[domain] = Generator(PCG64(self.master_seed + offset))
        return self._streams[domain]

    def entity_rng(self, domain: str, entity_index: int) -> Generator:
        """Return an independent RNG specific to a single entity.

        Useful for parallel / shard-level generation where the
        global stream ordering would be unpredictable.
        """
        seed = (self.master_seed * 1_000_003 + self.DOMAIN_OFFSETS.get(domain, 99) * 1_000_000 + entity_index) & 0xFFFFFFFFFFFFFFFF
        return Generator(PCG64(seed))
