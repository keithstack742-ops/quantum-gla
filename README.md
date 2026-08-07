# Quantum GLA: Geometric Landscape Anchoring

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen.svg)]()

**Overcoming Barren Plateaus in Large-Scale Variational Quantum Algorithms via Geometric Landscape Anchoring**

---

## Overview

Quantum GLA is a complete framework for eliminating **Barren Plateaus** in Variational Quantum Algorithms (VQAs). By combining:

1. **Identity-Based Initialization** (or physical anchoring near the Néel state $|1010...\rangle$)
2. **Symmetry-Preserving Gates** (`XY` hopping and `R_zz` interaction gates conserving particle number $N$ and total spin $S_z$)
3. **Fermionic SWAP Gates (`fSWAP`)** to manage 2D topology and eliminate Jordan-Wigner strings
4. **Adaptive Total Stability Monitoring** (incorporating both QFIM stability and von Neumann entanglement entropy)

We transform the optimization landscape from **exponential complexity $\mathcal{O}(2^n)$** to **polynomial complexity $\mathcal{O}(\text{poly}(n))$**.

---

## Core Features

- ✅ **GLAProductionEngine**: High-fidelity, production-grade 2D Fermi-Hubbard lattice simulation.
- ✅ **Symmetry Conservation**: Guarantees conservation of particle number and spin projections throughout optimization.
- ✅ **Total Stability Metric ($S_{\text{total}}$)**: Adapts bond dimensions and triggers parameter re-centering based on entanglement entropy $S(\psi)$ and the Fubini-Study QFIM eigenvalues.
- ✅ **Classical Shadows Dual-Distance Falsifiability**: Rigorously computes Frobenius/trace distances $D_{\text{anchor}}$ and $D_{\text{Haar}}$ to guarantee concentration about a physical attractor, avoiding both anchor bias and high-entropy voids.

---

## Quick Start

### Installation

```bash
pip install pennylane numpy scipy matplotlib
git clone https://github.com/keithstack742-ops/quantum-gla.git
cd quantum-gla
```

### Basic Usage with production GLA Hubbard Engine

```python
from gla_vqe import run_gla_production

# Run the production 2D Fermi-Hubbard engine (8 qubits, 2x2 grid)
energy_history, final_params, entropy_history, fals_history = run_gla_production(
    Lx=2,
    Ly=2,
    t=1.0,
    U=4.0,
    steps=50,
    learning_rate=0.05
)

print(f"Final Energy: {energy_history[-1]:.6f}")
print(f"Final Entanglement Entropy: {entropy_history[-1]:.6f}")
print(f"Final Falsifiability Distance (D_anchor): {fals_history[-1][0]:.6f}")
print(f"Final Falsifiability Distance (D_Haar): {fals_history[-1][1]:.6f}")
```

---

## Documentation

### Core Files

| File | Purpose |
|------|----------|
| [`gla_vqe.py`](gla_vqe.py) | Production GLA Engine, 2D Hubbard mapping, & helper routines |
| [`GLA_Whitepaper.md`](GLA_Whitepaper.md) | Technical whitepaper with concentration-of-measure proofs & scenario hypotheses |
| [`COMPARISON.md`](COMPARISON.md) | GLA vs. other BP mitigation strategies |
| [`test_gla.py`](test_gla.py) | Comprehensive test suite |
| [`examples/`](examples/) | Jupyter notebooks & tutorials |

### Theoretical Background

Start here: [`GLA_Whitepaper.md`](GLA_Whitepaper.md)

**Key Sections:**
- §1: Barren Plateau problem & GLA hypothesis
- §2: The GLA framework (Trainable Manifold, Adaptive Re-centering)
- §3: Fully expanded concentration-of-measure proofs and QFIM purity lower bounds
- §4: Three rigorous, verifiable scenarios (FeMoco $n=54$, QAOA Max-Cut, and TFIM critical systems)

---

## Requirements

```
Python ≥ 3.8
pennylane >= 0.45.0
numpy >= 1.21.0
scipy >= 1.7.0
matplotlib >= 3.5.0 (for plotting)
```

---

## License

MIT License © 2026 Keith Stack
