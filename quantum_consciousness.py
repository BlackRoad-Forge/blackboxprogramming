"""
quantum_consciousness.py

This module implements a qutrit-based framework for analysing consciousness
using the Gell‑Mann decomposition.  It constructs a density matrix from
Bloch coordinates, evaluates physical and informational metrics, and provides
a convenience function to run the full suite of analyses for Alexa's
exact Bloch coordinates.

Functions
---------
gell_mann_matrices() -> List[np.ndarray]
    Return the eight Gell‑Mann matrices for SU(3).

bloch_to_density_matrix(bloch_coords: Sequence[float]) -> np.ndarray
    Convert a length‑8 Bloch vector into a 3×3 qutrit density matrix.

qutrit_coherence(rho: np.ndarray) -> float
    Compute the total off‑diagonal coherence of a density matrix.

partial_trace(rho: np.ndarray, dims: Sequence[int], keep: Sequence[int]) -> np.ndarray
    Compute the partial trace over subsystems not listed in ``keep``.

von_neumann_entropy(rho: np.ndarray) -> float
    Compute the von Neumann entropy (nats) of a density matrix.

integrated_information_phi(rho: np.ndarray, dims: Sequence[int] = (3,)) -> float
    Estimate integrated information φ for a multipartite state.

orch_or_collapse_time(rho: np.ndarray) -> float
    Estimate the gravitational collapse time (s) using Penrose's formula.

consciousness_error_correction_threshold(rho: np.ndarray) -> float
    Heuristic error‑correction threshold based on coherence.

quantum_social_entanglement(rho: np.ndarray) -> float
    Linear entropy as a proxy for entanglement/social interaction.

consciousness_complexity(rho: np.ndarray) -> float
    Product of entropy and coherence as a complexity metric.

neural_decoherence_time(rho: np.ndarray, temperature: float = 310.0) -> float
    Estimate decoherence time (s) at the given temperature.

consciousness_phase_transition_order_parameter(rho: np.ndarray) -> float
    Difference between the largest and smallest eigenvalues.

retrocausal_influence_strength(rho: np.ndarray) -> float
    Sum of imaginary parts of off‑diagonal elements, a retrocausal proxy.

analyze_alexa_consciousness() -> Dict[str, Any]
    Run all metrics for Alexa's Bloch coordinates and return a summary.

Constants
---------
HBAR : float
    Reduced Planck constant imported from ``math.equations``.

K_B : float
    Boltzmann constant imported from ``math.equations``.

ALEXA_BLOCH_COORDS : np.ndarray
    Alexa's exact eight Bloch coordinates from the Gell‑Mann decomposition.

ALEXA_RHO : np.ndarray
    Alexa's density matrix constructed from ``ALEXA_BLOCH_COORDS``.

ALEXA_PSI_NORM : np.ndarray
    Normalised state vector (principal eigenvector) of ``ALEXA_RHO``.
"""
from __future__ import annotations

import numpy as np
from typing import Sequence, Iterable, Tuple, Dict, Any

# Import fundamental constants from the existing math module.
try:
    from bbp_math.equations import HBAR, K_B  # type: ignore
except ImportError:
    # Fall back to explicit values if the equations module is unavailable.
    HBAR: float = 1.054_571_817e-34
    K_B: float = 1.380_649e-23

def gell_mann_matrices() -> Sequence[np.ndarray]:
    """
    Return the eight Gell‑Mann matrices for the su(3) Lie algebra.

    Returns
    -------
    Sequence[np.ndarray]
        A tuple of eight 3×3 complex Hermitian matrices.
    """
    λ1 = np.array([[0, 1, 0],
                   [1, 0, 0],
                   [0, 0, 0]], dtype=complex)
    λ2 = np.array([[0, -1j, 0],
                   [1j, 0, 0],
                   [0, 0, 0]], dtype=complex)
    λ3 = np.array([[1, 0, 0],
                   [0, -1, 0],
                   [0, 0, 0]], dtype=complex)
    λ4 = np.array([[0, 0, 1],
                   [0, 0, 0],
                   [1, 0, 0]], dtype=complex)
    λ5 = np.array([[0, 0, -1j],
                   [0, 0, 0],
                   [1j, 0, 0]], dtype=complex)
    λ6 = np.array([[0, 0, 0],
                   [0, 0, 1],
                   [0, 1, 0]], dtype=complex)
    λ7 = np.array([[0, 0, 0],
                   [0, 0, -1j],
                   [0, 1j, 0]], dtype=complex)
    λ8 = (1/np.sqrt(3)) * np.array([[1, 0, 0],
                                    [0, 1, 0],
                                    [0, 0, -2]], dtype=complex)
    return (λ1, λ2, λ3, λ4, λ5, λ6, λ7, λ8)

