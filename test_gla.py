"""Unit tests for Geometric Landscape Anchoring (GLA) VQE and Production Engine."""

import unittest
import numpy as np
import pennylane as qml
from gla_vqe import (
    build_hubbard_hamiltonian,
    prepare_neel_state,
    compute_von_neumann_entropy,
    compute_falsifiability_metrics,
    GLA_VQE,
    GLAProductionEngine
)

class TestGLAFramework(unittest.TestCase):
    """Test suite for the GLA VQE classes, methods, and helpers."""

    def test_hubbard_hamiltonian_symmetry(self):
        """Test that the 2D Fermi-Hubbard Hamiltonian has correct dimensions and structure."""
        Lx, Ly = 2, 2
        # Lx x Ly grid with up/down spins gives 2 * Lx * Ly = 8 qubits
        H = build_hubbard_hamiltonian(Lx, Ly, t=1.0, U=4.0)
        self.assertIsInstance(H, qml.Hamiltonian)
        self.assertEqual(len(H.wires), 8)

    def test_neel_state_preparation(self):
        """Test that the Néel state preparation applies PauliX on correct qubits."""
        n_sites = 4
        dev = qml.device("default.qubit", wires=2 * n_sites)

        @qml.qnode(dev)
        def circuit():
            prepare_neel_state(n_sites)
            return qml.state()

        state = circuit()
        # Non-zero index should be 0b10100101 (since 0, 2 are spin-up, 1+4, 3+4 are spin-down)
        # 10100101 binary is 165
        self.assertAlmostEqual(abs(state[165]), 1.0)

    def test_von_neumann_entropy(self):
        """Test the computation of subsystem entanglement entropy."""
        # Max-entangled Bell state on 2 qubits
        bell_state = np.zeros(4, dtype=complex)
        bell_state[0] = 1.0 / np.sqrt(2)
        bell_state[3] = 1.0 / np.sqrt(2)

        # Entropy of subsystem 1 qubit should be log(2)
        entropy = compute_von_neumann_entropy(bell_state, [0], 2)
        self.assertAlmostEqual(entropy, np.log(2))

        # Product state entropy should be 0
        product_state = np.zeros(4, dtype=complex)
        product_state[0] = 1.0
        entropy_prod = compute_von_neumann_entropy(product_state, [0], 2)
        self.assertAlmostEqual(entropy_prod, 0.0)

    def test_falsifiability_metrics(self):
        """Test that the dual distances are calculated correctly."""
        n_qubits = 4
        # Create identical states
        v1 = np.zeros(2**n_qubits, dtype=complex)
        v1[0] = 1.0
        v2 = np.zeros(2**n_qubits, dtype=complex)
        v2[0] = 1.0

        D_anchor, D_Haar = compute_falsifiability_metrics(v1, n_qubits, v2, seed=42)
        # Identical overlap trace distance should be 0
        self.assertAlmostEqual(D_anchor, 0.0, places=5)
        # Distance to Haar random state should be greater than 0
        self.assertGreater(D_Haar, 0.0)

    def test_production_engine_optimization(self):
        """Test a brief optimization loop of the production engine."""
        engine = GLAProductionEngine(Lx=1, Ly=2, t=1.0, U=4.0, n_layers=1, verbose=False)
        self.assertEqual(engine.n_qubits, 4)

        energies, final_params, _, fals_history = engine.run_production_vqe(steps=2, learning_rate=0.01)
        self.assertEqual(len(energies), 2)
        self.assertEqual(len(fals_history), 2)

if __name__ == "__main__":
    unittest.main()
