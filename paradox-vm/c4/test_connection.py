import json, socket, struct, unittest, ssl, tempfile, subprocess, shutil, threading, queue
from pathlib import Path
from hashlib import sha256
from connection import PROTOCOL, MeshConnectionManager, MeshSession, PeerIdentity, ReplayCache, send_frame, receive_frame

class FakeTLS:
    def __init__(self, incoming, cert=b"peer-cert"): self.incoming,self.outgoing,self.cert=bytearray(incoming),bytearray(),cert
    def getpeercert(self,binary_form=False): return self.cert if binary_form else {}
    def sendall(self,data): self.outgoing.extend(data)
    def recv(self,size):
        part=bytes(self.incoming[:size]); del self.incoming[:size]; return part
    def close(self): pass
    def shutdown(self,how): pass

def frame(value):
    body=json.dumps(value,sort_keys=True,separators=(",",":")).encode()
    return struct.pack("!I",len(body))+body

def setup_ids():
    local=PeerIdentity("local","A:0,0,0,0","11"*32); cert=b"peer-cert"
    peer=PeerIdentity("peer","A:1,0,0,0",sha256(cert).hexdigest())
    hello={"protocol":PROTOCOL,"node_id":"peer","address_id":peer.address_id,"nonce":"ab"*32}
    return local,peer,cert,hello

class FrameTests(unittest.TestCase):
    def test_socketpair_round_trip(self):
        a,b=socket.socketpair()
        try: send_frame(a,{"ok":True}); self.assertEqual(receive_frame(b),{"ok":True})
        finally: a.close(); b.close()
    def test_oversize_rejected(self):
        a,b=socket.socketpair()
        try:
            with self.assertRaises(ValueError): send_frame(a,{"x":"a"*300},max_bytes=64)
        finally: a.close(); b.close()
    def test_zero_length_rejected(self):
        a,b=socket.socketpair()
        try:
            a.sendall(struct.pack("!I",0))
            with self.assertRaises(ValueError): receive_frame(b)
        finally: a.close(); b.close()
    def test_non_object_rejected(self):
        a,b=socket.socketpair()
        try:
            a.sendall(struct.pack("!I",2)+b"[]")
            with self.assertRaises(ValueError): receive_frame(b)
        finally: a.close(); b.close()

class ReplayTests(unittest.TestCase):
    def test_accept_once(self):
        c=ReplayCache(ttl=10); self.assertTrue(c.accept_once("n",now=1)); self.assertFalse(c.accept_once("n",now=2))
    def test_expiry(self):
        c=ReplayCache(ttl=5); self.assertTrue(c.accept_once("n",now=1)); self.assertTrue(c.accept_once("n",now=7))
    def test_full_cache_fails_closed(self):
        c=ReplayCache(max_entries=2); self.assertTrue(c.accept_once("a")); self.assertTrue(c.accept_once("b"))
        self.assertFalse(c.accept_once("c")); self.assertFalse(c.accept_once("a"))
        self.assertEqual(len(c._items),2)
    def test_bad_limits(self):
        with self.assertRaises(ValueError): ReplayCache(ttl=0)

class SessionTests(unittest.TestCase):
    def test_pinned_identity_handshake(self):
        local,peer,cert,hello=setup_ids(); sock=FakeTLS(frame(hello),cert)
        s=MeshSession(sock,local,{peer.node_id:peer},ReplayCache())
        self.assertEqual(s.establish(),peer); self.assertTrue(sock.outgoing)
    def test_unknown_peer_rejected(self):
        local,peer,cert,hello=setup_ids(); hello["node_id"]="stranger"
        with self.assertRaises(PermissionError): MeshSession(FakeTLS(frame(hello),cert),local,{},ReplayCache()).establish()
    def test_bad_certificate_pin_rejected(self):
        local,peer,cert,hello=setup_ids()
        with self.assertRaises(PermissionError): MeshSession(FakeTLS(frame(hello),b"bad"),local,{peer.node_id:peer},ReplayCache()).establish()
    def test_address_binding_rejected(self):
        local,peer,cert,hello=setup_ids(); hello["address_id"]="B:0,0,0,0"
        with self.assertRaises(PermissionError): MeshSession(FakeTLS(frame(hello),cert),local,{peer.node_id:peer},ReplayCache()).establish()
    def test_expected_peer_id_enforced(self):
        local,peer,cert,hello=setup_ids(); s=MeshSession(FakeTLS(frame(hello),cert),local,{peer.node_id:peer},ReplayCache())
        with self.assertRaises(PermissionError): s.establish(expected_peer_id="other")
    def test_replayed_handshake_nonce_rejected(self):
        local,peer,cert,hello=setup_ids(); cache=ReplayCache()
        MeshSession(FakeTLS(frame(hello),cert),local,{peer.node_id:peer},cache).establish()
        with self.assertRaises(PermissionError): MeshSession(FakeTLS(frame(hello),cert),local,{peer.node_id:peer},cache).establish()
    def test_send_requires_handshake(self):
        local,peer,cert,hello=setup_ids(); s=MeshSession(FakeTLS(b"",cert),local,{peer.node_id:peer},ReplayCache())
        with self.assertRaises(ConnectionError): s.send({"type":"ping"})
    def test_receive_valid_message(self):
        local,peer,cert,hello=setup_ids()
        data={"protocol":PROTOCOL,"sender":"peer","recipient":"local","sequence":1,"message_id":"cd"*16,"payload":{"type":"ping"}}
        s=MeshSession(FakeTLS(frame(hello)+frame(data),cert),local,{peer.node_id:peer},ReplayCache())
        s.establish(); self.assertEqual(s.receive(),{"type":"ping"})
    def test_wrong_recipient_rejected(self):
        local,peer,cert,hello=setup_ids()
        data={"protocol":PROTOCOL,"sender":"peer","recipient":"other","sequence":1,"message_id":"cd"*16,"payload":{}}
        s=MeshSession(FakeTLS(frame(hello)+frame(data),cert),local,{peer.node_id:peer},ReplayCache()); s.establish()
        with self.assertRaises(PermissionError): s.receive()

