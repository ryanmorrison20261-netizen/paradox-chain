import unittest
from connection import MeshConnectionManager, PeerIdentity
from fabric import MeshEndpoint, MeshFabric
from mesh4d import MeshAddress, MeshLink, ParadoxMesh4D

class StubSession:
    def __init__(self, peer, incoming=()):
        self.peer=peer
        self.incoming=list(incoming)
        self.sent=[]
        self.closed=False
    def send(self, payload):
        self.sent.append(payload)
        return len(self.sent)
    def receive(self):
        if not self.incoming: raise RuntimeError("no test frame")
        return self.incoming.pop(0)
    def close(self): self.closed=True

def fixture():
    addresses={
        "A":MeshAddress("alpha",0,0,0,0),
        "B":MeshAddress("alpha",1,0,0,0),
        "C":MeshAddress("alpha",2,0,0,0),
    }
    endpoints={}
    for node,address in addresses.items():
        ident=PeerIdentity(node,address.stable_id(),(str(ord(node)%10))*64)
        endpoints[node]=MeshEndpoint(ident,address,"localhost",9000+ord(node))
    topology=ParadoxMesh4D()
    topology.add_link(MeshLink(addresses["A"],addresses["B"],"AB",True,True,"evidence-AB"))
    topology.add_link(MeshLink(addresses["B"],addresses["C"],"BC",True,True,"evidence-BC"))
    return addresses,endpoints,topology

def fabric_for(node, addresses, endpoints, topology):
    local=endpoints[node]
    peers={k:v for k,v in endpoints.items() if k!=node}
    manager=MeshConnectionManager(local.identity,{k:v.identity for k,v in peers.items()})
    return MeshFabric(local,peers,topology,manager)

class MeshFabricTests(unittest.TestCase):
    def test_route_across_fourth_dimension_topology(self):
        addresses,endpoints,topology=fixture()
        self.assertEqual(fabric_for("A",addresses,endpoints,topology).route_to("C"),("A","B","C"))

    def test_send_uses_authenticated_next_hop(self):
        addresses,endpoints,topology=fixture()
        fabric=fabric_for("A",addresses,endpoints,topology)
        ab=StubSession(endpoints["B"].identity); fabric.attach_session("B",ab)
        msg_id=fabric.send_to("C",{"action":"status"})
        self.assertEqual(len(msg_id),32)
        envelope=ab.sent[0]
        self.assertEqual(envelope["route"],["A","B","C"])
        self.assertEqual(envelope["hop_index"],0)

    def test_forwarding_reaches_destination(self):
        addresses,endpoints,topology=fixture()
        a=fabric_for("A",addresses,endpoints,topology)
        b=fabric_for("B",addresses,endpoints,topology)
        c=fabric_for("C",addresses,endpoints,topology)
        ab=StubSession(endpoints["B"].identity); a.attach_session("B",ab)
        a.send_to("C",{"event":"hello"})
        incoming_b=StubSession(endpoints["A"].identity,[ab.sent[0]])
        outgoing_bc=StubSession(endpoints["C"].identity)
        b.attach_session("A",incoming_b); b.attach_session("C",outgoing_bc)
        self.assertIsNone(b.receive_from("A"))
        forwarded=outgoing_bc.sent[0]
        self.assertEqual(forwarded["hop_index"],1)
        incoming_c=StubSession(endpoints["B"].identity,[forwarded])
        c.attach_session("B",incoming_c)
        self.assertEqual(c.receive_from("B"),{"event":"hello"})

    def test_unverified_edge_is_not_routable(self):
        addresses,endpoints,topology=fixture()
        blocked=ParadoxMesh4D()
        blocked.add_link(MeshLink(addresses["A"],addresses["B"],"AB-bad",False,False,"bad-evidence"))
        blocked.add_node(addresses["C"])
        fabric=fabric_for("A",addresses,endpoints,blocked)
        with self.assertRaises(ConnectionError): fabric.route_to("B")

    def test_session_cannot_attach_to_non_neighbor(self):
        addresses,endpoints,topology=fixture()
        fabric=fabric_for("A",addresses,endpoints,topology)
        with self.assertRaises(PermissionError):
            fabric.attach_session("C",StubSession(endpoints["C"].identity))

if __name__ == "__main__": unittest.main()
