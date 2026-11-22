import json, tempfile, unittest
from pathlib import Path
from decimal import Decimal
from world3d import AABB, World3D, metres, save_state, load_state, replay_events

class TestC2(unittest.TestCase):
    def test_3d_translation(self):
        w=World3D(); w.move(("1","2","3"),"m")
        self.assertEqual(w.snapshot()["position_m"],["1","2","3"])
    def test_unit_conversions(self):
        self.assertEqual(metres("100","cm"),Decimal("1"))
        self.assertEqual(metres("1","km"),Decimal("1000"))
        self.assertEqual(metres("10","mm"),Decimal("0.010"))
    def test_unknown_unit_rejected(self):
        with self.assertRaises(ValueError): metres(1,"mile")
    def test_decimal_no_float_drift(self):
        w=World3D(); w.move(("0.1","0.2","0.3")); w.move(("0.2","0.3","0.4"))
        self.assertEqual(w.snapshot()["position_m"],["0.3","0.5","0.7"])
    def test_bounds_enforced_atomically(self):
        w=World3D(bounds=(("0","0","0"),("10","10","10")))
        with self.assertRaises(ValueError): w.move(("11","0","0"))
        self.assertEqual(w.snapshot()["position_m"],["0","0","0"])
        self.assertEqual(w.snapshot()["event_count"],0)
    def test_swept_collision_detected(self):
        box=AABB.from_values("wall",("4","-1","-1"),("6","1","1"))
        w=World3D(obstacles=(box,))
        with self.assertRaisesRegex(ValueError,"collision"): w.move(("10","0","0"))
        self.assertEqual(w.snapshot()["position_m"],["0","0","0"])
    def test_no_collision_outside_box(self):
        box=AABB.from_values("wall",("4","-1","-1"),("6","1","1"))
        w=World3D(obstacles=(box,)); w.move(("10","2","0"))
        self.assertEqual(w.snapshot()["position_m"],["10","2","0"])
    def test_velocity_acceleration_time(self):
        w=World3D(); w.set_kinematics(("1","0","0"),("2","0","0")); w.step("2")
        self.assertEqual(w.snapshot()["position_m"],["4","0","0"])
        self.assertEqual(w.snapshot()["velocity_mps"],["5","0","0"])
        self.assertEqual(w.snapshot()["time_s"],"2")
    def test_nonpositive_dt_rejected(self):
        w=World3D()
        for dt in ("0","-1"):
            with self.assertRaises(ValueError): w.step(dt)
    def test_invalid_aabb_rejected(self):
        with self.assertRaises(ValueError): AABB.from_values("bad",(1,1,1),(1,2,3))
    def test_persistence_integrity(self):
        w=World3D(); w.move(("1","2","3"))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"state.json"; digest=save_state(p,w)
            self.assertEqual(load_state(p)["position_m"],["1","2","3"])
            raw=json.loads(p.read_text()); raw["state"]["position_m"][0]="999"; p.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError,"digest"): load_state(p)
    def test_event_replay(self):
        w=World3D(); w.move(("1","2","3")); w.move(("-1","0","2"))
        self.assertEqual(replay_events(("0","0","0"),w.snapshot()["events"]),("0","2","5"))
    def test_replay_detects_tampering(self):
        w=World3D(); w.move(("1","0","0")); events=w.snapshot()["events"]
        events[0]["end_m"][0]="99"
        with self.assertRaises(ValueError): replay_events(("0","0","0"),events)

if __name__=="__main__": unittest.main()
