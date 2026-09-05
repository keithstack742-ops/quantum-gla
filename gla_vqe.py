"""Geometric Landscape Anchoring (GLA) VQE Implementation

Reference implementation for GLA framework using PennyLane.
Demonstrates identity initialization, local cost functions, and adaptive QFIM monitoring.
Also provides a production-grade GLA engine for 2D Fermi-Hubbard lattices.
"""

import pennylane as qml
from pennylane import numpy as np
import numpy as np_orig
from typing import Tuple, List, Optional, Union

def build_hubbard_hamiltonian(Lx: int, Ly: int, t: float, U: float) -> qml.Hamiltonian:
    """Constructs the 2D Fermi-Hubbard Hamiltonian on a Lx x Ly grid.

    Qubits 0 to N_s - 1 map to spin-up electrons.
    Qubits N_s to 2*N_s - 1 map to spin-down electrons.
    where N_s = Lx * Ly is the number of spatial lattice sites.

    Args:
        Lx: Grid width
        Ly: Grid height
        t: Hopping parameter
        U: Coulomb interaction strength

    Returns:
        pennylane.Hamiltonian representing the physical system.
    """
    n_sites = Lx * Ly
    n_qubits = 2 * n_sites

    # Identify nearest neighbors
    neighbors = []
    for y in range(Ly):
        for x in range(Lx):
            idx = y * Lx + x
            # Horizontal neighbor
            if x + 1 < Lx:
                neighbors.append((idx, y * Lx + (x + 1)))
            # Vertical neighbor
            if y + 1 < Ly:
                neighbors.append((idx, (y + 1) * Lx + x))

    coeffs = []
    obs = []

    # Constant term tracker for U/4 * I per site
    constant_energy = (U / 4.0) * n_sites
    coeffs.append(constant_energy)
    obs.append(qml.Identity(0))

    # 1. Hopping terms for spin-up and spin-down
    for u, v in neighbors:
        for spin in [0, 1]:
            p = u + spin * n_sites
            q = v + spin * n_sites

            # Ensure p < q
            if p > q:
                p, q = q, p

            # Jordan-Wigner hopping:
            # -t/2 * (X_p Z_{p+1}...Z_{q-1} X_q + Y_p Z_{p+1}...Z_{q-1} Y_q)
            z_string_wires = list(range(p + 1, q))

            if len(z_string_wires) == 0:
                op1 = qml.PauliX(p) @ qml.PauliX(q)
                op2 = qml.PauliY(p) @ qml.PauliY(q)
            else:
                z_op = qml.PauliZ(z_string_wires[0])
                for w in z_string_wires[1:]:
                    z_op = z_op @ qml.PauliZ(w)
                op1 = qml.PauliX(p) @ z_op @ qml.PauliX(q)
                op2 = qml.PauliY(p) @ z_op @ qml.PauliY(q)

            coeffs.append(-t / 2.0)
            obs.append(op1)
            coeffs.append(-t / 2.0)
            obs.append(op2)

    # 2. On-site interaction terms: U * n_{i,up} * n_{i,down}
    # n_{i,up} = (I - Z_i)/2, n_{i,down} = (I - Z_{i + n_sites})/2
    # So U * n_{i,up} * n_{i,down} = U/4 * (I - Z_i - Z_{i+n_sites} + Z_i * Z_{i+n_sites})
    for i in range(n_sites):
        # -U/4 * Z_i
        coeffs.append(-U / 4.0)
        obs.append(qml.PauliZ(i))

        # -U/4 * Z_{i+n_sites}
        coeffs.append(-U / 4.0)
        obs.append(qml.PauliZ(i + n_sites))

        # U/4 * Z_i * Z_{i+n_sites}
        coeffs.append(U / 4.0)
        obs.append(qml.PauliZ(i) @ qml.PauliZ(i + n_sites))

    return qml.Hamiltonian(coeffs, obs)


