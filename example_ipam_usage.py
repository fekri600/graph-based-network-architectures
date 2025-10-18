#!/usr/bin/env python3
"""
Practical Example: Using IPAM_Manager with Network Visualization and Export

This script demonstrates practical usage of IPAM_Manager including:
1. Creating a network topology
2. Applying IPAM configuration
3. Exporting configuration to JSON
4. Generating sample device configuration snippets
5. Validating the configuration
"""

import networkx as nx
import json
from ipam_manager import IPAM_Manager
from resilient_3tier_network import create_3tier_network


def export_to_json(G, filename='network_ipam_config.json'):
    """
    Export complete IPAM configuration to JSON file.
    
    Args:
        G (nx.Graph): NetworkX graph with IPAM attributes
        filename (str): Output JSON filename
    """
    config = {
        'switches': {},
        'endpoints': {},
        'links': [],
        'vlans': {},
        'statistics': {
            'total_nodes': G.number_of_nodes(),
            'total_edges': G.number_of_edges()
        }
    }
    
    # Extract switch configurations
    for node in G.nodes():
        attrs = G.nodes[node]
        
        if any(node.startswith(prefix) for prefix in ['csw', 'asw', 'esw', 'spine', 'leaf']):
            switch_config = {
                'node_type': 'switch',
                'vlans_supported': attrs.get('vlans_supported', [])
            }
            
            # Add gateway info if present
            if 'interface_vlan' in attrs:
                switch_config['interface_vlan'] = attrs['interface_vlan']
                switch_config['gateway_ip'] = attrs['interface_vlan_gateway']
            
            config['switches'][node] = switch_config
        
        # Extract endpoint/server configurations
        elif any(node.startswith(prefix) for prefix in ['ep', 'srv']):
            endpoint_config = {
                'node_type': 'endpoint' if node.startswith('ep') else 'server',
                'ip_address': attrs.get('ip_address', 'N/A'),
                'default_gateway': attrs.get('default_gateway', 'N/A'),
                'vlan_id': attrs.get('vlan_id', 'N/A'),
                'subnet': attrs.get('subnet', 'N/A')
            }
            
            config['endpoints'][node] = endpoint_config
    
    # Extract link configurations
    for edge in G.edges(data=True):
        node1, node2, attrs = edge
        link_config = {
            'source': node1,
            'destination': node2,
            'vlan_id': attrs.get('vlan_id', None)
        }
        config['links'].append(link_config)
    
    # Collect VLAN information
    vlans_used = set()
    for node in G.nodes():
        if 'vlans_supported' in G.nodes[node]:
            vlans_used.update(G.nodes[node]['vlans_supported'])
    
    for vlan_id in sorted(vlans_used):
        # Find gateway for this VLAN
        gateway = None
        for node in G.nodes():
            if G.nodes[node].get('interface_vlan') == vlan_id:
                gateway = G.nodes[node].get('interface_vlan_gateway')
                break
        
        config['vlans'][str(vlan_id)] = {
            'vlan_id': vlan_id,
            'gateway': gateway,
            'subnet': f'10.{vlan_id}.0.0/24'
        }
    
    # Write to file
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✓ Configuration exported to {filename}")
    return config


def generate_cisco_switch_config(G, switch_name):
    """
    Generate sample Cisco IOS configuration for a switch.
    
    Args:
        G (nx.Graph): NetworkX graph with IPAM attributes
        switch_name (str): Name of the switch node
        
    Returns:
        str: Cisco IOS configuration snippet
    """
    attrs = G.nodes[switch_name]
    config_lines = [f"!\n! Configuration for {switch_name}\n!"]
    
    # VLAN configuration
    vlans = attrs.get('vlans_supported', [])
    if vlans:
        config_lines.append("\n! VLAN Configuration")
        for vlan_id in vlans:
            config_lines.append(f"vlan {vlan_id}")
            config_lines.append(f" name VLAN{vlan_id}")
    
    # Interface VLAN (SVI) configuration
    if 'interface_vlan' in attrs:
        vlan_id = attrs['interface_vlan']
        gateway_ip = attrs['interface_vlan_gateway']
        config_lines.append(f"\n! Interface VLAN (Gateway)")
        config_lines.append(f"interface Vlan{vlan_id}")
        config_lines.append(f" description Gateway for VLAN {vlan_id}")
        config_lines.append(f" ip address {gateway_ip} 255.255.255.0")
        config_lines.append(" no shutdown")
    
    # Access port configuration (for endpoints)
    endpoints_connected = []
    for neighbor in G.neighbors(switch_name):
        if neighbor.startswith('ep') or neighbor.startswith('srv'):
            edge_data = G.edges[switch_name, neighbor]
            vlan_id = edge_data.get('vlan_id', 1)
            endpoints_connected.append((neighbor, vlan_id))
    
    if endpoints_connected:
        config_lines.append("\n! Access Ports Configuration")
        for idx, (endpoint, vlan_id) in enumerate(endpoints_connected):
            port_num = idx + 1
            config_lines.append(f"interface GigabitEthernet1/0/{port_num}")
            config_lines.append(f" description Connected to {endpoint}")
            config_lines.append(" switchport mode access")
            config_lines.append(f" switchport access vlan {vlan_id}")
            config_lines.append(" spanning-tree portfast")
            config_lines.append(" no shutdown")
    
    # Trunk port configuration (for inter-switch links)
    switches_connected = []
    for neighbor in G.neighbors(switch_name):
        if any(neighbor.startswith(prefix) for prefix in ['csw', 'asw', 'esw', 'spine', 'leaf']):
            switches_connected.append(neighbor)
    
    if switches_connected:
        config_lines.append("\n! Trunk Ports Configuration")
        for idx, neighbor in enumerate(switches_connected):
            port_num = len(endpoints_connected) + idx + 1
            config_lines.append(f"interface GigabitEthernet1/0/{port_num}")
            config_lines.append(f" description Uplink to {neighbor}")
            config_lines.append(" switchport mode trunk")
            config_lines.append(" switchport trunk allowed vlan all")
            config_lines.append(" no shutdown")
    
    config_lines.append("!\nend\n")
    return "\n".join(config_lines)


