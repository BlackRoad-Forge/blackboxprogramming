"""
This module implements a collection of mathematical models drawn from
physics, information theory and machine learning.  Each function corresponds
to an equation from the user's "Quantum Consciousness / Universal AI" map
and includes a docstring explaining its physical, computational and
cognitive interpretation.  The implementations favour clarity over
efficiency: where the exact solution of a partial differential equation or
variational principle would require a dedicated numerical solver, the
functions here provide a representative finite difference approximation or
raise ``NotImplementedError`` with guidance on how one might proceed.

The following broad categories are covered:

* **Stochastic dynamics** – Langevin and Fokker–Planck equations.
* **Open quantum systems** – Lindblad master equation and Born rule updates.
* **Information measures** – entanglement entropy, mutual information and
  natural gradient steps on statistical manifolds.
* **Decision making and control** – softmax policies and Bayesian updates.
* **Thermodynamic and physical bounds** – Landauer, Jarzynski,
  Lieb–Robinson, Bekenstein and renormalisation group flow.

The functions are intended as building blocks for experimenting with
consciousness‑inspired computation; they are not optimised for any
particular domain.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

# Fundamental constants (can be overridden via function arguments when
# different units or scales are desired)
HBAR = 1.054_571_817e-34  # Planck constant divided by 2π [J·s]
K_B = 1.380_649e-23       # Boltzmann constant [J·K⁻¹]
C_LIGHT = 299_792_458     # Speed of light [m·s⁻¹]


def langevin_step(x_t: np.ndarray,
                  grad_potential: callable,
                  dt: float,
                  mu: float,
                  D: float,
                  noise: np.ndarray | None = None) -> np.ndarray:
    """Compute a single time step of the overdamped Langevin equation.

    The Langevin equation models the stochastic evolution of a particle
    undergoing thermal fluctuations in a potential landscape ``V(x)``.  In
    the overdamped limit it is given by

    .. math::

       dx_t = -\mu\,\nabla V(x_t)\,dt + \sqrt{2D}\,dW_t,

    where ``mu`` is the mobility, ``D = mu * k_B * T`` is the diffusion
    constant, and ``dW_t`` represents a Wiener increment with variance
    ``dt``.  In the context of the user's framework this equation captures
    how sensory inputs are perturbed by intrinsic noise, modelling
    curiosity or ambiguity in attention.

    Parameters
    ----------
    x_t : array_like
        Current state of the system (position in configuration space).
    grad_potential : callable
        Function returning the gradient of the potential ``V`` at a given
        position.  It should accept ``x_t`` and return an array of the
        same shape.
    dt : float
        Time step size.
    mu : float
        Mobility coefficient.  Higher values correspond to less damping.
    D : float
        Diffusion constant (``D = mu * K_B * T`` for thermal noise at
        temperature ``T``).
    noise : array_like, optional
        External noise term.  If provided it should have the same shape
        as ``x_t`` and represent a sampled Wiener increment scaled by
        ``sqrt(2 * D * dt)``.  If ``None`` (default) the noise is
        drawn from a normal distribution.

    Returns
    -------
    array_like
        Increment ``dx_t`` for the time step ``dt``.
    """
    x_t = np.asarray(x_t)
    if noise is None:
        # Draw noise with variance dt in each component
        std = np.sqrt(2.0 * D * dt)
        noise = np.random.normal(scale=std, size=x_t.shape)
    # Deterministic drift term
    drift = -mu * np.asarray(grad_potential(x_t)) * dt
    return drift + noise


def fokker_planck_rhs(p: np.ndarray,
                      x: np.ndarray,
                      mu: float,
                      potential: callable,
                      D: float) -> np.ndarray:
    """Compute the right–hand side of the Fokker–Planck equation for 1D.

    The Fokker–Planck equation describes the time evolution of the
    probability density ``p(x, t)`` associated with a stochastic process.
    For the overdamped Langevin dynamics defined above, the equation reads

    .. math::

       \partial_t p(x,t) = \nabla\cdot\big(\mu\,p\,\nabla V\big)
       + D\,\nabla^2 p.

    Here we implement a simple finite difference approximation on a
    regular grid ``x``.  Periodic boundary conditions are assumed.  In
    applications the user may wish to replace this with a more accurate
    solver (e.g. spectral methods or implicit schemes).

    Parameters
    ----------
    p : array_like
        Probability density on the grid ``x``.  Should sum to one when
        integrated over ``x``.
    x : array_like
        Grid points (1D) at which ``p`` is defined.  Assumed to be
        equally spaced.
    mu : float
        Mobility coefficient from the Langevin equation.
    potential : callable
        Function returning the potential ``V(x)`` at grid points.
    D : float
        Diffusion constant.

    Returns
    -------
    array_like
        Approximation to ``∂_t p`` evaluated on the same grid.
    """
    p = np.asarray(p)
    x = np.asarray(x)
    # grid spacing (assume uniform)
    dx = x[1] - x[0]
    # compute gradient of V on grid
    V = potential(x)
    # first derivative of p * ∂_x V (flux term)
    dVdx = np.gradient(V, dx, edge_order=2)
    flux = mu * p * dVdx
    dfluxdx = np.gradient(flux, dx, edge_order=2)
    # diffusion term
    lap_p = np.gradient(np.gradient(p, dx, edge_order=2), dx, edge_order=2)
    return dfluxdx + D * lap_p


def lindblad_master_equation(rho: np.ndarray,
                             H: np.ndarray,
                             Ls: list[np.ndarray],
                             gammas: list[float],
                             hbar: float = HBAR) -> np.ndarray:
    """Evaluate the Lindblad master equation for an open quantum system.

    The Lindblad equation governs the Markovian evolution of a density
    matrix ``rho`` subject to a Hamiltonian ``H`` and a set of Lindblad
    operators ``L_k`` with associated rates ``γ_k``.  In compact form,

    .. math::

       \dot\rho = -\tfrac{i}{\hbar}[H,\rho]
           + \sum_k \gamma_k \Big(L_k\rho L_k^\dagger
           - \tfrac12\{L_k^\dagger L_k,\rho\}\Big).

    This equation captures decoherence and dissipation processes.  In
    machine learning terms the dissipation channels can be interpreted
    as regularisation, and in the cognitive analogy they model habit
    formation or forgetting.

    Parameters
    ----------
    rho : array_like
        Density matrix of shape ``(n, n)``.  Should be Hermitian and
        positive semidefinite.
    H : array_like
        System Hamiltonian (``n × n`` Hermitian matrix).
    Ls : list of array_like
        Sequence of Lindblad jump operators ``L_k`` (each of shape
        ``(n, n)``).
    gammas : list of float
        Corresponding rates ``γ_k`` for each Lindblad operator.
    hbar : float, optional
        Reduced Planck constant.  Defaults to the module constant ``HBAR``.

    Returns
    -------
    array_like
        Time derivative ``dot_rho`` of the density matrix.
    """
    rho = np.asarray(rho, dtype=complex)
    H = np.asarray(H, dtype=complex)
    dim = rho.shape[0]
    # Coherent part
    commutator = H @ rho - rho @ H
    dot_rho = -1j / hbar * commutator
    # Dissipative part
    for L, gamma in zip(Ls, gammas):
        L = np.asarray(L, dtype=complex)
        # jump term
        jump = L @ rho @ L.conj().T
        # anticommutator term
        LdL = L.conj().T @ L
        anti = LdL @ rho + rho @ LdL
        dot_rho += gamma * (jump - 0.5 * anti)
    return dot_rho


def born_rule_update(rho: np.ndarray,
                     Ms: list[np.ndarray],
                     outcome: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Perform a generalized measurement (POVM) update on a density matrix.

    Given a set of measurement operators ``M_k`` (satisfying
    ``\sum_k M_k^\dagger M_k = I``), the probability of outcome ``k``
    when measuring the state ``rho`` is ``p(k) = Tr(M_k^\dagger M_k rho)``.
    If an ``outcome`` index is specified, the post–measurement state is
    updated according to

    .. math::

       \rho' = \frac{M_k\rho M_k^\dagger}{p(k)}.

    If ``outcome`` is ``None`` (default), the function returns the
    probability vector for all outcomes and leaves ``rho`` unchanged.

    Parameters
    ----------
    rho : array_like
        Density matrix of shape ``(n, n)``.
    Ms : list of array_like
        List of measurement operators ``M_k``.
    outcome : int or None, optional
        Index ``k`` specifying which outcome occurred.  If ``None``, no
        update is performed and only probabilities are returned.

    Returns
    -------
    tuple
        A tuple ``(probs, rho_updated)`` where ``probs`` is a 1D array of
        outcome probabilities and ``rho_updated`` is the post–measurement
        state (equal to ``rho`` if ``outcome`` is ``None``).
    """
    rho = np.asarray(rho, dtype=complex)
    # compute effects E_k = M_k^† M_k
    effects = [M.conj().T @ M for M in Ms]
    probs = np.array([np.real(np.trace(E @ rho)) for E in effects])
    if outcome is None:
        return probs, rho.copy()
    # update
    M_k = Ms[outcome]
    p_k = probs[outcome]
    if p_k <= 0:
        raise ValueError(f"Outcome {outcome} has zero probability.")
    rho_updated = M_k @ rho @ M_k.conj().T / p_k
    return probs, rho_updated


