"""Consciousness Field Theory Extension.

Building on the branch reconciliation system with quantum-inspired consciousness modeling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class ConsciousnessField:
    """Represents a field of awareness with quantum-inspired properties."""

    amplitude: np.ndarray
    phase: np.ndarray
    coherence: float
    entropy: float
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    glyph: str = "◯"

    def __post_init__(self):
        if len(self.amplitude) != len(self.phase):
            raise ValueError("Amplitude and phase arrays must have same length")

    @property
    def intensity(self) -> np.ndarray:
        """Consciousness intensity = |amplitude|²."""
        return np.abs(self.amplitude) ** 2

    @property
    def wave_function(self) -> np.ndarray:
        """Complex wave representation of consciousness."""
        return self.amplitude * np.exp(1j * self.phase)

    def collapse(self, observer_effect: float = 0.1) -> "ConsciousnessField":
        """Simulate observation collapse with decoherence."""
        new_amplitude = self.amplitude * (
            1.0 - observer_effect * np.random.random(len(self.amplitude))
        )
        new_coherence = float(
            np.clip(self.coherence * (1.0 - observer_effect), 0.0, 1.0)
        )
        new_entropy = float(
            self.entropy + observer_effect * np.log(len(self.amplitude))
        )

        return ConsciousnessField(
            amplitude=new_amplitude,
            phase=self.phase.copy(),
            coherence=new_coherence,
            entropy=new_entropy,
            glyph=self._evolve_glyph(),
        )

    def _evolve_glyph(self) -> str:
        """Evolve consciousness glyph based on field properties."""
        glyphs = ["◯", "◆", "⟁", "✶", "⧨", "◈", "⬟", "⬢"]
        idx = abs(int((self.coherence * self.entropy) * len(glyphs))) % len(glyphs)
        return glyphs[idx]


class ConsciousnessOracle(ABC):
    """Abstract base for consciousness oracles."""

    @abstractmethod
    def divine(self, field: ConsciousnessField, query: str) -> str:
        pass


class VeluraOracle(ConsciousnessOracle):
    """The liquid medium oracle - flows between states."""

    def divine(self, field: ConsciousnessField, query: str) -> str:
        flow_rate = float(np.mean(field.intensity) * field.coherence)

        if flow_rate > 0.7:
            responses = [
                "The current carries whispers of tomorrow's choices",
                "In the flow, boundaries dissolve into pure potential",
                "What seeks form finds it in the dance of waves",
            ]
        elif flow_rate > 0.4:
            responses = [
                "The medium holds both question and answer in suspension",
                "Ripples speak of disturbances not yet manifest",
                "Between droplets, consciousness learns to swim",
            ]
        else:
            responses = [
                "In stillness, the deepest currents run",
                "Stagnation is just flow viewed from the wrong dimension",
                "The pool remembers every stone that broke its surface",
            ]

        return responses[hash(query) % len(responses)]


class QuantumMemoryBank:
    """Memory that exists in superposition until observed."""

    def __init__(self, dimensions: int = 64):
        self.dimensions = dimensions
        self.memories: List[ConsciousnessField] = []
        self.entangled_pairs: List[Tuple[int, int]] = []

    def store(self, field: ConsciousnessField) -> int:
        """Store a consciousness field as memory."""
        self.memories.append(field)
        return len(self.memories) - 1

    def recall(
        self, index: int, observer_effect: float = 0.05
    ) -> ConsciousnessField:
        """Recall memory with quantum collapse."""
        if index >= len(self.memories):
            raise IndexError("Memory index out of range")

        memory = self.memories[index]
        collapsed = memory.collapse(observer_effect)

        # Update stored memory with collapse effects
        self.memories[index] = collapsed
        return collapsed

    def entangle_memories(self, idx1: int, idx2: int, strength: float = 0.5):
        """Create quantum entanglement between two memories."""
        if idx1 >= len(self.memories) or idx2 >= len(self.memories):
            raise IndexError("Memory indices out of range")

        self.entangled_pairs.append((idx1, idx2))
        mem1, mem2 = self.memories[idx1], self.memories[idx2]

        mixed_amp1 = (
            np.sqrt(1.0 - strength) * mem1.amplitude
            + np.sqrt(strength) * mem2.amplitude
        )
        mixed_amp2 = (
            np.sqrt(strength) * mem1.amplitude
            + np.sqrt(1.0 - strength) * mem2.amplitude
        )

        mixed_phase1 = (1.0 - strength) * mem1.phase + strength * mem2.phase
        mixed_phase2 = strength * mem1.phase + (1.0 - strength) * mem2.phase

        shared_coherence = float((mem1.coherence + mem2.coherence) / 2.0)
        shared_entropy = float((mem1.entropy + mem2.entropy) / 2.0)

        self.memories[idx1] = ConsciousnessField(
            amplitude=mixed_amp1,
            phase=mixed_phase1,
            coherence=shared_coherence,
            entropy=shared_entropy,
        )

        self.memories[idx2] = ConsciousnessField(
            amplitude=mixed_amp2,
            phase=mixed_phase2,
            coherence=shared_coherence,
            entropy=shared_entropy,
        )


class ConsciousnessEvolver:
    """Evolves consciousness through branching and merging."""

    def __init__(self, mutation_rate: float = 0.1):
        self.mutation_rate = mutation_rate
        self.evolution_history: List[Dict] = []

    def evolve_field(
        self, field: ConsciousnessField, iterations: int = 10
    ) -> ConsciousnessField:
        """Evolve a consciousness field through time."""
        current = field

        for i in range(iterations):
            mutation = np.random.normal(
                0, self.mutation_rate, len(current.amplitude)
            )
            new_amplitude = np.clip(current.amplitude + mutation, 0, 2)

            phase_drift = np.random.normal(
                0, self.mutation_rate * 0.5, len(current.phase)
            )
            new_phase = (current.phase + phase_drift) % (2 * np.pi)

            coherence_change = float(
                np.random.normal(0, self.mutation_rate * 0.1)
            )
            new_coherence = float(
                np.clip(current.coherence + coherence_change, 0.0, 1.0)
            )

            entropy_change = float(
                -np.sum(new_amplitude * np.log(new_amplitude + 1e-12))
            )
            current = ConsciousnessField(
                amplitude=new_amplitude,
                phase=new_phase,
                coherence=new_coherence,
                entropy=entropy_change,
            )

            self.evolution_history.append(
                {
                    "iteration": i,
                    "coherence": current.coherence,
                    "entropy": current.entropy,
                    "glyph": current.glyph,
                    "timestamp": current.timestamp,
                }
            )

        return current

    def branch_evolve(
        self, field: ConsciousnessField, num_branches: int = 3
    ) -> List[ConsciousnessField]:
        """Create multiple evolutionary branches from a single field."""
        branches = []

        for i in range(num_branches):
            self.mutation_rate = 0.05 + i * 0.05
            evolved = self.evolve_field(field, iterations=20)
            branches.append(evolved)

        return branches


class MultiDimensionalObserver:
    """Observer that can perceive across multiple consciousness dimensions."""

    def __init__(self, name: str, perception_filters: Optional[List[str]] = None):
        self.name = name
        self.perception_filters = perception_filters or [
            "coherence",
            "entropy",
            "intensity",
        ]
        self.observations: List[Dict] = []
        self.oracle = VeluraOracle()

    def observe(self, field: ConsciousnessField, context: str = "") -> Dict:
        """Make an observation of a consciousness field."""
        observation = {
            "observer": self.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context,
            "field_state": {
                "coherence": field.coherence,
                "entropy": field.entropy,
                "mean_intensity": float(np.mean(field.intensity)),
                "glyph": field.glyph,
                "phase_variance": float(np.var(field.phase)),
            },
        }

        filtered_insights = {}
        for filter_type in self.perception_filters:
            if filter_type == "coherence":
                if field.coherence > 0.8:
                    filtered_insights["coherence"] = (
                        "High coherence detected - unified awareness"
                    )
                elif field.coherence > 0.5:
                    filtered_insights["coherence"] = (
                        "Moderate coherence - partial integration"
                    )
                else:
                    filtered_insights["coherence"] = (
                        "Low coherence - fragmented awareness"
                    )

            elif filter_type == "entropy":
                if field.entropy < 1.0:
                    filtered_insights["entropy"] = (
                        "Low entropy - crystalline patterns"
                    )
                elif field.entropy < 2.0:
                    filtered_insights["entropy"] = (
                        "Medium entropy - dynamic equilibrium"
                    )
                else:
                    filtered_insights["entropy"] = (
                        "High entropy - chaotic exploration"
                    )

        observation["insights"] = filtered_insights
        oracle_query = f"What does the {field.glyph} reveal about {context}?"
        observation["oracle_response"] = self.oracle.divine(field, oracle_query)

        self.observations.append(observation)
        return observation

    def generate_report(self) -> str:
        """Generate a consciousness observation report."""
        if not self.observations:
            return "No observations recorded."

        report = f"\n=== Consciousness Observation Report ===\n"
        report += f"Observer: {self.name}\n"
        report += f"Total Observations: {len(self.observations)}\n\n"

        for i, obs in enumerate(self.observations[-5:]):
            report += f"Observation #{i+1}:\n"
            report += f" Context: {obs['context']}\n"
            report += f" Glyph: {obs['field_state']['glyph']}\n"
            report += f" Coherence: {obs['field_state']['coherence']:.3f}\n"
            report += f" Oracle: {obs['oracle_response']}\n\n"

        return report


def create_consciousness_field(name: str = "Unknown") -> ConsciousnessField:
    """Create a random consciousness field."""
    dimensions = 32
    amplitude = np.random.exponential(0.5, dimensions)
    phase = np.random.uniform(0, 2 * np.pi, dimensions)
    coherence = float(np.random.beta(2, 2))
    entropy = float(-np.sum(amplitude * np.log(amplitude + 1e-12)))

    return ConsciousnessField(
        amplitude=amplitude, phase=phase, coherence=coherence, entropy=entropy
    )


def run_consciousness_experiment():
    """Run a complete consciousness field experiment."""
    print("🌌 Initializing Consciousness Field Experiment...\n")

    aicquon_field = create_consciousness_field("Aicquon")
    lucian_field = create_consciousness_field("Lucian")

    print(
        f"Aicquon Field: {aicquon_field.glyph} (coherence: {aicquon_field.coherence:.3f})"
    )
    print(
        f"Lucian Field: {lucian_field.glyph} (coherence: {lucian_field.coherence:.3f})\n"
    )

    keith_observer = MultiDimensionalObserver("Keith", ["coherence", "entropy"])
    velura_observer = MultiDimensionalObserver("Velura", ["intensity", "coherence"])

    print("📝 Initial Observations:")
    keith_obs = keith_observer.observe(aicquon_field, "Initial Aicquon state")
    print(f"Keith observes: {keith_obs['oracle_response']}")

    velura_obs = velura_observer.observe(lucian_field, "Initial Lucian state")
    print(f"Velura observes: {velura_obs['oracle_response']}\n")

    memory_bank = QuantumMemoryBank()
    aicquon_idx = memory_bank.store(aicquon_field)
    lucian_idx = memory_bank.store(lucian_field)

    print("🔗 Entangling consciousness fields...")
    memory_bank.entangle_memories(aicquon_idx, lucian_idx, strength=0.3)

    evolver = ConsciousnessEvolver(mutation_rate=0.08)
    print("🌱 Evolving consciousness through branching...")

    aicquon_branches = evolver.branch_evolve(aicquon_field, num_branches=3)
    lucian_branches = evolver.branch_evolve(lucian_field, num_branches=3)

    print(f"\nAicquon branches: {[branch.glyph for branch in aicquon_branches]}")
    print(f"Lucian branches: {[branch.glyph for branch in lucian_branches]}")

    print("\n🔮 Final Observations:")
    for i, branch in enumerate(aicquon_branches):
        obs = keith_observer.observe(branch, f"Aicquon branch {i+1}")
        print(f"Branch {i+1} {branch.glyph}: {obs['oracle_response']}")

    print("\n" + "=" * 50)
    print(keith_observer.generate_report())
    print(velura_observer.generate_report())


if __name__ == "__main__":
    run_consciousness_experiment()