def symmetry_preserving_layer(
    params: np.ndarray,
    Lx: int,
    Ly: int,
    n_sites: int,
    fswap_angle: float = np.pi
):
    """Applies a single layer of the Symmetry-Preserving Ansatz.

    This contains:
    - XY-type hopping gates (using qml.IsingXY) to simulate fermion movement
    - ZZ-type interaction gates (using qml.IsingZZ or rotation) for on-site repulsion
    - Fermionic SWAP (qml.FermionicSWAP) gates to manage 2D topology

    Args:
        params: Array of parameters for this layer.
                Format: [hopping_params_up, hopping_params_down, interaction_params]
        Lx: Grid width
        Ly: Grid height
        n_sites: Number of spatial sites (Lx * Ly)
        fswap_angle: Rotation parameter for Fermionic SWAP
    """
    # Parameters breakdown:
    # We have up and down hopping channels.
    # In a 2D grid, horizontal and vertical bonds can be hopping.
    # Let's collect all horizontal and vertical neighbors
    neighbors = []
    for y in range(Ly):
        for x in range(Lx):
            idx = y * Lx + x
            if x + 1 < Lx:
                neighbors.append((idx, y * Lx + (x + 1)))
            if y + 1 < Ly:
                neighbors.append((idx, (y + 1) * Lx + x))

    n_bonds = len(neighbors)

    # 1. Hopping gates (XY-type)
    # Spin-up hopping
    for b_idx, (u, v) in enumerate(neighbors):
        phi_hop = params[b_idx]
        qml.IsingXY(phi_hop, wires=[u, v])

    # Spin-down hopping
    for b_idx, (u, v) in enumerate(neighbors):
        phi_hop = params[n_bonds + b_idx]
        qml.IsingXY(phi_hop, wires=[u + n_sites, v + n_sites])

    # 2. Interleave Fermionic SWAPs to manage 2D topology
    # This prevents long-range Jordan-Wigner strings.
    # For a simple demo, we apply fSWAP on the grid cross-bonds or vertical links.
    for u, v in neighbors:
        # Avoid simple horizontal self-swaps, we can do fSWAPs on vertical transitions
        # if vertical coordinate difference is 1
        if abs(u - v) == Lx:
            qml.FermionicSWAP(fswap_angle, wires=[u, v])
            qml.FermionicSWAP(fswap_angle, wires=[u + n_sites, v + n_sites])

    # 3. On-site interaction gates: IsingZZ between spin-up and spin-down
    for i in range(n_sites):
        gamma = params[2 * n_bonds + i]
        qml.IsingZZ(gamma, wires=[i, i + n_sites])


def prepare_neel_state(n_sites: int):
    """Prepares the antiferromagnetic Néel state on the spatial lattice.

    The Néel state alternatingly populates spin-up and spin-down sites:
    |1010...⟩ for spin-up, and |0101...⟩ for spin-down.
    This corresponds to total particle number N = n_sites, and Sz = 0 conservation.

    Args:
        n_sites: Number of spatial sites
    """
    for i in range(n_sites):
        if i % 2 == 0:
            # Populated in spin-up
            qml.PauliX(i)
        else:
            # Populated in spin-down
            qml.PauliX(i + n_sites)