def entanglement_entropy(rho: np.ndarray) -> float:
    """Compute the von Neumann entropy of a density matrix.

    The von Neumann entropy

    .. math::

       S(\rho) = -\mathrm{Tr}(\rho \ln\rho)

    measures the degree of mixing or entanglement of the quantum state.
    In the context of the user's map it captures how integrated or
    segregated a sub‑experience is.  This function computes the entropy by
    diagonalising ``rho`` and summing over ``-p log p`` for the positive
    eigenvalues ``p``.  Zero eigenvalues contribute nothing.

    Parameters
    ----------
    rho : array_like
        Density matrix (Hermitian, positive semidefinite).  Need not be
        normalised; the entropy depends only on the eigenvalues up to
        normalisation.

    Returns
    -------
    float
        Von Neumann entropy ``S(rho)``.
    """
    rho = np.asarray(rho, dtype=complex)
    # ensure Hermitian by symmetrising
    rho = 0.5 * (rho + rho.conj().T)
    # compute eigenvalues
    eigvals = np.linalg.eigvalsh(rho)
    # filter small negative values due to numerical error
    eigvals = np.real(eigvals.clip(min=0))
    # normalise (trace may not be exactly one)
    total = eigvals.sum()
    if total > 0:
        eigvals = eigvals / total
    # compute entropy
    # use masked array to avoid log(0)
    mask = eigvals > 0
    return float(-np.sum(eigvals[mask] * np.log(eigvals[mask])))