def generate_endpoint_config(G, endpoint_name):
    """
    Generate sample configuration for an endpoint/server.
    
    Args:
        G (nx.Graph): NetworkX graph with IPAM attributes
        endpoint_name (str): Name of the endpoint node
        
    Returns:
        str: Configuration snippet
    """
    attrs = G.nodes[endpoint_name]
    
    config = f"""
# Network Configuration for {endpoint_name}
# ==========================================

IP Address:       {attrs.get('ip_address', 'N/A')}
Subnet Mask:      255.255.255.0
Default Gateway:  {attrs.get('default_gateway', 'N/A')}
VLAN ID:          {attrs.get('vlan_id', 'N/A')}
Subnet:           {attrs.get('subnet', 'N/A')}

# Linux Configuration
# -------------------
# sudo ip addr add {attrs.get('ip_address', 'N/A')}/24 dev eth0
# sudo ip route add default via {attrs.get('default_gateway', 'N/A')}

# Windows Configuration
# ---------------------
# netsh interface ip set address "Ethernet" static {attrs.get('ip_address', 'N/A')} 255.255.255.0 {attrs.get('default_gateway', 'N/A')}
"""
    return config


def validate_configuration(G):
    """
    Validate the IPAM configuration for common issues.
    
    Args:
        G (nx.Graph): NetworkX graph with IPAM attributes
        
    Returns:
        dict: Validation results
    """
    results = {
        'valid': True,
        'warnings': [],
        'errors': [],
        'statistics': {}
    }
    
    # Check 1: All endpoints have IP addresses
    endpoints = [n for n in G.nodes() if n.startswith('ep') or n.startswith('srv')]
    endpoints_with_ip = [n for n in endpoints if 'ip_address' in G.nodes[n]]
    
    if len(endpoints_with_ip) != len(endpoints):
        results['errors'].append(f"{len(endpoints) - len(endpoints_with_ip)} endpoints missing IP addresses")
        results['valid'] = False
    else:
        results['statistics']['endpoints_configured'] = len(endpoints_with_ip)
    
    # Check 2: IP address uniqueness
    ip_addresses = [G.nodes[n]['ip_address'] for n in endpoints_with_ip]
    unique_ips = set(ip_addresses)
    
    if len(ip_addresses) != len(unique_ips):
        duplicates = len(ip_addresses) - len(unique_ips)
        results['errors'].append(f"{duplicates} duplicate IP addresses found!")
        results['valid'] = False
    else:
        results['statistics']['unique_ips'] = len(unique_ips)
    
    # Check 3: All endpoints have gateways
    endpoints_with_gateway = [n for n in endpoints if 'default_gateway' in G.nodes[n]]
    
    if len(endpoints_with_gateway) != len(endpoints):
        results['warnings'].append(f"{len(endpoints) - len(endpoints_with_gateway)} endpoints missing gateway configuration")
    else:
        results['statistics']['endpoints_with_gateway'] = len(endpoints_with_gateway)
    
    # Check 4: Gateway reachability (gateway IPs exist)
    gateway_ips = set(G.nodes[n]['default_gateway'] for n in endpoints_with_gateway)
    configured_gateways = set()
    
    for node in G.nodes():
        if 'interface_vlan_gateway' in G.nodes[node]:
            configured_gateways.add(G.nodes[node]['interface_vlan_gateway'])
    
    missing_gateways = gateway_ips - configured_gateways
    if missing_gateways:
        results['errors'].append(f"Endpoints reference non-existent gateways: {missing_gateways}")
        results['valid'] = False
    
    # Check 5: VLAN usage statistics
    vlans_used = set()
    for node in G.nodes():
        if 'vlans_supported' in G.nodes[node]:
            vlans_used.update(G.nodes[node]['vlans_supported'])
    
    results['statistics']['vlans_used'] = len(vlans_used)
    results['statistics']['vlan_ids'] = sorted(list(vlans_used))
    
    return results


