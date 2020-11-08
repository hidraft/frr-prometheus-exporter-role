#!/usr/bin/python3

from prometheus_client import start_http_server, Gauge, Enum, Counter, Summary
import os
import json
import time

bgp_global = {
        "bgp-v4-valid": Gauge("frr_bgp_valid_v4", "Count of Valid IPv4 Prefixes"),
        "bgp-v6-valid": Gauge("frr_bgp_valid_v6", "Count of Valid IPv6 Prefixes"),
        "bgp-peersUp": Gauge("frr_bgp_peersUp", "BGP Peers Up"),
        }

bgp_af = {
        "bgp-peer-pfxRcd": Gauge("frr_bgp_peer_pfxRcd", "BGP Peer Prefixes Received", ["addrfam","peerip","asnum"]),
        "bgp-peer-state": Enum("frr_bgp_peer_state", "BGP Peer State", ["addrfam","peerip","asnum"], states=["Established", "Connect", "Active", "OpenSent", "Idle (Admin)", "Idle"]),
        "bgp-peer-msgRcvd": Gauge("frr_bgp_peer_msgRcvd", "BGP Peer Messages Received", ["addrfam","peerip","asnum"]),
        "bgp-peer-msgSent": Gauge("frr_bgp_peer_msgSent", "BGP Peer Messages Sent", ["addrfam","peerip","asnum"]),
        "bgp-peer-peerUptime": Gauge("frr_bgp_peer_peerUptime", "BGP Peer Uptime", ["addrfam","peerip","asnum"]),
        }

LATENCY = Summary("frr_respose_latency", "A daemon response time")

def getBGPPrefixes():
    cmd = {
           "bgp-v4-valid": "show bgp ipv4 json",
           "bgp-v6-valid": "show bgp ipv6 json",
          }

    for c in cmd:
        print("Running: %s" % (c))
        output = os.popen("vtysh -c \"" + cmd[c] + "\"").read()
        bgp_global[c].set(len(json.loads(output)['routes']))

@LATENCY.time()
def getBGP():
    cmd = "show bgp summary json"
    bgp_gauge_states = ["pfxRcd","msgRcvd","msgSent","peerUptime"]
    bgp_enum_states = ["state"]
    print("Running: %s" % (cmd))
    output = json.loads(os.popen("vtysh -c \"" + cmd + "\"").read())

    for key in bgp_af:
      bgp_af[key]._metrics.clear()

    for af_key, af_value in output.items():
        print("Running in Address Family: %s" % (af_key))
        for peer_key, peer_value in af_value["peers"].items():
            print("  Runing for peer: %s (AS%s)" % (peer_key, peer_value["remoteAs"]))
            peer_value["peerUptime"] = peer_value["peerUptimeMsec"]/1000
            for bgp_gauge_state in bgp_gauge_states:
                bgp_af["bgp-peer-" + bgp_gauge_state].labels(addrfam=af_key, peerip=peer_key, asnum=peer_value["remoteAs"]).set(peer_value[bgp_gauge_state])
            for bgp_enum_state in bgp_enum_states:
                bgp_af["bgp-peer-" + bgp_enum_state].labels(addrfam=af_key, peerip=peer_key, asnum=peer_value["remoteAs"]).state(peer_value[bgp_enum_state])
            if peer_value["state"] == "Established":
                bgp_global["bgp-peersUp"].inc()


if __name__ == "__main__":
    # Start up the server to expose the metrics.
    start_http_server(9144)
    # Generate some requests.
    while True:
        getBGPPrefixes()
        getBGP()
        time.sleep(30)