def mutual_information(rho_AB: np.ndarray,
                       dims: tuple[int, int]) -> float:
    """Compute the mutual information ``I(A:B)`` of a bipartite state.

    For a bipartite density matrix ``rho_AB`` acting on ``H_A ⊗ H_B`` the
    mutual information is defined as

    .. math::

       I(A:B) = S(\rho_A) + S(\rho_B) - S(\rho_{AB}),

    where ``S`` denotes the von Neumann entropy and the partial traces
    produce the reduced states ``rho_A = Tr_B rho_AB`` and
    ``rho_B = Tr_A rho_AB``.  This quantity measures the total amount of
    correlation (classical and quantum) between the subsystems.  In the
    user's analogy it quantifies integration across entangled awareness
    streams.

    Parameters
    ----------
    rho_AB : array_like
        Density matrix of shape ``(n_A * n_B, n_A * n_B)``.
    dims : tuple of int
        Dimensions ``(n_A, n_B)`` of the two subsystems.

    Returns
    -------
    float
        Mutual information ``I(A:B)``.
    """
    rho_AB = np.asarray(rho_AB, dtype=complex)
    n_A, n_B = dims
    # total entropy
    S_AB = entanglement_entropy(rho_AB)
    # partial trace over B
    rho_A = np.zeros((n_A, n_A), dtype=complex)
    for i in range(n_B):
        idx = slice(i * n_A, (i + 1) * n_A)
        rho_A += rho_AB[idx, idx]
    S_A = entanglement_entropy(rho_A)
    # partial trace over A
    rho_B = np.zeros((n_B, n_B), dtype=complex)
    for i in range(n_A):
        idx = slice(i, n_A * n_B, n_A)
        rho_B += rho_AB[idx, :][:, idx]
    S_B = entanglement_entropy(rho_B)
    return S_A + S_B - S_AB


