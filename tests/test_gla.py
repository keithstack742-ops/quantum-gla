import pytest
import numpy as np
from gla_vqe import GLA_VQE, run_gla_vqe


def test_gla_vqe_initialization():
    """Test the initialization of the GLA_VQE solver."""
    n_qubits = 4
    n_layers = 2
    solver = GLA_VQE(n_qubits=n_qubits, n_layers=n_layers)

    assert solver.n_qubits == n_qubits
    assert solver.n_layers == n_layers
    assert solver.init_sigma == 1.0 / (n_qubits ** 2)
    assert solver.hamiltonian is not None


def test_gla_vqe_initialization_custom_sigma():
    """Test custom init_sigma in initialization."""
    n_qubits = 6
    n_layers = 3
    init_sigma = 0.5
    solver = GLA_VQE(n_qubits=n_qubits, n_layers=n_layers, init_sigma=init_sigma)

    assert solver.init_sigma == init_sigma


def test_cost_function():
    """Test cost_function calculation and output type."""
    n_qubits = 4
    n_layers = 2
    solver = GLA_VQE(n_qubits=n_qubits, n_layers=n_layers, verbose=False)

    # Initialize parameters to zeros
    params = np.zeros((n_layers, n_qubits, 2))
    cost = solver.cost_function(params)

    assert isinstance(cost, (float, np.ndarray))
    # Energy should be a float value
    assert not np.isnan(cost)


def test_compute_gradient_variance():
    """Test that gradient variance computation returns a valid float."""
    n_qubits = 4
    n_layers = 2
    solver = GLA_VQE(n_qubits=n_qubits, n_layers=n_layers, verbose=False)
    params = np.zeros((n_layers, n_qubits, 2))

    variance = solver.compute_gradient_variance(params, n_samples=3)

    assert isinstance(variance, float)
    assert variance >= 0.0


def test_compute_qfim_spectrum():
    """Test QFIM spectrum and stability metric computation."""
    n_qubits = 4
    n_layers = 2
    solver = GLA_VQE(n_qubits=n_qubits, n_layers=n_layers, verbose=False)
    params = np.zeros((n_layers, n_qubits, 2))

    stability, eigenvalues = solver.compute_qfim_spectrum(params)

    assert isinstance(stability, float)
    assert stability > 0.0
    assert len(eigenvalues) == n_layers * n_qubits * 2
    # Allow for extremely small negative eigenvalues due to numerical precision
    assert np.all(eigenvalues >= -1e-12)


def test_optimize_without_anchoring():
    """Test optimization loop without adaptive anchoring."""
    n_qubits = 4
    n_layers = 2
    solver = GLA_VQE(n_qubits=n_qubits, n_layers=n_layers, verbose=False)

    steps = 5
    energies, final_params = solver.optimize(steps=steps, adaptive_anchoring=False)

    assert len(energies) == steps
    assert final_params.shape == (n_layers, n_qubits, 2)
    # Energy should generally decrease or stay stable
    assert energies[-1] <= energies[0] + 1e-5


def test_optimize_with_anchoring():
    """Test optimization loop with adaptive anchoring."""
    n_qubits = 4
    n_layers = 2
    solver = GLA_VQE(n_qubits=n_qubits, n_layers=n_layers, verbose=False)

    steps = 5
    # Force re-centering by setting high stability threshold
    energies, final_params = solver.optimize(
        steps=steps,
        adaptive_anchoring=True,
        stability_threshold=1.1,  # stability metric <= 1.0, so this triggers re-centering
        monitor_interval=2
    )

    assert len(energies) == steps
    assert final_params.shape == (n_layers, n_qubits, 2)


def test_run_gla_vqe_convenience():
    """Test the high-level convenience function run_gla_vqe."""
    energies, final_params = run_gla_vqe(
        n_qubits=4,
        n_layers=2,
        steps=5,
        adaptive_anchoring=True,
        verbose=False
    )

    assert len(energies) == 5
    assert final_params.shape == (2, 4, 2)
