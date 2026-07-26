"""Tutorial: Getting Started with Quantum GLA

This script demonstrates the basic usage of the GLA framework.
"""

import sys
sys.path.insert(0, '..')

from gla_vqe import run_gla_vqe
import numpy as np

# Run GLA VQE on a small system (4 qubits)
print("=" * 80)
print("Quantum GLA Tutorial: Basic Usage")
print("=" * 80)

energies, final_params = run_gla_vqe(
    n_qubits=4,
    n_layers=2,
    steps=50,
    init_sigma=1.0 / (4 ** 2),
    adaptive_anchoring=True
)

print(f"\n" + "=" * 80)
print("Results Summary")
print("=" * 80)
print(f"Initial Energy:  {energies[0]:10.6f}")
print(f"Final Energy:    {energies[-1]:10.6f}")
print(f"Improvement:     {energies[0] - energies[-1]:10.6f}")
print(f"Iterations:      {len(energies)}")
print(f"Parameter Shape: {final_params.shape}")
print("=" * 80)