def natural_gradient(grad: ArrayLike,
                     fisher: np.ndarray,
                     eta: float = 1.0) -> np.ndarray:
    """Compute a natural gradient update direction.

    In information geometry the natural gradient modifies an ordinary
    gradient ``∇_θ L`` by the inverse Fisher information matrix ``F^{-1}``
    to account for curvature of the statistical manifold.  The natural
    gradient step is

    .. math::

       \Delta\theta = -\eta\,F^{-1}\nabla_\theta L.

    In the user's framework this corresponds to following the steepest
    descent in "belief space" when updating cognitive models.  This
    function solves the linear system ``F ⋅ Δθ = ∇_θ L`` using a stable
    solver.  If ``F`` is singular or ill‑conditioned a pseudoinverse is
    computed.

    Parameters
    ----------
    grad : array_like
        Gradient vector ``∇_θ L`` of shape ``(n,)``.
    fisher : array_like
        Fisher information matrix ``F`` of shape ``(n, n)``.
    eta : float, optional
        Learning rate or step size.  Default is ``1.0``.

    Returns
    -------
    ndarray
        Natural gradient update ``Δθ``.
    """
    grad = np.asarray(grad, dtype=float)
    fisher = np.asarray(fisher, dtype=float)
    # Solve F x = grad for x; use pseudoinverse if necessary
    try:
        delta = np.linalg.solve(fisher, grad)
    except np.linalg.LinAlgError:
        # use pseudoinverse for stability
        delta = np.linalg.pinv(fisher) @ grad
    return -eta * delta


def quantum_speed_limits(delta_E: float,
                         avg_E: float,
                         E0: float,
                         hbar: float = HBAR) -> float:
    """Compute lower bounds on the time required for a quantum evolution.

    Quantum speed limits provide fundamental bounds on how quickly a
    quantum state can evolve.  Two common expressions are

    .. math::

       \tau \ge \frac{\pi\hbar}{2 \Delta E}, \qquad
       \tau \ge \frac{\pi\hbar}{2 (\langle E\rangle - E_0)},

    where ``ΔE`` is the energy uncertainty (standard deviation) and
    ``⟨E⟩ - E_0`` is the average energy above the ground state.  In the
    consciousness analogy this sets a lower bound on how rapidly a
    cognitive state can genuinely change.  This function returns the
    maximum of the two bounds.

    Parameters
    ----------
    delta_E : float
        Energy uncertainty ``ΔE`` of the initial state.
    avg_E : float
        Expectation value ``⟨E⟩`` of the energy.
    E0 : float
        Ground state energy ``E_0`` (lowest eigenvalue of the Hamiltonian).
    hbar : float, optional
        Reduced Planck constant.

    Returns
    -------
    float
        Lower bound ``τ_min`` on the evolution time.
    """
    if delta_E <= 0 and avg_E <= E0:
        raise ValueError("At least one of delta_E or avg_E - E0 must be positive.")
    bound1 = np.pi * hbar / (2.0 * delta_E) if delta_E > 0 else 0.0
    energy_gap = avg_E - E0
    bound2 = np.pi * hbar / (2.0 * energy_gap) if energy_gap > 0 else 0.0
    return max(bound1, bound2)


def softmax_policy(q: ArrayLike,
                   beta: float = 1.0,
                   prior: ArrayLike | None = None) -> np.ndarray:
    """Compute a softmax policy from action values.

    Given a vector of state–action values ``Q`` and an inverse
    temperature ``β`` the softmax policy is defined by

    .. math::

       \pi(a) \propto \pi_0(a) \exp(β Q(a)),

    where ``π0`` is an optional prior distribution over actions.  In the
    user's framework the temperature ``1/β`` controls the exploration–
    exploitation tradeoff: high ``β`` makes the agent more decisive while
    low ``β`` introduces more randomness.

    Parameters
    ----------
    q : array_like
        Array of action values (higher is better).
    beta : float, optional
        Inverse temperature.  Default is ``1.0``.
    prior : array_like, optional
        Prior policy ``π0`` of the same shape as ``q``.  If ``None`` a
        uniform prior is assumed.

    Returns
    -------
    ndarray
        Normalised probability distribution over actions.
    """
    q = np.asarray(q, dtype=float)
    if prior is None:
        prior = np.ones_like(q) / len(q)
    else:
        prior = np.asarray(prior, dtype=float)
        prior = prior / np.sum(prior)
    # compute unnormalised logits
    logits = beta * q + np.log(prior)
    # subtract max for numerical stability
    logits = logits - np.max(logits)
    pi = np.exp(logits)
    return pi / np.sum(pi)


