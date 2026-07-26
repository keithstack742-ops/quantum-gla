"""Geometric Landscape Anchoring (GLA) VQE Implementation

Reference implementation for GLA framework using PennyLane.
Demonstrates identity initialization, local cost functions, and adaptive QFIM monitoring.
"""

import pennylane as qml
from pennylane import numpy as np
import numpy as np_orig
from typing import Tuple, List, Optional


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
        grad_fn = qml.grad(self.cost_function)
        gradients = []
        
        for _ in range(n_samples):
            # Random perturbation
            delta = np_orig.random.normal(0, 0.01, params.shape)
            g = np_orig.linalg.norm(grad_fn(params + delta))
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
        grad_fn = qml.grad(self.cost_function)
        p_flat = params.flatten()
        n_params = len(p_flat)
        
        # Compute Jacobian (gradient for each parameter)
        jacobian = np_orig.zeros((n_params, n_params))
        for i in range(n_params):
            params_pert = p_flat.copy()
            params_pert[i] += eps
            g = grad_fn(params_pert.reshape(params.shape))
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
    """Convenience function to run GLA VQE.
    
    Args:
        n_qubits: Number of qubits
        n_layers: Number of ansatz layers
        steps: Optimization steps
        init_sigma: Perturbation scale (default: 1/n_qubits^2)
        adaptive_anchoring: Enable adaptive re-centering
        verbose: Print progress
        
    Returns:
        (energy_history, final_params)
    """
    solver = GLA_VQE(
        n_qubits=n_qubits,
        n_layers=n_layers,
        init_sigma=init_sigma,
        verbose=verbose
    )
    
    return solver.optimize(
        steps=steps,
        adaptive_anchoring=adaptive_anchoring
    )


if __name__ == "__main__":
    # Example: 2×2 Hubbard lattice (8 qubits)
    energies, params = run_gla_vqe(
        n_qubits=8,
        n_layers=4,
        steps=100,
        adaptive_anchoring=True
    )
    
    print(f"\nFinal Results:")
    print(f"  Final Energy: {energies[-1]:.6f}")
    print(f"  Energy improvement: {energies[0] - energies[-1]:.6f}")
    print(f"  Total iterations: {len(energies)}")