class ManagerTests(unittest.TestCase):
    def test_disabled_by_default(self):
        local,peer,*_=setup_ids(); self.assertFalse(MeshConnectionManager(local,{peer.node_id:peer}).enabled)
    def test_self_not_remote(self):
        local,*_=setup_ids()
        with self.assertRaises(ValueError): MeshConnectionManager(local,{local.node_id:local})
    def test_registry_key_must_match_identity(self):
        local,peer,*_=setup_ids()
        with self.assertRaises(ValueError): MeshConnectionManager(local,{"alias":peer})

class TLSLoopbackTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("openssl"), "openssl is required for local TLS fixture")
    def test_mutual_tls_loopback_bidirectional_exchange(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            def run(*args): subprocess.run(["openssl",*args],check=True,capture_output=True)
            run("req","-x509","-newkey","rsa:2048","-nodes","-keyout",str(root/"ca.key"),"-out",str(root/"ca.crt"),"-subj","/CN=Paradox-Test-CA","-days","2")
            for name in ("node-a","node-b"):
                run("req","-newkey","rsa:2048","-nodes","-keyout",str(root/f"{name}.key"),"-out",str(root/f"{name}.csr"),"-subj",f"/CN={name}")
                (root/f"{name}.ext").write_text("subjectAltName=DNS:localhost,IP:127.0.0.1\\nextendedKeyUsage=serverAuth,clientAuth\\nkeyUsage=digitalSignature,keyEncipherment\\n")
                run("x509","-req","-in",str(root/f"{name}.csr"),"-CA",str(root/"ca.crt"),"-CAkey",str(root/"ca.key"),"-CAcreateserial","-out",str(root/f"{name}.crt"),"-days","2","-sha256","-extfile",str(root/f"{name}.ext"))
            def identity(name, address):
                der=ssl.PEM_cert_to_DER_cert((root/f"{name}.crt").read_text())
                return PeerIdentity(name,address,sha256(der).hexdigest())
            a,b=identity("node-a","mesh:0,0,0,0"),identity("node-b","mesh:1,0,0,0")
            client_ctx=ssl.create_default_context(ssl.Purpose.SERVER_AUTH,cafile=str(root/"ca.crt"))
            client_ctx.minimum_version=ssl.TLSVersion.TLSv1_3
            client_ctx.load_cert_chain(str(root/"node-a.crt"),str(root/"node-a.key"))
            server_ctx=ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            server_ctx.minimum_version=ssl.TLSVersion.TLSv1_3
            server_ctx.verify_mode=ssl.CERT_REQUIRED
            server_ctx.load_cert_chain(str(root/"node-b.crt"),str(root/"node-b.key"))
            server_ctx.load_verify_locations(cafile=str(root/"ca.crt"))
            listener=socket.socket(); listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            listener.bind(("127.0.0.1",0)); listener.listen(1); listener.settimeout(5)
            result=queue.Queue()
            def serve():
                try:
                    manager=MeshConnectionManager(b,{a.node_id:a},enabled=True,timeout=5)
                    session=manager.accept_one(listener,server_ctx)
                    result.put(session)
                except Exception as exc: result.put(exc)
            thread=threading.Thread(target=serve,daemon=True); thread.start()
            client=None; server=None
            try:
                manager=MeshConnectionManager(a,{b.node_id:b},enabled=True,timeout=5)
                client=manager.connect(b.node_id,"localhost",listener.getsockname()[1],client_ctx)
                server=result.get(timeout=6)
                if isinstance(server,Exception): raise server
                client.send({"kind":"ping","dimension":4})
                self.assertEqual(server.receive(),{"kind":"ping","dimension":4})
                server.send({"kind":"pong","authenticated":True})
                self.assertEqual(client.receive(),{"kind":"pong","authenticated":True})
            finally:
                if client: client.close()
                if server and not isinstance(server,Exception): server.close()
                listener.close(); thread.join(timeout=2)

if __name__ == "__main__": unittest.main()