def compute_von_neumann_entropy(state_vector: np.ndarray, system_wires: List[int], total_qubits: int) -> float:
    """Computes the von Neumann entropy for a subset of wires from the state vector.

    Args:
        state_vector: Full 2^total_qubits state vector.
        system_wires: Subsystem wires to measure entanglement of.
        total_qubits: Total number of qubits in system.

    Returns:
        The von Neumann entropy value.
    """
    # Reshape the state vector to partition subsystem A (system_wires) and B (rest)
    num_subsystem = len(system_wires)
    num_rest = total_qubits - num_subsystem

    # Map wires to indices
    # Convert state_vector to a standard numpy matrix if necessary
    state_tensor = np_orig.reshape(np_orig.array(state_vector), [2] * total_qubits)

    # Transpose to put system_wires first
    all_axes = list(range(total_qubits))
    rest_wires = [w for w in all_axes if w not in system_wires]
    transposed_tensor = np_orig.transpose(state_tensor, system_wires + rest_wires)

    # Flatten subsystem and rest dimensions to form a matrix
    matrix_form = np_orig.reshape(transposed_tensor, (2**num_subsystem, 2**num_rest))

    # Compute reduced density matrix rho_A = matrix_form @ matrix_form^H
    rho_A = matrix_form @ np_orig.conj(matrix_form).T

    # Diagonalize rho_A
    eigenvals = np_orig.linalg.eigvalsh(rho_A)

    # Entropy sum_i -p_i log(p_i)
    entropy = 0.0
    for p in eigenvals:
        if p > 1e-12:
            entropy -= p * np_orig.log(p)

    return float(entropy)


def compute_falsifiability_metrics(
    state_vector: np.ndarray,
    n_qubits: int,
    anchor_state: np.ndarray,
    seed: Optional[int] = None
) -> Tuple[float, float]:
    """Estimates the dual-distance falsifiability metrics D_anchor and D_Haar.

    D_anchor: Distance of optimized state from physical anchor state (Néel).
              Must be non-vanishing to prove the state moves away from anchor bias.
    D_Haar: Distance of optimized state from high-entropy Haar-random states.
            Must be non-vanishing to show the state does not collapse into high-entropy voids.

    The distances are defined on the density operator level using trace/Frobenius norms.

    Args:
        state_vector: State vector of current state
        n_qubits: Number of qubits in system
        anchor_state: State vector of the anchor state (Néel)
        seed: Random seed for mock Haar generation

    Returns:
        (D_anchor, D_Haar) trace/Frobenius distance metrics.
    """
    if seed is not None:
        np_orig.random.seed(seed)

    # Density matrix representing optimized state
    rho = np_orig.outer(state_vector, np_orig.conj(state_vector))

    # Density matrix representing anchor state
    rho_anchor = np_orig.outer(anchor_state, np_orig.conj(anchor_state))

    # Generate a dummy Haar state matrix representing random void
    # For a genuine Haar-random state vector, we draw from standard normal distribution
    random_real = np_orig.random.normal(0, 1, 2**n_qubits)
    random_imag = np_orig.random.normal(0, 1, 2**n_qubits)
    haar_state = random_real + 1j * random_imag
    haar_state /= np_orig.linalg.norm(haar_state)
    rho_haar = np_orig.outer(haar_state, np_orig.conj(haar_state))

    # Frobenius distance metrics: ||rho1 - rho2||_F
    D_anchor = float(np_orig.linalg.norm(rho - rho_anchor, 'fro'))
    D_Haar = float(np_orig.linalg.norm(rho - rho_haar, 'fro'))

    return D_anchor, D_Haar