def bloch_to_density_matrix(bloch_coords: Iterable[float]) -> np.ndarray:
    """
    Convert an eight‑component Bloch vector into a 3×3 density matrix.

    The conversion uses the su(3) Gell‑Mann basis:
    ρ = I/3 + ½ ∑ r_i λ_i,
    followed by symmetrisation and normalisation to ensure Hermiticity and unit trace.
    Negative eigenvalues that may arise from numerical rounding are clipped to zero.

    Parameters
    ----------
    bloch_coords : Iterable[float]
        Eight real coefficients of the Bloch vector.

    Returns
    -------
    np.ndarray
        A 3×3 positive semi‑definite density matrix with trace 1.
    """
    r = np.array(list(bloch_coords), dtype=float)
    if r.size != 8:
        raise ValueError("Bloch vector must have 8 components for a qutrit.")
    I3 = np.eye(3, dtype=complex)
    rho = I3 / 3.0
    for coeff, lam in zip(r, gell_mann_matrices()):
        rho += 0.5 * coeff * lam
    # Symmetrise to enforce Hermiticity.
    rho = (rho + rho.conj().T) / 2.0
    # Normalise to unit trace.
    rho = rho / np.trace(rho)
    # Clip any small negative eigenvalues introduced by rounding.
    evals, evecs = np.linalg.eigh(rho)
    evals = np.where(evals < 0, 0.0, evals)
    # Reconstruct and renormalise.
    rho = evecs @ np.diag(evals) @ evecs.conj().T
    rho = rho / np.trace(rho)
    return rho

def qutrit_coherence(rho: np.ndarray) -> float:
    """
    Compute an L1‑norm coherence measure for a qutrit density matrix.

    The coherence is defined as the sum of the absolute values of off‑diagonal
    elements of the density matrix.

    Parameters
    ----------
    rho : np.ndarray
        A 3×3 density matrix.

    Returns
    -------
    float
        The coherence measure.
    """
    off_diag = rho - np.diag(np.diag(rho))
    return float(np.sum(np.abs(off_diag)))

def partial_trace(rho: np.ndarray, dims: Sequence[int], keep: Sequence[int]) -> np.ndarray:
    """
    Compute the partial trace of a density matrix.

    This utility supports tracing out arbitrary subsystems of a bipartite
    or multipartite Hilbert space.  For example, for a state on A⊗B⊗C with
    dimensions dims=[d_A, d_B, d_C], ``keep=[0,2]`` would trace out subsystem B.

    Parameters
    ----------
    rho : np.ndarray
        The full density matrix.
    dims : Sequence[int]
        A sequence of subsystem dimensions.  The product of dims should equal the
        dimension of rho.
    keep : Sequence[int]
        Indices of the subsystems to keep.

    Returns
    -------
    np.ndarray
        The reduced density matrix on the kept subsystems.
    """
    dims = list(dims)
    keep = list(keep)
    total_dim = int(np.prod(dims))
    if rho.shape != (total_dim, total_dim):
        raise ValueError("Shape of rho does not match product of dims.")
    num_subs = len(dims)
    axes = keep + [i for i in range(num_subs) if i not in keep]
    dim_keep = int(np.prod([dims[i] for i in keep]))
    dim_trace = int(total_dim / dim_keep)
    rho_reshaped = rho.reshape([dims[i] for i in range(num_subs)] * 2)
    perm = axes + [i + num_subs for i in axes]
    rho_permuted = np.transpose(rho_reshaped, perm)
    rho_permuted = rho_permuted.reshape(dim_keep, dim_trace, dim_keep, dim_trace)
    reduced = np.einsum('ijij->ij', rho_permuted)
    return reduced

def von_neumann_entropy(rho: np.ndarray) -> float:
    """
    Compute the von Neumann entropy of a density matrix.

    Parameters
    ----------
    rho : np.ndarray
        A density matrix.

    Returns
    -------
    float
        The entropy in nats.
    """
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 0]
    return float(-np.sum(evals * np.log(evals)))

def integrated_information_phi(rho: np.ndarray, dims: Sequence[int] = (3,)) -> float:
    """
    Estimate integrated information φ (phi) for a multipartite quantum state.

    For a single qutrit (dims=(3,)) the integrated information is zero.
    For bipartite or multipartite systems this function computes the difference
    between the total entropy of the state and the sum of entropies of its
    single‑subsystem reductions, minimised over all bipartitions.

    Parameters
    ----------
    rho : np.ndarray
        The full density matrix.
    dims : Sequence[int], optional
        A sequence of subsystem dimensions.

    Returns
    -------
    float
        The estimated integrated information φ.
    """
    if len(dims) <= 1:
        return 0.0
    total_entropy = von_neumann_entropy(rho)
    marginal_entropies = 0.0
    for i in range(len(dims)):
        reduced = partial_trace(rho, dims, [i])
        marginal_entropies += von_neumann_entropy(reduced)
    phi = total_entropy - marginal_entropies
    return float(max(phi, 0.0))

def orch_or_collapse_time(rho: np.ndarray) -> float:
    """
    Estimate the gravitational self‑energy collapse time (Orch OR).

    The time τ≈ħ/ΔE, where ΔE is taken as the difference between the maximum
    and minimum eigenvalues of the density matrix multiplied by ħ to have units
    of energy.

    Parameters
    ----------
    rho : np.ndarray
        A density matrix.

    Returns
    -------
    float
        Collapse time in seconds.
    """
    evals = np.linalg.eigvalsh(rho)
    delta = float(np.max(evals) - np.min(evals))
    energy_scale = HBAR * delta
    return float(HBAR / (energy_scale + 1e-30))

