import unittest
from lattice import (Infinite343, BlockAddress, NodeAddress, encode_child,
                     decode_child, cell3x3, decode_cell, BLOCK_SIZE, GRID_CELLS)

class TestInfinite343(unittest.TestCase):
    def setUp(self): self.vm=Infinite343()
    def test_343_count_and_roundtrip(self):
        self.assertEqual(BLOCK_SIZE,343)
        for i in range(343): self.assertEqual(encode_child(*decode_child(i)),i)
    def test_expand_is_lazy_and_has_343_unique_children(self):
        root=self.vm.address()
        children=list(self.vm.expand(root))
        self.assertEqual(len(children),343)
        self.assertEqual(len({c.stable_id for c in children}),343)
        self.assertEqual(root.depth,0)
        self.assertEqual(children[-1].depth,1)
    def test_recursive_nesting(self):
        n=self.vm.address().child(1,2,3).child(6,6,6)
        self.assertEqual(n.depth,2)
        self.assertEqual(n.parent().depth,1)
        self.assertEqual(n.parent().parent().depth,0)
    def test_3x3_has_nine_cells(self):
        cells=self.vm.cell_grid()
        self.assertEqual(len(cells),9)
        self.assertEqual([c.cell for c in cells],list(range(9)))
        for i in range(9): self.assertEqual(cell3x3(*decode_cell(i)),i)
    def test_nine_cells_each_expand_to_343(self):
        self.assertEqual(sum(sum(1 for _ in self.vm.expand(c)) for c in self.vm.cell_grid()),9*343)
    def test_infinite_positive_negative_coordinates(self):
        p=BlockAddress(10**100,0,-10**100)
        self.assertEqual(p.neighbour("xp").x,10**100+1)
        self.assertEqual(p.neighbour("zn").z,-10**100-1)
        self.assertEqual(p.neighbour("xn").neighbour("xp"),p)
    def test_all_six_neighbours(self):
        n=self.vm.neighbourhood()
        self.assertEqual(set(n),{"xp","xn","yp","yn","zp","zn"})
        self.assertEqual(n["xp"].tuple,(1,0,0))
        self.assertEqual(n["zn"].tuple,(0,0,-1))
    def test_stable_ids(self):
        self.assertEqual(self.vm.address((1,2,3),4,(5,6)).stable_id,
                         self.vm.address((1,2,3),4,(5,6)).stable_id)
        self.assertNotEqual(self.vm.address().stable_id,self.vm.address(cell=1).stable_id)
    def test_invalid_coordinates_rejected(self):
        for args in [((-1,0,0),0,()),((0,0),0,()),((0,0,0),9,()),((0,0,0),0,(343,))]:
            with self.assertRaises(ValueError): self.vm.address(*args)
    def test_manifest_describes_lazy_model(self):
        m=self.vm.manifest(self.vm.address())
        self.assertEqual(m["children_per_node"],343)
        self.assertEqual(m["grid_cells"],9)
        self.assertEqual(m["materialized_children"],0)
        self.assertEqual(m["expansion"],"lazy")
    def test_expansion_order_is_deterministic(self):
        ids1=[x.stable_id for x in self.vm.expand(self.vm.address())]
        ids2=[x.stable_id for x in self.vm.expand(self.vm.address())]
        self.assertEqual(ids1,ids2)

if __name__=="__main__": unittest.main()