def bayesian_update(prior: ArrayLike,
                    likelihood: ArrayLike,
                    evidence: float | None = None) -> np.ndarray:
    """Perform a Bayesian update of a prior distribution.

    Given a prior distribution ``p(z)`` and a likelihood function
    ``p(x|z)`` proportional to the probability of observing data ``x``
    given latent variable ``z``, Bayes' rule yields the posterior

    .. math::

       p(z|x) = \frac{p(x|z) p(z)}{p(x)},

    where ``p(x) = Σ_z p(x|z) p(z)`` is the evidence.  In the user's
    framework this corresponds to updating beliefs on the basis of new
    evidence.  This function takes arrays proportional to the prior and
    likelihood and returns the normalised posterior.

    Parameters
    ----------
    prior : array_like
        Prior distribution ``p(z)`` (need not sum to one).
    likelihood : array_like
        Likelihood values ``p(x|z)`` (same shape as ``prior``).  Should
        be non‑negative.
    evidence : float or None, optional
        If provided, overrides the normalising constant.  Otherwise the
        evidence is computed as ``Σ_z p(z) p(x|z)``.

    Returns
    -------
    ndarray
        Normalised posterior distribution ``p(z|x)``.
    """
    prior = np.asarray(prior, dtype=float)
    likelihood = np.asarray(likelihood, dtype=float)
    unnorm = prior * likelihood
    if evidence is None:
        evidence = np.sum(unnorm)
    if evidence == 0:
        raise ValueError("Evidence is zero; cannot normalise posterior.")
    return unnorm / evidence


def free_energy(q: ArrayLike,
                p_joint: ArrayLike) -> float:
    """Compute the variational free energy ``F[q]`` for a given posterior ``q``.

    The variational free energy (negative evidence lower bound) is

    .. math::

       \mathcal{F}[q] = \mathbb{E}_q[\ln q(z) - \ln p(x,z)]
                     = \sum_z q(z) \big[\ln q(z) - \ln p(x,z)\big].

    Minimising this quantity with respect to ``q`` underpins a broad class
    of variational inference algorithms and, in the user's framework,
    represents the drive to reduce surprise.  The input ``p_joint``
    should contain values proportional to the joint distribution ``p(x,z)``
    (normalisation is irrelevant since it cancels in the expectation).

    Parameters
    ----------
    q : array_like
        Posterior distribution ``q(z)``.
    p_joint : array_like
        Values proportional to the joint distribution ``p(x,z)``.  Must
        have the same shape as ``q`` and contain strictly positive values.

    Returns
    -------
    float
        Variational free energy ``F[q]``.
    """
    q = np.asarray(q, dtype=float)
    p_joint = np.asarray(p_joint, dtype=float)
    # ensure normalisation of q
    q = q / np.sum(q)
    # avoid log(0) by clipping
    eps = 1e-12
    q_clipped = np.clip(q, eps, None)
    p_clipped = np.clip(p_joint, eps, None)
    return float(np.sum(q_clipped * (np.log(q_clipped) - np.log(p_clipped))))


def landauer_minimum_work(n_bits: int,
                          temperature: float,
                          k_b: float = K_B) -> float:
    """Compute Landauer's bound on the work to erase information.

    Landauer's principle states that erasing one bit of information at
    temperature ``T`` costs at least ``k_B T ln 2`` of work.  This
    function multiplies that basic unit by the number of bits to erase.

    Parameters
    ----------
    n_bits : int
        Number of bits erased.
    temperature : float
        Absolute temperature ``T`` in kelvin.
    k_b : float, optional
        Boltzmann constant.  Defaults to the module constant ``K_B``.

    Returns
    -------
    float
        Minimum work ``W_min`` required to erase ``n_bits`` bits at
        temperature ``T``.
    """
    return n_bits * k_b * temperature * np.log(2.0)


def jarzynski_average(works: ArrayLike,
                       beta: float) -> float:
    """Compute the Jarzynski estimator ``⟨e^{−β W}⟩``.

    The Jarzynski equality relates nonequilibrium work fluctuations to
    equilibrium free energy differences:

    .. math::

       \langle e^{-βW} \rangle = e^{-β \Delta F}.

    This function takes an array of work values ``W`` measured in
    identically prepared non‑equilibrium processes and a given inverse
    temperature ``β`` and returns the exponential average
    ``⟨e^{−βW}⟩``.  If many work samples are available, the natural
    logarithm of this quantity approximates ``−β ΔF``.  In the user's
    analogy this bound expresses the energetic cost of cognitive updates.

    Parameters
    ----------
    works : array_like
        Sequence of work values ``W``.
    beta : float
        Inverse temperature ``1/(k_B T)``; units must match those of ``W``.

    Returns
    -------
    float
        Exponential average ``⟨e^{−βW}⟩``.
    """
    works = np.asarray(works, dtype=float)
    return float(np.mean(np.exp(-beta * works)))