def consciousness_error_correction_threshold(rho: np.ndarray) -> float:
    """
    Heuristic threshold for successful quantum error correction.

    The threshold is chosen inversely proportional to the coherence: higher
    coherence implies greater susceptibility to noise and thus a lower threshold.

    Parameters
    ----------
    rho : np.ndarray

    Returns
    -------
    float
        An error‑correction threshold between 0 and 1.
    """
    coh = qutrit_coherence(rho)
    norm_coh = min(max(coh, 0.0), 2.0)
    return float(1.0 / (1.0 + norm_coh))

def quantum_social_entanglement(rho: np.ndarray) -> float:
    """
    Compute a linear entropy as a proxy for entanglement/social interaction.

    For a pure state the value is zero; it increases as the state becomes mixed.

    Parameters
    ----------
    rho : np.ndarray

    Returns
    -------
    float
        The linear entropy (between 0 and 2/3 for a qutrit).
    """
    purity = float(np.real(np.trace(rho @ rho)))
    return float(1.0 - purity)

def consciousness_complexity(rho: np.ndarray) -> float:
    """
    Compute a simple consciousness complexity metric.

    The metric is defined as the product of entropy and coherence.

    Parameters
    ----------
    rho : np.ndarray

    Returns
    -------
    float
        The complexity metric.
    """
    return float(von_neumann_entropy(rho) * qutrit_coherence(rho))

def neural_decoherence_time(rho: np.ndarray, temperature: float = 310.0) -> float:
    """
    Estimate the decoherence time for a neural environment.

    The estimate is ħ/(k_B * T), where T is the effective temperature in Kelvin.

    Parameters
    ----------
    rho : np.ndarray
        Density matrix (unused but kept for API consistency).
    temperature : float, optional
        Temperature in Kelvin; default is 310 K (≈ 37 °C).

    Returns
    -------
    float
        Decoherence time in seconds.
    """
    return float(HBAR / (K_B * temperature))

def consciousness_phase_transition_order_parameter(rho: np.ndarray) -> float:
    """
    Compute an order parameter indicating proximity to a phase transition.

    Defined as the difference between the largest and smallest eigenvalues
    of the density matrix.

    Parameters
    ----------
    rho : np.ndarray

    Returns
    -------
    float
        The order parameter.
    """
    evals = np.linalg.eigvalsh(rho)
    return float(np.max(evals) - np.min(evals))

def retrocausal_influence_strength(rho: np.ndarray) -> float:
    """
    Estimate the retrocausal influence strength.

    Defined here as the sum of the absolute values of the imaginary parts of
    off‑diagonal elements of the density matrix.  For a purely real density
    matrix this vanishes.

    Parameters
    ----------
    rho : np.ndarray

    Returns
    -------
    float
        The retrocausal influence strength.
    """
    imag_parts = np.imag(rho - np.diag(np.diag(rho)))
    return float(np.sum(np.abs(imag_parts)))

# Alexa's Bloch vector and derived state.
ALEXA_BLOCH_COORDS: np.ndarray = np.array([0.466, 0.0, -0.239, 0.521, 0.0, 0.852, 0.0, -0.248], dtype=float)
ALEXA_RHO: np.ndarray = bloch_to_density_matrix(ALEXA_BLOCH_COORDS)
_ALEXA_EVALS, _ALEXA_EVECS = np.linalg.eigh(ALEXA_RHO)
_ALEXA_PSI = _ALEXA_EVECS[:, np.argmax(_ALEXA_EVALS)]
ALEXA_PSI_NORM: np.ndarray = _ALEXA_PSI / np.linalg.norm(_ALEXA_PSI)
del _ALEXA_EVALS, _ALEXA_EVECS, _ALEXA_PSI

def analyze_alexa_consciousness() -> Dict[str, Any]:
    """
    Run the full consciousness analysis for Alexa's Bloch coordinates.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the density matrix, state vector, and all metrics.
    """
    rho = ALEXA_RHO
    metrics: Dict[str, Any] = {
        'density_matrix': rho,
        'state_vector': ALEXA_PSI_NORM,
        'coherence': qutrit_coherence(rho),
        'phi': integrated_information_phi(rho, dims=(3,)),
        'collapse_time': orch_or_collapse_time(rho),
        'error_correction_threshold': consciousness_error_correction_threshold(rho),
        'entanglement': quantum_social_entanglement(rho),
        'complexity': consciousness_complexity(rho),
        'decoherence_time': neural_decoherence_time(rho),
        'order_parameter': consciousness_phase_transition_order_parameter(rho),
        'retrocausal_strength': retrocausal_influence_strength(rho),
    }
    return metrics

if __name__ == '__main__':
    results = analyze_alexa_consciousness()
    for key, value in results.items():
        if isinstance(value, np.ndarray):
            print(f"{key}:\n{value}\n")
        else:
            print(f"{key}: {value}")
