import unittest
from mesh4d import (MeshAddress, MeshLink, ParadoxMesh4D, hyperblock_addresses,
                    BLOCK_4D_SIZE, LAYER_3D_SIZE)

class Mesh4DTests(unittest.TestCase):
    def test_hyperblock_is_7_to_the_fourth(self):
        cells=list(hyperblock_addresses("alpha"))
        self.assertEqual(len(cells),2401)
        self.assertEqual(len(set(cells)),2401)
        self.assertEqual(BLOCK_4D_SIZE,2401)
    def test_seven_343_xyz_layers(self):
        cells=list(hyperblock_addresses("alpha"))
        for w in range(7):
            self.assertEqual(sum(1 for n in cells if n.w==w),343)
        self.assertEqual(LAYER_3D_SIZE*7,2401)
    def test_fourth_dimension_neighbours(self):
        n=MeshAddress("alpha",0,0,0,0)
        self.assertEqual(n.neighbour("w+").coordinates,(0,0,0,1))
        self.assertEqual(n.neighbour("w-").coordinates,(0,0,0,-1))
        self.assertEqual(n.neighbour("x-").coordinates,(-1,0,0,0))
    def test_coordinates_unbounded_and_negative(self):
        n=MeshAddress("alpha",10**80,-10**80,0,7)
        self.assertEqual(n.neighbour("x+").x,10**80+1)
    def test_parallel_spaces_are_separate_namespaces(self):
        a=MeshAddress("parallel-A",0,0,0,0)
        b=MeshAddress("parallel-B",0,0,0,0)
        self.assertNotEqual(a,b)
        self.assertNotEqual(a.stable_id(),b.stable_id())
    def test_cross_space_link_requires_authorized_verified_evidence(self):
        a=MeshAddress("A",0,0,0,0); b=MeshAddress("B",0,0,0,0)
        with self.assertRaises(PermissionError):
            MeshLink(a,b,"bridge",False,True,"evidence-1")
        with self.assertRaises(PermissionError):
            MeshLink(a,b,"bridge",True,False,"evidence-1")
    def test_mesh_routes_across_explicit_bridge(self):
        a=MeshAddress("A",0,0,0,0); a1=a.neighbour("x+")
        b=MeshAddress("B",0,0,0,0); b1=b.neighbour("w+")
        mesh=ParadoxMesh4D()
        mesh.add_link(MeshLink(a,a1,"intra-A",True,True,"ev-A"))
        mesh.add_link(MeshLink(a1,b,"bridge-A-B",True,True,"ev-bridge"))
        mesh.add_link(MeshLink(b,b1,"intra-B",True,True,"ev-B"))
        self.assertEqual(mesh.route(a,b1),(a,a1,b,b1))
    def test_unverified_same_space_link_is_not_routable(self):
        a=MeshAddress("A",0,0,0,0); b=a.neighbour("x+")
        mesh=ParadoxMesh4D(); mesh.add_link(MeshLink(a,b,"unverified",False,False,"evidence"))
        self.assertIsNone(mesh.route(a,b))
    def test_no_route_without_bridge(self):
        a=MeshAddress("A",0,0,0,0); b=MeshAddress("B",0,0,0,0)
        mesh=ParadoxMesh4D()
        mesh.add_node(a); mesh.add_node(b)
        self.assertIsNone(mesh.route(a,b))
    def test_deterministic_shortest_route(self):
        a=MeshAddress("A",0,0,0,0); b=a.neighbour("x+"); c=a.neighbour("y+")
        d=MeshAddress("A",2,0,0,0)
        mesh=ParadoxMesh4D()
        for i,(u,v) in enumerate(((a,b),(b,d),(a,c),(c,d))):
            mesh.add_link(MeshLink(u,v,f"l{i}",True,True,f"e{i}"))
        self.assertEqual(len(mesh.route(a,d)),3)
    def test_duplicate_link_id_rejected(self):
        a=MeshAddress("A",0,0,0,0); b=a.neighbour("x+")
        mesh=ParadoxMesh4D(); link=MeshLink(a,b,"same",True,True,"ev")
        mesh.add_link(link)
        with self.assertRaises(ValueError): mesh.add_link(link)
    def test_audit_chain_verifies(self):
        a=MeshAddress("A",0,0,0,0); b=a.neighbour("w+")
        mesh=ParadoxMesh4D(); mesh.add_link(MeshLink(a,b,"w-link",True,True,"proof"))
        self.assertEqual(len(mesh.audit()),3)
    def test_audit_detects_tampering(self):
        a=MeshAddress("A",0,0,0,0); mesh=ParadoxMesh4D(); mesh.add_node(a)
        mesh._audit[0]["node"]["space_id"]="tampered"
        with self.assertRaises(ValueError): mesh.audit()
    def test_manifest(self):
        m=ParadoxMesh4D().manifest()
        self.assertEqual(m["dimensions"],4)
        self.assertEqual(m["cells_per_hyperblock"],2401)

if __name__ == "__main__": unittest.main()
