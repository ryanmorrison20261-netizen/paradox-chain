import unittest
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
        self.agent.skip_hop(hops, authorized_spaces={"A", "C"})
        self.assertEqual(self.agent.current, hops[-1])
        self.agent.return_home()
        self.assertTrue(self.agent.verify())
        self.assertEqual([r.sequence for r in self.agent.history], [1, 2, 3])

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

    def test_checkpoint_records_logical_time(self):
        self.agent.jump(Address("B", 1, 2, 3, 4), authorized_spaces={"B"})
        cp = self.agent.checkpoint()
        self.assertEqual(cp["logical_time"], 1)
        self.assertTrue(cp["verified"])

    def test_hash_chain_detects_tampering(self):
        self.agent.jump(Address("B", 1, 2, 3, 4), authorized_spaces={"B"})
        r = self.agent.history[0]
        from dataclasses import replace
        self.agent.history[0] = replace(r, destination={"space":"evil","x":0,"y":0,"z":0,"w":0})
        self.assertFalse(self.agent.verify())

    def test_address_requires_integer_coordinates(self):
        with self.assertRaises(ValueError):
            Address("home", 1.5, 0, 0, 0)

if __name__ == "__main__":
    unittest.main()
