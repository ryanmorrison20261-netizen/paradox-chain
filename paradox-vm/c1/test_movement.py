import unittest
from decimal import Decimal

from movement import C1Movement, run_c1_test


class TestC1Movement(unittest.TestCase):
    def test_requested_backward_then_forward_sequence(self):
        result = run_c1_test()
        self.assertTrue(result["passed"])
        self.assertEqual(result["position_m"], "45")
        self.assertEqual(result["movement_count"], 2)

    def test_event_chain_is_contiguous(self):
        vm = C1Movement()
        first = vm.move("backward", "5")
        second = vm.move("forward", "50")
        self.assertEqual(first.end_m, "-5")
        self.assertEqual(second.start_m, first.end_m)
        self.assertEqual(second.end_m, "45")

    def test_decimal_precision_without_binary_float_drift(self):
        vm = C1Movement()
        vm.move("forward", "0.1")
        vm.move("forward", "0.2")
        self.assertEqual(vm.position, Decimal("0.3"))

    def test_minimum_boundary(self):
        vm = C1Movement(start_m=0, min_m=-5, max_m=50)
        vm.move("backward", 5)
        with self.assertRaises(ValueError):
            vm.move("backward", "0.0001")
        self.assertEqual(vm.position, Decimal("-5"))
        self.assertEqual(len(vm.history), 1)

    def test_maximum_boundary(self):
        vm = C1Movement(start_m=0, min_m=-5, max_m=50)
        vm.move("forward", 50)
        with self.assertRaises(ValueError):
            vm.move("forward", 1)
        self.assertEqual(vm.position, Decimal("50"))

    def test_negative_distance_rejected(self):
        vm = C1Movement()
        with self.assertRaises(ValueError):
            vm.move("forward", -1)
        self.assertEqual(vm.position, Decimal("0"))

    def test_unknown_direction_rejected(self):
        with self.assertRaises(ValueError):
            C1Movement().move("left", 1)

    def test_non_finite_distance_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.assertRaises(ValueError):
                C1Movement().move("forward", value)

    def test_invalid_bounds_rejected(self):
        with self.assertRaises(ValueError):
            C1Movement(min_m=10, max_m=0)

    def test_failed_move_does_not_mutate_history(self):
        vm = C1Movement(max_m=1)
        with self.assertRaises(ValueError):
            vm.move("forward", 2)
        self.assertEqual(vm.position, Decimal("0"))
        self.assertEqual(vm.history, [])


if __name__ == "__main__":
    unittest.main()