class GLA_VQE:
    """Geometric Landscape Anchoring VQE Solver"""
    
    def __init__(
        self,
        n_qubits: int,
        n_layers: int,
        init_sigma: float = None,
        device_name: str = "default.qubit",
        verbose: bool = True
    ):
        """Initialize GLA VQE solver.
        
        Args:
            n_qubits: Number of qubits
            n_layers: Number of circuit layers
            init_sigma: Perturbation scale for identity initialization.
                       If None, defaults to 1.0 / (n_qubits ** 2)
            device_name: PennyLane device name
            verbose: Print optimization progress
        """
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.init_sigma = init_sigma or 1.0 / (n_qubits ** 2)
        self.device_name = device_name
        self.verbose = verbose
        
        # Create device
        self.dev = qml.device(device_name, wires=n_qubits)
        
        # Hamiltonian definition (2D TFIM for demo)
        self._setup_hamiltonian()
        
    def _setup_hamiltonian(self):
        """Setup Transverse Field Ising Model (TFIM) Hamiltonian."""
        coeffs = []
        obs = []
        
        # Nearest-neighbor ZZ interactions
        for i in range(self.n_qubits - 1):
            coeffs.append(-1.0)
            obs.append(qml.PauliZ(i) @ qml.PauliZ(i + 1))
        
        # Transverse field X terms
        for i in range(self.n_qubits):
            coeffs.append(-0.5)
            obs.append(qml.PauliX(i))
        
        self.hamiltonian = qml.Hamiltonian(coeffs, obs)
        
    def ansatz(self, params: np.ndarray):
        """GLA Ansatz: RY-RZ rotations + staggered CNOT entanglement.
        
        Args:
            params: Shape (n_layers, n_qubits, 2)
        """
        for l in range(self.n_layers):
            # Single-qubit rotations
            for i in range(self.n_qubits):
                qml.RY(params[l, i, 0], wires=i)
                qml.RZ(params[l, i, 1], wires=i)
            
            # Even layer: even-indexed CNOTs
            for i in range(0, self.n_qubits - 1, 2):
                qml.CNOT(wires=[i, i + 1])
            
            # Odd layer: odd-indexed CNOTs
            for i in range(1, self.n_qubits - 1, 2):
                qml.CNOT(wires=[i, i + 1])
    
    def cost_function(self, params: np.ndarray) -> float:
        """Compute cost (energy expectation value).
        
        Args:
            params: Circuit parameters
            
        Returns:
            Energy expectation value
        """
        @qml.qnode(self.dev)
        def _cost(p):
            self.ansatz(p)
            return qml.expval(self.hamiltonian)
        
        return _cost(params)
    
    def compute_gradient_variance(
        self,
        params: np.ndarray,
        n_samples: int = 5
    ) -> float:
        """Estimate gradient variance via finite sampling.
        
        Args:
            params: Circuit parameters
            n_samples: Number of random parameter shifts
            
        Returns:
            Estimated gradient variance
        """
        from pennylane import numpy as pnp
        grad_fn = qml.grad(self.cost_function)
        gradients = []
        
        for _ in range(n_samples):
            # Random perturbation
            delta = np_orig.random.normal(0, 0.01, params.shape)
            params_input = pnp.array(params + delta, requires_grad=True)
            g = np_orig.linalg.norm(grad_fn(params_input))
            gradients.append(g)
        
        return float(np_orig.var(gradients))
    
    def compute_qfim_spectrum(
        self,
        params: np.ndarray,
        eps: float = 1e-5
    ) -> Tuple[float, np_orig.ndarray]:
        """Compute QFIM spectrum and stability metric.
        
        Args:
            params: Circuit parameters
            eps: Finite-difference step size
            
        Returns:
            (stability_metric, eigenvalues)
        """
        from pennylane import numpy as pnp
        grad_fn = qml.grad(self.cost_function)
        p_flat = params.flatten()
        n_params = len(p_flat)
        
        # Compute Jacobian (gradient for each parameter)
        jacobian = np_orig.zeros((n_params, n_params))
        for i in range(n_params):
            params_pert = p_flat.copy()
            params_pert[i] += eps
            params_input = pnp.array(params_pert.reshape(params.shape), requires_grad=True)
            g = grad_fn(params_input)
            jacobian[i] = g.flatten()
        
        # QFIM = J^T J
        qfim = jacobian.T @ jacobian
        eigenvalues = np_orig.linalg.eigvalsh(qfim)
        
        # Stability metric
        lambda_min = np_orig.max([eigenvalues[0], 1e-12])  # Avoid log(0)
        lambda_max = np_orig.max([eigenvalues[-1], 1e-12])
        stability = lambda_min / lambda_max
        
        return stability, eigenvalues
    
    def optimize(
        self,
        steps: int = 100,
        learning_rate: float = 0.05,
        adaptive_anchoring: bool = True,
        stability_threshold: float = 0.01,
        monitor_interval: int = 10
    ) -> Tuple[List[float], np.ndarray]:
        """Run GLA VQE optimization.
        
        Args:
            steps: Number of optimization steps
            learning_rate: Adam optimizer learning rate
            adaptive_anchoring: Enable QFIM-based re-centering
            stability_threshold: Re-center if S(θ) < threshold
            monitor_interval: Monitor QFIM every N steps
            
        Returns:
            (energy_history, final_params)
        """
        # Initialize parameters: identity + perturbation
        params = np.random.normal(
            0, self.init_sigma, (self.n_layers, self.n_qubits, 2),
            requires_grad=True
        )
        
        opt = qml.AdamOptimizer(stepsize=learning_rate)
        energy_history = []
        
        if self.verbose:
            print(f"Starting GLA VQE: {self.n_qubits} qubits, {self.n_layers} layers")
            print(f"Initial sigma: {self.init_sigma:.2e}")
            print("-" * 80)
        
        for step in range(steps):
            # Optimization step
            params, energy = opt.step_and_cost(self.cost_function, params)
            energy_history.append(energy)
            
            # Monitoring and adaptive re-centering
            if adaptive_anchoring and step % monitor_interval == 0:
                stability, eigenvalues = self.compute_qfim_spectrum(params)
                
                if self.verbose:
                    grad_fn = qml.grad(self.cost_function)
                    grad_norm = np_orig.linalg.norm(grad_fn(params))
                    print(f"Step {step:4d} | Energy: {energy:10.6f} | "
                          f"Grad Norm: {grad_norm:.4e} | Stability: {stability:.4e}")
                
                # Re-center if stability degrades
                if stability < stability_threshold:
                    if self.verbose:
                        print(f"  → Re-centering (S={stability:.4e} < {stability_threshold})")
                    
                    alpha = 0.3
                    sigma_recenter = 0.01
                    params = ((1 - alpha) * params + 
                             np.random.normal(0, sigma_recenter, params.shape,
                                            requires_grad=True))
            
            elif self.verbose and step % monitor_interval == 0:
                grad_fn = qml.grad(self.cost_function)
                grad_norm = np_orig.linalg.norm(grad_fn(params))
                print(f"Step {step:4d} | Energy: {energy:10.6f} | Grad Norm: {grad_norm:.4e}")
        
        if self.verbose:
            print("-" * 80)
            print(f"Optimization complete. Final Energy: {energy_history[-1]:.6f}")
        
        return energy_history, params


