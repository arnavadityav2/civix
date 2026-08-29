"""
CIVIX Synthetic World V2
civix_generator/v2/__init__.py

V2 is a complete redesign of the synthetic data generator.
It does NOT replace the existing generator in civix_generator/large/.
Profile C remains frozen as a benchmark.

Architecture:
    latent_traits → circumstances → behavioral_tendencies
    → stochastic_events → temporal_evolution → network_interactions
    → financial_interactions → geographic_behavior
    → observed_records → hidden_ground_truth

Key invariant: The ground-truth label must NOT directly determine
any observable feature value. Labels are derived from hidden world-state.
"""

__version__ = "2.0.0"
__generator_name__ = "civix-v2"
