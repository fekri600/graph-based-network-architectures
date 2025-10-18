#!/usr/bin/env python3
"""
Integration Test for IPAM_Manager with Real Network Topologies

This script demonstrates IPAM_Manager usage with actual 3-Tier, Fat-Tree,
and Spine-Leaf network topologies.
"""

import networkx as nx
import sys
from ipam_manager import IPAM_Manager

# Import the network topology generators
from resilient_3tier_network import create_3tier_network
from fat_tree_network import create_fat_tree_network, calculate_topology_counts
from spine_leaf_network import create_spine_leaf_network


def test_3tier_topology():
    """Test IPAM_Manager with a 3-Tier network topology."""
    print("\n" + "=" * 100)
    print("TEST 1: 3-TIER NETWORK TOPOLOGY")
    print("=" * 100)
    
    # Create the 3-tier network
    print("\nCreating 3-Tier network topology...")
    G = create_3tier_network()
    print(f"✓ Created 3-Tier network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Initialize IPAM Manager
    print("\nInitializing IPAM_Manager...")
    ipam = IPAM_Manager(G)
    
    # Assign network attributes
    print("\nAssigning network attributes...")
    ipam.assign_network_attributes('3-tier')
    
    # Print summary
    ipam.print_summary(verbose=False)
    
    # Print sample configurations
    print("\n" + "-" * 100)
    print("SAMPLE CONFIGURATIONS")
    print("-" * 100)
    
    # Show aggregation switch configuration
    agg_switches = [n for n in G.nodes() if n.startswith('asw')]
    if agg_switches:
        agg_switch = agg_switches[0]
        print(f"\nAggregation Switch ({agg_switch}):")
        attrs = G.nodes[agg_switch]
        print(f"  Interface VLAN: {attrs.get('interface_vlan', 'N/A')}")
        print(f"  Gateway IP: {attrs.get('interface_vlan_gateway', 'N/A')}")
        print(f"  VLANs Supported: {attrs.get('vlans_supported', [])}")
    
    # Show access switch configuration
    access_switches = [n for n in G.nodes() if n.startswith('esw')]
    if access_switches:
        access_switch = access_switches[0]
        print(f"\nAccess Switch ({access_switch}):")
        attrs = G.nodes[access_switch]
        print(f"  VLANs Supported: {attrs.get('vlans_supported', [])}")
    
    # Show endpoint configurations (first 3)
    endpoints = [n for n in G.nodes() if n.startswith('ep')][:3]
    print(f"\nEndpoint Configurations (showing first 3 of {len([n for n in G.nodes() if n.startswith('ep')])}):")
    for ep in endpoints:
        attrs = G.nodes[ep]
        print(f"\n  {ep}:")
        print(f"    IP Address: {attrs.get('ip_address', 'N/A')}")
        print(f"    Default Gateway: {attrs.get('default_gateway', 'N/A')}")
        print(f"    VLAN ID: {attrs.get('vlan_id', 'N/A')}")
        print(f"    Subnet: {attrs.get('subnet', 'N/A')}")
    
    return G, ipam


def test_spine_leaf_topology():
    """Test IPAM_Manager with a Spine-Leaf network topology."""
    print("\n" + "=" * 100)
    print("TEST 2: SPINE-LEAF NETWORK TOPOLOGY")
    print("=" * 100)
    
    # Create the spine-leaf network
    print("\nCreating Spine-Leaf network topology...")
    G = create_spine_leaf_network()
    print(f"✓ Created Spine-Leaf network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Initialize IPAM Manager
    print("\nInitializing IPAM_Manager...")
    ipam = IPAM_Manager(G)
    
    # Assign network attributes
    print("\nAssigning network attributes...")
    ipam.assign_network_attributes('spine-leaf')
    
    # Print summary
    ipam.print_summary(verbose=False)
    
    # Print sample configurations
    print("\n" + "-" * 100)
    print("SAMPLE CONFIGURATIONS")
    print("-" * 100)
    
    # Show spine switch configuration
    spine_switches = [n for n in G.nodes() if n.startswith('spine')]
    if spine_switches:
        spine_switch = spine_switches[0]
        print(f"\nSpine Switch ({spine_switch}):")
        attrs = G.nodes[spine_switch]
        print(f"  Interface VLAN: {attrs.get('interface_vlan', 'N/A')}")
        print(f"  Gateway IP: {attrs.get('interface_vlan_gateway', 'N/A')}")
        print(f"  VLANs Supported: {attrs.get('vlans_supported', [])}")
    
    # Show leaf switch configuration
    leaf_switches = [n for n in G.nodes() if n.startswith('leaf')]
    if leaf_switches:
        leaf_switch = leaf_switches[0]
        print(f"\nLeaf Switch ({leaf_switch}):")
        attrs = G.nodes[leaf_switch]
        print(f"  VLANs Supported: {attrs.get('vlans_supported', [])}")
    
    # Show server configurations (first 3)
    servers = [n for n in G.nodes() if n.startswith('srv')][:3]
    print(f"\nServer Configurations (showing first 3 of {len([n for n in G.nodes() if n.startswith('srv')])}):")
    for srv in servers:
        attrs = G.nodes[srv]
        print(f"\n  {srv}:")
        print(f"    IP Address: {attrs.get('ip_address', 'N/A')}")
        print(f"    Default Gateway: {attrs.get('default_gateway', 'N/A')}")
        print(f"    VLAN ID: {attrs.get('vlan_id', 'N/A')}")
        print(f"    Subnet: {attrs.get('subnet', 'N/A')}")
    
    return G, ipam


def test_fat_tree_topology():
    """Test IPAM_Manager with a Fat-Tree network topology."""
    print("\n" + "=" * 100)
    print("TEST 3: FAT-TREE NETWORK TOPOLOGY")
    print("=" * 100)
    
    # Calculate topology counts and create the fat-tree network
    print("\nCreating Fat-Tree network topology...")
    counts = calculate_topology_counts()
    G = create_fat_tree_network(counts)
    print(f"✓ Created Fat-Tree network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Initialize IPAM Manager
    print("\nInitializing IPAM_Manager...")
    ipam = IPAM_Manager(G)
    
    # Assign network attributes
    print("\nAssigning network attributes...")
    ipam.assign_network_attributes('fat-tree')
    
    # Print summary
    ipam.print_summary(verbose=False)
    
    # Print sample configurations
    print("\n" + "-" * 100)
    print("SAMPLE CONFIGURATIONS")
    print("-" * 100)
    
    # Show core switch configuration
    core_switches = [n for n in G.nodes() if n.startswith('csw')]
    if core_switches:
        core_switch = core_switches[0]
        print(f"\nCore Switch ({core_switch}):")
        attrs = G.nodes[core_switch]
        print(f"  VLANs Supported: {attrs.get('vlans_supported', [])}")
    
    # Show aggregation switch configuration (from first pod)
    agg_switches = [n for n in G.nodes() if n.startswith('asw0_')]
    if agg_switches:
        agg_switch = agg_switches[0]
        print(f"\nAggregation Switch ({agg_switch}):")
        attrs = G.nodes[agg_switch]
        print(f"  Interface VLAN: {attrs.get('interface_vlan', 'N/A')}")
        print(f"  Gateway IP: {attrs.get('interface_vlan_gateway', 'N/A')}")
        print(f"  VLANs Supported: {attrs.get('vlans_supported', [])}")
    
    # Show edge switch configuration (from first pod)
    edge_switches = [n for n in G.nodes() if n.startswith('esw0_')]
    if edge_switches:
        edge_switch = edge_switches[0]
        print(f"\nEdge Switch ({edge_switch}):")
        attrs = G.nodes[edge_switch]
        print(f"  VLANs Supported: {attrs.get('vlans_supported', [])}")
    
    # Show server configurations (first 3)
    servers = [n for n in G.nodes() if n.startswith('srv')][:3]
    print(f"\nServer Configurations (showing first 3 of {len([n for n in G.nodes() if n.startswith('srv')])}):")
    for srv in servers:
        attrs = G.nodes[srv]
        print(f"\n  {srv}:")
        print(f"    IP Address: {attrs.get('ip_address', 'N/A')}")
        print(f"    Default Gateway: {attrs.get('default_gateway', 'N/A')}")
        print(f"    VLAN ID: {attrs.get('vlan_id', 'N/A')}")
        print(f"    Subnet: {attrs.get('subnet', 'N/A')}")
    
    return G, ipam


def verify_ip_uniqueness(G, topology_name):
    """Verify that all IP addresses assigned are unique."""
    print(f"\n" + "-" * 100)
    print(f"IP UNIQUENESS VERIFICATION FOR {topology_name}")
    print("-" * 100)
    
    ip_addresses = []
    for node in G.nodes():
        if 'ip_address' in G.nodes[node]:
            ip_addresses.append(G.nodes[node]['ip_address'])
    
    unique_ips = set(ip_addresses)
    total_ips = len(ip_addresses)
    
    print(f"Total IP addresses assigned: {total_ips}")
    print(f"Unique IP addresses: {len(unique_ips)}")
    
    if len(unique_ips) == total_ips:
        print("✓ All IP addresses are unique! No conflicts detected.")
    else:
        print(f"✗ WARNING: {total_ips - len(unique_ips)} IP address conflicts detected!")
        # Find duplicates
        from collections import Counter
        ip_counts = Counter(ip_addresses)
        duplicates = {ip: count for ip, count in ip_counts.items() if count > 1}
        print(f"Duplicate IPs: {duplicates}")
    
    return len(unique_ips) == total_ips


def main():
    """Main function to run all integration tests."""
    print("\n" + "=" * 100)
    print("IPAM_MANAGER INTEGRATION TESTS")
    print("Testing with Real Network Topologies: 3-Tier, Spine-Leaf, and Fat-Tree")
    print("=" * 100)
    
    results = []
    
    # Test 1: 3-Tier Topology
    try:
        G_3tier, ipam_3tier = test_3tier_topology()
        uniqueness_ok = verify_ip_uniqueness(G_3tier, "3-TIER TOPOLOGY")
        results.append(("3-Tier", "PASS" if uniqueness_ok else "FAIL"))
    except Exception as e:
        print(f"\n✗ 3-Tier test failed with error: {e}")
        results.append(("3-Tier", "FAIL"))
    
    # Test 2: Spine-Leaf Topology
    try:
        G_spine_leaf, ipam_spine_leaf = test_spine_leaf_topology()
        uniqueness_ok = verify_ip_uniqueness(G_spine_leaf, "SPINE-LEAF TOPOLOGY")
        results.append(("Spine-Leaf", "PASS" if uniqueness_ok else "FAIL"))
    except Exception as e:
        print(f"\n✗ Spine-Leaf test failed with error: {e}")
        results.append(("Spine-Leaf", "FAIL"))
    
    # Test 3: Fat-Tree Topology
    try:
        G_fat_tree, ipam_fat_tree = test_fat_tree_topology()
        uniqueness_ok = verify_ip_uniqueness(G_fat_tree, "FAT-TREE TOPOLOGY")
        results.append(("Fat-Tree", "PASS" if uniqueness_ok else "FAIL"))
    except Exception as e:
        print(f"\n✗ Fat-Tree test failed with error: {e}")
        results.append(("Fat-Tree", "FAIL"))
    
    # Print final summary
    print("\n" + "=" * 100)
    print("FINAL TEST RESULTS")
    print("=" * 100)
    for topology, result in results:
        status_symbol = "✓" if result == "PASS" else "✗"
        print(f"{status_symbol} {topology}: {result}")
    
    all_passed = all(result == "PASS" for _, result in results)
    
    print("\n" + "=" * 100)
    if all_passed:
        print("ALL TESTS PASSED! ✓")
    else:
        print("SOME TESTS FAILED! ✗")
    print("=" * 100)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