def run_gla_vqe(
    n_qubits: int,
    n_layers: int,
    steps: int = 100,
    init_sigma: Optional[float] = None,
    adaptive_anchoring: bool = True,
    verbose: bool = True
) -> Tuple[List[float], np.ndarray]:
    """Convenience function to run GLA VQE."""
    solver = GLA_VQE(
        n_qubits=n_qubits,
        n_layers=n_layers,
        init_sigma=init_sigma,
        verbose=verbose
    )
    return solver.optimize(steps=steps, adaptive_anchoring=adaptive_anchoring)


class GLAProductionEngine:
    """Production-grade Geometric Landscape Anchoring (GLA) engine for 2D Fermi-Hubbard lattice simulation."""

    def __init__(
        self,
        Lx: int,
        Ly: int,
        t: float = 1.0,
        U: float = 4.0,
        n_layers: int = 3,
        init_sigma: Optional[float] = None,
        stability_threshold: float = 0.01,
        verbose: bool = True
    ):
        self.Lx = Lx
        self.Ly = Ly
        self.n_sites = Lx * Ly
        self.n_qubits = 2 * self.n_sites
        self.t = t
        self.U = U
        self.n_layers = n_layers
        self.init_sigma = init_sigma or (1.0 / (self.n_qubits ** 2))
        self.stability_threshold = stability_threshold
        self.verbose = verbose

        # Instantiate device
        self.dev = qml.device("default.qubit", wires=self.n_qubits)

        # Build Hamiltonian
        self.hamiltonian = build_hubbard_hamiltonian(Lx, Ly, t, U)

        # Count parameter shape per layer:
        # up_hopping bonds + down_hopping bonds + interaction terms
        # bonds count is calculated in symmetry_preserving_layer
        neighbors = []
        for y in range(Ly):
            for x in range(Lx):
                idx = y * Lx + x
                if x + 1 < Lx:
                    neighbors.append((idx, y * Lx + (x + 1)))
                if y + 1 < Ly:
                    neighbors.append((idx, (y + 1) * Lx + x))

        self.n_bonds = len(neighbors)
        # Total parameters per layer: spin_up_hopping (n_bonds) + spin_down_hopping (n_bonds) + interaction (n_sites)
        self.n_params_per_layer = 2 * self.n_bonds + self.n_sites
        self.params_shape = (self.n_layers, self.n_params_per_layer)

    def ansatz(self, params: np.ndarray):
        """Prepares the physical Néel state anchor and applies symmetry-preserving layers."""
        prepare_neel_state(self.n_sites)
        for l in range(self.n_layers):
            symmetry_preserving_layer(params[l], self.Lx, self.Ly, self.n_sites)

    def cost_function(self, params: np.ndarray) -> float:
        """Expectation value of Fermi-Hubbard Hamiltonian."""
        @qml.qnode(self.dev)
        def _cost(p):
            self.ansatz(p)
            return qml.expval(self.hamiltonian)
        return _cost(params)

    def get_state_vector(self, params: np.ndarray) -> np.ndarray:
        """Retrieves full state vector representation from the device."""
        @qml.qnode(self.dev)
        def _state(p):
            self.ansatz(p)
            return qml.state()
        return _state(params)

    def compute_gradient_variance(self, params: np.ndarray, n_samples: int = 5) -> float:
        """Estimates the gradient variance near current parameter point."""
        grad_fn = qml.grad(self.cost_function)
        gradients = []
        for _ in range(n_samples):
            delta = np_orig.random.normal(0, 0.01, params.shape)
            g = np_orig.linalg.norm(grad_fn(params + delta))
            gradients.append(g)
        return float(np_orig.var(gradients))

    def compute_qfim_stability(self, params: np.ndarray, eps: float = 1e-5) -> float:
        """Computes current QFIM spectrum and stability metric lambda_min/lambda_max."""
        grad_fn = qml.grad(self.cost_function)
        p_flat = params.flatten()
        n_params = len(p_flat)

        jacobian = np_orig.zeros((n_params, n_params))
        for i in range(n_params):
            params_pert = p_flat.copy()
            params_pert[i] += eps
            g = grad_fn(params_pert.reshape(params.shape))
            jacobian[i] = g.flatten()

        qfim = jacobian.T @ jacobian
        eigenvalues = np_orig.linalg.eigvalsh(qfim)

        lambda_min = np_orig.max([eigenvalues[0], 1e-12])
        lambda_max = np_orig.max([eigenvalues[-1], 1e-12])
        return float(lambda_min / lambda_max)
    
    def run_production_vqe(
        self,
        steps: int = 100,
        learning_rate: float = 0.05,
        target_energy: Optional[float] = None
    ) -> Tuple[List[float], np.ndarray, List[float], List[Tuple[float, float]]]:
        """Runs optimization tracking dual-distance falsifiability and entropy-stabilized adaptive re-centering.

        Args:
            steps: Number of iterations
            learning_rate: Gradient descent step size
            target_energy: Optional ground-state target energy for monitoring

        Returns:
            (energy_history, final_params, entropy_history, falsifiability_history)
        """
        # Identity-biased initialization
        params = np.random.normal(0, self.init_sigma, self.params_shape, requires_grad=True)

        # Form Néel state anchor vector on standard Hilbert space
        # Spin up has even occupied, spin down has odd + n_sites occupied
        anchor_vector = np_orig.zeros(2**self.n_qubits, dtype=complex)
        neel_index = 0
        for i in range(self.n_sites):
            if i % 2 == 0:
                neel_index |= (1 << (self.n_qubits - 1 - i))
            else:
                neel_index |= (1 << (self.n_qubits - 1 - (i + self.n_sites)))
        anchor_vector[neel_index] = 1.0

        opt = qml.AdamOptimizer(stepsize=learning_rate)

        energy_history = []
        entropy_history = []
        falsifiability_history = []

        if self.verbose:
            print(f"\n================ GLA Production Engine Running ================")
            print(f"Lattice Size: {self.Lx}x{self.Ly} | Total Qubits: {self.n_qubits}")
            print(f"Hopping t: {self.t} | Coulomb interaction U: {self.U}")
            print(f"Parameters shape: {self.params_shape}")
            print("================================================================\n")

        for step in range(steps):
            params, energy = opt.step_and_cost(self.cost_function, params)
            energy_history.append(energy)

            # Fetch full state vector
            state_vector = self.get_state_vector(params)

            # Compute von Neumann entropy of spin-up subsystem
            entropy = compute_von_neumann_entropy(state_vector, list(range(self.n_sites)), self.n_qubits)
            entropy_history.append(entropy)

            # Dual-distance metrics
            D_anchor, D_Haar = compute_falsifiability_metrics(state_vector, self.n_qubits, anchor_vector)
            falsifiability_history.append((D_anchor, D_Haar))

            # QFIM Stability
            if step % 10 == 0 or step == steps - 1:
                qfim_stability = self.compute_qfim_stability(params)

                # Total stability metric S_total(theta) = S(theta) * exp( - (S(psi) - S_target) / S_max )
                # S_target = 0.5, S_max = 2.0
                S_total = qfim_stability * np_orig.exp(-max(0.0, entropy - 0.5) / 2.0)

                if self.verbose:
                    grad_fn = qml.grad(self.cost_function)
                    grad_norm = np_orig.linalg.norm(grad_fn(params))
                    print(f"Step {step:3d} | Energy: {energy:.6f} | Ent. Entropy: {entropy:.4f} | "
                          f"S_total: {S_total:.3e} | D_anchor: {D_anchor:.3f} | D_Haar: {D_Haar:.3f}")

                # Re-centering triggered if S_total < threshold
                if S_total < self.stability_threshold:
                    if self.verbose:
                        print(f"  → S_total {S_total:.3e} < threshold {self.stability_threshold} | Re-centering Trajectory!")
                    # Shift origin and re-anchor parameters
                    alpha = 0.3
                    params = ((1 - alpha) * params + np.random.normal(0, 0.01, params.shape, requires_grad=True))

        return energy_history, params, entropy_history, falsifiability_history


def run_gla_production(
    Lx: int,
    Ly: int,
    t: float = 1.0,
    U: float = 4.0,
    n_layers: int = 3,
    steps: int = 50,
    learning_rate: float = 0.05
):
    """Wrapper function to run the full GLA VQE Production pipeline."""
    engine = GLAProductionEngine(
        Lx=Lx,
        Ly=Ly,
        t=t,
        U=U,
        n_layers=n_layers,
        verbose=True
    )
    return engine.run_production_vqe(steps=steps, learning_rate=learning_rate)


if __name__ == "__main__":
    # Standard TFIM simulation for backwards compatibility
    print("Running TFIM simulation...")
    energies, params = run_gla_vqe(
        n_qubits=8,
        n_layers=4,
        steps=50,
        adaptive_anchoring=True
    )
    print(f"Final TFIM Energy: {energies[-1]:.6f}")
    
    # 2D Hubbard Production Engine Run (2x2 grid = 8 qubits)
    print("\nRunning Production 2D Hubbard simulation...")
    run_gla_production(Lx=2, Ly=2, steps=30)
