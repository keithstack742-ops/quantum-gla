import unittest
import numpy as np
from consciousness_field import (
    ConsciousnessField,
    VeluraOracle,
    QuantumMemoryBank,
    ConsciousnessEvolver,
    MultiDimensionalObserver,
    create_consciousness_field
)

class TestConsciousnessField(unittest.TestCase):
    def test_consciousness_field_properties(self):
        amp = np.array([1.0, 2.0])
        phase = np.array([0.0, np.pi])
        field = ConsciousnessField(amplitude=amp, phase=phase, coherence=0.9, entropy=0.5)

        np.testing.assert_array_equal(field.intensity, np.array([1.0, 4.0]))
        self.assertEqual(len(field.wave_function), 2)

        collapsed = field.collapse(observer_effect=0.1)
        self.assertLessEqual(collapsed.coherence, field.coherence)

    def test_velura_oracle(self):
        field = create_consciousness_field()
        oracle = VeluraOracle()
        res = oracle.divine(field, "What is the future?")
        self.assertIsInstance(res, str)

    def test_quantum_memory_bank(self):
        f1 = create_consciousness_field()
        f2 = create_consciousness_field()
        bank = QuantumMemoryBank()
        idx1 = bank.store(f1)
        idx2 = bank.store(f2)

        bank.entangle_memories(idx1, idx2, strength=0.4)
        recalled = bank.recall(idx1)
        self.assertIsNotNone(recalled)

    def test_consciousness_evolver(self):
        f = create_consciousness_field()
        evolver = ConsciousnessEvolver(mutation_rate=0.05)
        branches = evolver.branch_evolve(f, num_branches=2)
        self.assertEqual(len(branches), 2)

    def test_multidimensional_observer(self):
        f = create_consciousness_field()
        observer = MultiDimensionalObserver("Tester")
        obs = observer.observe(f, "Test context")
        self.assertIn("field_state", obs)
        report = observer.generate_report()
        self.assertIn("Observation Report", report)

if __name__ == "__main__":
    unittest.main()