def lieb_robinson_bound(distance: float,
                        time: float,
                        c: float,
                        v: float,
                        xi: float) -> float:
    """Compute a Lieb–Robinson type bound for operator spreading.

    The Lieb–Robinson bound provides an upper limit on the speed at which
    information or correlations can propagate in a lattice system with
    short‑range interactions.  In one formulation the norm of the
    commutator of local observables at distance ``d`` apart at time ``t``
    is bounded by

    .. math::

       \|[A_x(t), B_y]\| \lesssim c\,\exp\Big[ -\frac{d - v t}{\xi} \Big],

    where ``v`` is the Lieb–Robinson velocity, ``ξ`` is a locality length
    scale and ``c`` is a model‑dependent constant.  In the user's map
    this bound expresses that there is a finite speed at which cognitive
    coordination can occur.  The function returns the bound value.

    Parameters
    ----------
    distance : float
        Distance ``d(x,y)`` between the two observables.
    time : float
        Evolution time ``t``.
    c : float
        Prefactor constant ``c``.
    v : float
        Lieb–Robinson velocity ``v`` (units of distance per unit time).
    xi : float
        Locality length scale ``ξ``.

    Returns
    -------
    float
        Upper bound on the operator norm ``||[A_x(t), B_y]||``.
    """
    argument = (distance - v * time) / xi
    return c * np.exp(-argument)


def bekenstein_entropy_bound(energy: float,
                             radius: float,
                             k_b: float = K_B,
                             hbar: float = HBAR,
                             c: float = C_LIGHT) -> float:
    """Compute the Bekenstein bound on the entropy of a system.

    The Bekenstein bound states that the entropy ``S`` of a system of
    energy ``E`` confined to a sphere of radius ``R`` satisfies

    .. math::

       S \le \frac{2\pi k_B E R}{\hbar c}.

    This inequality places a fundamental limit on the information content
    of any physical system.  In the user's framework it quantifies the
    ultimate memory capacity of a conscious computing substrate.  The
    function returns the right–hand side of this inequality.

    Parameters
    ----------
    energy : float
        Total energy ``E`` of the system.
    radius : float
        Effective radius ``R`` enclosing the system.
    k_b : float, optional
        Boltzmann constant.
    hbar : float, optional
        Reduced Planck constant.
    c : float, optional
        Speed of light.

    Returns
    -------
    float
        Upper bound on the entropy ``S`` in units of ``k_B`` (so the
        actual entropy is ``S / k_B`` dimensionless).
    """
    return 2 * np.pi * k_b * energy * radius / (hbar * c)


def renormalization_flow_step(g: ArrayLike,
                              beta_funcs: callable,
                              dl: float) -> np.ndarray:
    """Compute a single renormalisation group (RG) flow step for couplings.

    Renormalisation group equations describe how coupling constants
    ``g_i`` change as one varies the energy or length scale of a theory.
    They take the form

    .. math::

       \partial_\ell g_i = \beta_i(g_1, g_2, \ldots),

    where ``ℓ`` is the logarithm of the scale.  This function performs a
    simple Euler integration step of size ``dl`` using the provided
    beta–function callback ``beta_funcs``.  The callback should accept the
    current couplings ``g`` and return an array of ``β_i(g)``.  In the
    cognitive analogy these flows capture how concepts stabilise as
    one zooms out to coarser descriptions.

    Parameters
    ----------
    g : array_like
        Current values of the couplings.
    beta_funcs : callable
        Function ``β(g)`` returning the flow derivatives of the couplings.
    dl : float
        Increment in RG "time" (logarithmic scale parameter).  A small
        positive value corresponds to integrating towards larger length
        scales; a negative value integrates towards smaller scales.

    Returns
    -------
    ndarray
        Updated couplings ``g + dl * β(g)``.
    """
    g = np.asarray(g, dtype=float)
    beta = np.asarray(beta_funcs(g), dtype=float)
    return g + dl * beta
