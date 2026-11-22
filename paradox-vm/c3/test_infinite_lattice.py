import unittest
from paradox_vm_c3_infinite_lattice import (Cell, HierarchicalAddress, cells,
    layer_cells, neighbours, expand, CELLS_PER_BLOCK, WAYS_PER_LAYER)


class InfiniteLatticeTests(unittest.TestCase):
    def test_block_is_exactly_343_unique_cells(self):
        block = tuple(cells())
        self.assertEqual(len(block), 343)
        self.assertEqual(len(set(block)), 343)
        self.assertEqual(len(block), CELLS_PER_BLOCK)

    def test_each_layer_has_49_ways(self):
        for z in range(7):
            layer = layer_cells(z)
            self.assertEqual(len(layer), 49)
            self.assertEqual(len(set(layer)), 49)
            self.assertEqual(len(layer), WAYS_PER_LAYER)

    def test_seven_layers_partition_block(self):
        self.assertEqual(set(c for z in range(7) for c in layer_cells(z)), set(cells()))

    def test_cell_bounds(self):
        for bad in [(-1, 0, 0), (7, 0, 0), (0, 0, 7), (1.0, 0, 0)]:
            with self.assertRaises(ValueError):
                Cell(*bad)

    def test_hierarchical_addresses_are_immutable_and_nested(self):
        root = HierarchicalAddress()
        a = root.child(Cell(1, 2, 3))
        b = a.child(Cell(6, 5, 4))
        self.assertEqual(root.depth, 0)
        self.assertEqual(a.depth, 1)
        self.assertEqual(b.depth, 2)
        self.assertEqual(b.parent(), a)
        self.assertEqual(b.encode(), "P/123/654")

    def test_root_has_no_parent(self):
        with self.assertRaises(ValueError):
            HierarchicalAddress().parent()

    def test_unbounded_neighbours_work_at_negative_and_positive_coordinates(self):
        n = neighbours((-100, 0, 100))
        self.assertEqual(n["x-"], (-101, 0, 100))
        self.assertEqual(n["x+"], (-99, 0, 100))
        self.assertEqual(n["z+"], (-100, 0, 101))

    def test_neighbour_input_validation(self):
        for bad in [(1, 2), (1, 2, 3.0), [1, 2, 3]]:
            with self.assertRaises(ValueError):
                neighbours(bad)

    def test_expand_one_level_is_343(self):
        frontier = expand(HierarchicalAddress(), 1)
        self.assertEqual(len(frontier), 343)
        self.assertEqual(len(set(frontier)), 343)

    def test_expand_zero_depth_is_root(self):
        self.assertEqual(expand(HierarchicalAddress(), 0), (HierarchicalAddress(),))

    def test_expand_rejects_negative_depth(self):
        with self.assertRaises(ValueError):
            expand(HierarchicalAddress(), -1)


if __name__ == "__main__":
    unittest.main()
