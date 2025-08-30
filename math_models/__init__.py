"""
Init for math module in blackboxprogramming.

This package contains various mathematical models drawn from physics, computing, and machine learning.
"""

from .equations import (
    langevin_step,
    fokker_planck_rhs,
    lindblad_master_equation,
    born_rule_update,
    entanglement_entropy,
    mutual_information,
    natural_gradient,
    quantum_speed_limits,
    softmax_policy,
    bayesian_update,
    free_energy,
    landauer_minimum_work,
    jarzynski_average,
    lieb_robinson_bound,
    bekenstein_entropy_bound,
    renormalization_flow_step,
)

__all__ = [
    "langevin_step",
    "fokker_planck_rhs",
    "lindblad_master_equation",
    "born_rule_update",
    "entanglement_entropy",
    "mutual_information",
    "natural_gradient",
    "quantum_speed_limits",
    "softmax_policy",
    "bayesian_update",
    "free_energy",
    "landauer_minimum_work",
    "jarzynski_average",
    "lieb_robinson_bound",
    "bekenstein_entropy_bound",
    "renormalization_flow_step",
]
