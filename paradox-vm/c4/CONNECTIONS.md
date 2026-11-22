# C4 Secure Mesh Connections

Opt-in transport for the C4 4D topology. Networking is disabled by default.

## Design
- Logical addresses remain (space_id, x, y, z, w); they are not credentials.
- Each node ID and exact 4D address is pinned to a SHA-256 TLS certificate fingerprint.
- Operator-supplied TLS contexts must enforce TLS 1.3 and mutual certificate verification.
- Client TLS contexts must also enable hostname verification.
- Cross-space routing remains governed by the C4 bridge policy; a certificate does not authorize a bridge or business action.
- Canonical JSON frames use a 4-byte length prefix and a 1 MiB maximum.
- Handshake nonces and message IDs use a bounded TTL replay cache; sequence numbers are monotonic per session.
- There is no 0-RTT application data path. Default connection timeout is 5 seconds (maximum 60).

## Operator setup
Issue one certificate per node through your approved PKI. Keep private keys in an OS secret store or managed PKI; never commit or share them in chat. Provision trusted peer node IDs, address IDs, and certificate fingerprints out-of-band.

Create ssl.SSLContext objects with the local certificate chain and trusted CA loaded. Set minimum_version to ssl.TLSVersion.TLSv1_3; both client and server contexts must use verify_mode = ssl.CERT_REQUIRED. Client contexts must retain check_hostname = True.

Example configuration:

    import ssl
    client_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="ca.pem")
    client_ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    client_ctx.load_cert_chain("node-client.crt", "node-client.key")

    server_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    server_ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    server_ctx.verify_mode = ssl.CERT_REQUIRED
    server_ctx.load_cert_chain("node-server.crt", "node-server.key")
    server_ctx.load_verify_locations(cafile="ca.pem")

Instantiate MeshConnectionManager(local_identity, trusted_peers, enabled=True).
The dialer calls connect(peer_id, host, port, client_ctx). The listener calls
accept_one(listener_socket, server_ctx). Authenticated sessions expose
send({"type": "health_ping"}), receive(), and close().

## Production gates
- Do not expose a listener without firewall policy, connection caps, rate limits, monitoring and DoS controls.
- Certificate issuance, rotation, revocation and identity/address registry updates require an approved PKI process.
- The in-memory replay cache is single-process only. Multi-worker or multi-host deployments need a shared atomic replay store.
- Certificate authentication proves possession under the configured CA and pin; it does not prove a human identity or grant action authority.
- The transport carries JSON data only. It does not execute commands, mutate topology or grant cross-space permissions.
- No certificates, private keys, live peers or remote network data are provisioned here.
- Tests use fake TLS sockets and local socket pairs; they do not prove live connectivity, production PKI correctness or external security review.

## Reproduce
    cd paradox-vm/c4
    python -m unittest -v
