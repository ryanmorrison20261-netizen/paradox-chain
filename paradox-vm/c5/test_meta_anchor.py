import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from meta_anchor import Address, MetaAnchor, AGENTS, create_s7_anchors


class MetaAnchorTests(unittest.TestCase):
    def setUp(self):
        self.home = Address("home", 0, 0, 0, 0)
        self.agent = MetaAnchor("S7-1", self.home)

    def test_jump_keeps_home_and_returns(self):
        target = Address("parallel-A", 7, 2, -1, 3)
        self.agent.jump(target, authorized_spaces={"parallel-A"})
        self.assertEqual(self.agent.home, self.home)
        self.assertEqual(self.agent.current, target)
        self.agent.return_home()
        self.assertEqual(self.agent.current, self.home)
        self.assertTrue(self.agent.verify())

    def test_skip_hops_are_ordered_and_reversible(self):
        hops = [Address("A", 1, 0, 0, 0), Address("C", 9, 0, 0, 2)]
        records = self.agent.skip_hop(hops, authorized_spaces={"A", "C"})
        self.assertEqual(self.agent.current, hops[-1])
        self.assertEqual([r.sequence for r in records], [1, 2])
        self.agent.return_home()
        self.assertTrue(self.agent.verify())
        self.assertEqual([r.sequence for r in self.agent.history], [1, 2, 3])

    def test_skip_hops_reject_atomically_if_later_hop_unauthorized(self):
        before = self.agent.checkpoint()
        hops = [Address("allowed", 1, 0, 0, 0),
                Address("blocked", 2, 0, 0, 0)]
        with self.assertRaises(PermissionError):
            self.agent.skip_hop(hops, authorized_spaces={"allowed"})
        self.assertEqual(self.agent.checkpoint(), before)
        self.assertEqual(self.agent.current, self.home)
        self.assertEqual(self.agent.sequence, 0)

    def test_skip_hops_reject_invalid_item_without_mutation(self):
        with self.assertRaises(TypeError):
            self.agent.skip_hop([Address("A", 1, 0, 0, 0), "bad"],
                                authorized_spaces={"A"})
        self.assertEqual(self.agent.sequence, 0)
        self.assertTrue(self.agent.verify())

    def test_unauthorized_jump_does_not_mutate(self):
        with self.assertRaises(PermissionError):
            self.agent.jump(Address("blocked", 0, 0, 0, 1), authorized_spaces={"A"})
        self.assertEqual(self.agent.current, self.home)
        self.assertEqual(self.agent.sequence, 0)

    def test_each_agent_has_own_anchor(self):
        homes = {a: Address("home-"+a, 0, 0, 0, 0) for a in AGENTS}
        anchors = create_s7_anchors(homes)
        self.assertEqual(len(anchors), 7)
        for a in AGENTS:
            self.assertEqual(anchors[a].current, homes[a])
            self.assertTrue(anchors[a].verify())

    def test_requires_exactly_seven_agents(self):
        with self.assertRaises(ValueError):
            create_s7_anchors({"S7-1": self.home})

    def test_checkpoint_records_logical_time_and_digest(self):
        self.agent.jump(Address("B", 1, 2, 3, 4), authorized_spaces={"B"})
        cp = self.agent.checkpoint()
        self.assertEqual(cp["logical_time"], 1)
        self.assertEqual(cp["schema"], "paradox-s7-checkpoint-v2")
        self.assertEqual(len(cp["checkpoint_hash"]), 64)

    def test_hash_chain_detects_tampering(self):
        self.agent.jump(Address("B", 1, 2, 3, 4), authorized_spaces={"B"})
        r = self.agent.history[0]
        self.agent.history[0] = replace(
            r, destination={"space": "evil", "x": 0, "y": 0, "z": 0, "w": 0})
        self.assertFalse(self.agent.verify())
        with self.assertRaises(ValueError):
            self.agent.checkpoint()

    def test_restore_checkpoint_round_trip(self):
        self.agent.skip_hop([Address("B", 1, 2, 3, 4),
                             Address("C", 5, 6, 7, 8)],
                            authorized_spaces={"B", "C"})
        self.agent.return_home()
        restored = MetaAnchor.from_checkpoint(self.agent.checkpoint())
        self.assertEqual(restored.checkpoint(), self.agent.checkpoint())
        self.assertEqual(restored.current, self.home)
        self.assertEqual(restored.sequence, 3)
        self.assertTrue(restored.verify())

    def test_durable_save_and_restart_restore(self):
        self.agent.jump(Address("remote", 3, 2, 1, 0),
                        authorized_spaces={"remote"})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "s7-1.checkpoint.json"
            file_digest = self.agent.save(path)
            self.assertEqual(len(file_digest), 64)
            restored = MetaAnchor.restore(path)
            self.assertEqual(restored.checkpoint(), self.agent.checkpoint())
            self.assertEqual(restored.current, Address("remote", 3, 2, 1, 0))

    def test_checkpoint_digest_detects_tampering(self):
        cp = self.agent.checkpoint()
        cp["current"]["space"] = "forged"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            MetaAnchor.from_checkpoint(cp)

    def test_restore_rejects_corrupt_history_even_with_recomputed_outer_digest(self):
        cp = self.agent.checkpoint()
        self.agent.jump(Address("remote", 1, 1, 1, 1),
                        authorized_spaces={"remote"})
        cp = self.agent.checkpoint()
        cp["history"][0]["destination"]["space"] = "forged"
        # Recompute only the outer digest: the per-record chain must still fail.
        from meta_anchor import _digest
        body = {k: v for k, v in cp.items() if k != "checkpoint_hash"}
        cp["checkpoint_hash"] = _digest(body)
        with self.assertRaisesRegex(ValueError, "history verification"):
            MetaAnchor.from_checkpoint(cp)

    def test_restore_rejects_unknown_schema(self):
        cp = self.agent.checkpoint()
        cp["schema"] = "unknown"
        with self.assertRaises(ValueError):
            MetaAnchor.from_checkpoint(cp)

    def test_file_restore_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text("{not-json", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "could not be read"):
                MetaAnchor.restore(path)

    def test_address_requires_integer_coordinates(self):
        with self.assertRaises(ValueError):
            Address("home", 1.5, 0, 0, 0)

    def test_boolean_is_not_an_integer_coordinate(self):
        with self.assertRaises(ValueError):
            Address("home", True, 0, 0, 0)


if __name__ == "__main__":
    unittest.main()
