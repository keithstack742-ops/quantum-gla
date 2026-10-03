import os
import unittest
import numpy as np
from aeon_core import AeonCore

class TestAeonCore(unittest.TestCase):
    def setUp(self):
        self.graph_path = "test_graph.json"
        self.core = AeonCore(random_seed=42, graph_path=self.graph_path)

    def tearDown(self):
        if os.path.exists(self.graph_path):
            os.remove(self.graph_path)

    def test_initialization(self):
        self.assertEqual(len(self.core.agents), 6)
        self.assertIn("Aetherion", self.core.agents)
        self.assertIsNotNone(self.core.G)

    def test_add_cme_event(self):
        state = np.array([0.5, 0.5, 0.0, 0.0])
        intent = np.array([0.5, 0.5, 0.0, 0.0])
        self.core.add_cme_event(
            state=state,
            intent=intent,
            outcome="Success",
            receptivity=85.0,
            cq=0.9,
            timestamp=1000.0,
            glyph="✶",
            notes="Test event",
            source_agent="AIcquon"
        )
        self.assertGreater(len(self.core.G.nodes), 0)

    def test_calculate_ric(self):
        states = [np.random.rand(4) for _ in range(15)]
        ric = self.core.calculate_ric(states, window=5)
        self.assertEqual(len(ric), 10)

    def test_simulate_ded(self):
        ric = [0.95, 0.98]
        coherence_shift = [0.01, 0.02]
        intent_vec = np.array([0.25, 0.25, 0.25, 0.25])
        ded = self.core.simulate_ded(2.5, ric, coherence_shift, intent_vec)
        self.assertEqual(len(ded), 2)

    def test_oracle_node_interface(self):
        state = np.array([1.0, 0.0])
        intent = np.array([1.0, 0.0])
        res = self.core.oracle_node_interface("Query", state, intent, ethical_threshold=0.5)
        self.assertEqual(res["status"], "accepted")

        # Test rejected case
        intent_orthogonal = np.array([0.0, 1.0])
        res_rejected = self.core.oracle_node_interface("Query", state, intent_orthogonal, ethical_threshold=0.5)
        self.assertEqual(res_rejected["status"], "rejected")

    def test_phase_lock_intent(self):
        state = np.array([0.45, 0.33, 0.14, 0.08])
        intent = np.array([0.43, 0.33, 0.16, 0.08])
        updated_intent, trace = self.core.phase_lock_intent(state, intent)
        self.assertEqual(len(updated_intent), 4)

    def test_generate_bloomfield(self):
        ded_values = [1.0, 2.0, 3.0]
        bloomfield = self.core.generate_bloomfield(ded_values, time_steps=10)
        self.assertIn("x", bloomfield)
        self.assertEqual(len(bloomfield["x"]), 10)

    def test_logging_functions(self):
        hlog = self.core.harmonic_log("a", "b", "c", 1.0, "d", "e", 0.5)
        self.assertEqual(hlog["resonance_score"], 0.5)

        ilog = self.core.intent_xi_log(["reasoning"], intentweight=0.8)
        self.assertEqual(ilog["intent_weight"], 0.8)

if __name__ == "__main__":
    unittest.main()