def main():
    """Main function demonstrating IPAM_Manager usage."""
    print("=" * 100)
    print("PRACTICAL IPAM_MANAGER EXAMPLE")
    print("=" * 100)
    
    # Step 1: Create network topology
    print("\n[Step 1] Creating 3-Tier Network Topology...")
    G = create_3tier_network()
    print(f"✓ Network created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Step 2: Apply IPAM configuration
    print("\n[Step 2] Applying IPAM Configuration...")
    ipam = IPAM_Manager(G)
    ipam.assign_network_attributes('3-tier')
    print("✓ IPAM configuration applied")
    
    # Step 3: Validate configuration
    print("\n[Step 3] Validating Configuration...")
    validation = validate_configuration(G)
    
    if validation['valid']:
        print("✓ Configuration is VALID!")
    else:
        print("✗ Configuration has ERRORS!")
    
    if validation['errors']:
        print("\nErrors:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print("\nWarnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    print("\nStatistics:")
    for key, value in validation['statistics'].items():
        print(f"  {key}: {value}")
    
    # Step 4: Export configuration to JSON
    print("\n[Step 4] Exporting Configuration...")
    config = export_to_json(G, 'network_ipam_config.json')
    print(f"  - Switches configured: {len(config['switches'])}")
    print(f"  - Endpoints configured: {len(config['endpoints'])}")
    print(f"  - Links configured: {len(config['links'])}")
    print(f"  - VLANs used: {len(config['vlans'])}")
    
    # Step 5: Generate sample device configurations
    print("\n[Step 5] Generating Sample Device Configurations...")
    
    # Generate config for first aggregation switch
    agg_switches = [n for n in G.nodes() if n.startswith('asw')]
    if agg_switches:
        switch_name = agg_switches[0]
        config_text = generate_cisco_switch_config(G, switch_name)
        
        config_filename = f'{switch_name}_config.txt'
        with open(config_filename, 'w') as f:
            f.write(config_text)
        
        print(f"✓ Generated Cisco config for {switch_name} -> {config_filename}")
        print(f"\nSample configuration preview:")
        print("-" * 80)
        print(config_text[:500] + "...")
    
    # Generate config for first endpoint
    endpoints = [n for n in G.nodes() if n.startswith('ep')]
    if endpoints:
        endpoint_name = endpoints[0]
        endpoint_config = generate_endpoint_config(G, endpoint_name)
        
        endpoint_filename = f'{endpoint_name}_config.txt'
        with open(endpoint_filename, 'w') as f:
            f.write(endpoint_config)
        
        print(f"\n✓ Generated endpoint config for {endpoint_name} -> {endpoint_filename}")
        print(endpoint_config)
    
    # Step 6: Print summary
    print("\n[Step 6] Configuration Summary")
    print("-" * 100)
    ipam.print_summary(verbose=False)
    
    # Step 7: Display sample network information
    print("\n[Step 7] Sample Network Information")
    print("-" * 100)
    
    print("\n📍 Gateway Switches:")
    for node in sorted(G.nodes()):
        if 'interface_vlan_gateway' in G.nodes[node]:
            attrs = G.nodes[node]
            print(f"  {node}:")
            print(f"    VLAN: {attrs['interface_vlan']}, Gateway: {attrs['interface_vlan_gateway']}")
    
    print("\n📍 Sample Endpoints (first 5):")
    for i, node in enumerate(sorted(endpoints)[:5]):
        attrs = G.nodes[node]
        print(f"  {node}: {attrs['ip_address']} (GW: {attrs['default_gateway']}, VLAN: {attrs['vlan_id']})")
    
    print("\n" + "=" * 100)
    print("✓ EXAMPLE COMPLETED SUCCESSFULLY!")
    print("=" * 100)
    print("\nGenerated files:")
    print("  - network_ipam_config.json (Complete configuration)")
    print(f"  - {agg_switches[0]}_config.txt (Cisco switch configuration)")
    print(f"  - {endpoints[0]}_config.txt (Endpoint configuration)")
    print("\nNext steps:")
    print("  1. Review the generated JSON configuration file")
    print("  2. Import configurations to your network management system")
    print("  3. Deploy to network devices")
    print("=" * 100)


if __name__ == "__main__":
    main()

