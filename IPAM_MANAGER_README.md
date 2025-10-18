# IPAM_Manager Documentation

## Overview

The `IPAM_Manager` class provides automated IP Address Management (IPAM) and VLAN assignment for NetworkX-based network topologies. It supports **Fat-Tree**, **3-Tier**, and **Spine-Leaf** network architectures.

## Features

- **Automated VLAN Assignment**: Assigns VLANs to switches and network links
- **IP Address Management**: Assigns unique IP addresses from subnet pools using Python's `ipaddress` module
- **Gateway Configuration**: Configures Interface VLANs (SVIs) as gateways on aggregation/spine switches
- **Conflict-Free Assignment**: Ensures no IP address conflicts through systematic tracking
- **Multi-Topology Support**: Works with 3-Tier, Fat-Tree, and Spine-Leaf architectures

## Architecture

### Node Types Supported

#### 3-Tier Topology
- **Core Switches** (`csw0`, `csw1`, ...): Backbone switches
- **Aggregation Switches** (`asw0`, `asw1`, ...): Distribution layer with gateway functionality
- **Access Switches** (`esw0`, `esw1`, ...): Edge layer connecting endpoints
- **Endpoints** (`ep0_0`, `ep0_1`, ...): End devices (PCs, workstations)

#### Fat-Tree Topology
- **Core Switches** (`csw0`, `csw1`, ...): Top-level switches
- **Aggregation Switches** (`asw{pod}_{id}`, ...): Per-pod aggregation with gateway functionality
- **Edge Switches** (`esw{pod}_{id}`, ...): Per-pod edge switches
- **Servers** (`srv{pod}_{edge}_{id}`, ...): Compute servers

#### Spine-Leaf Topology
- **Spine Switches** (`spine0`, `spine1`, ...): Backbone layer with gateway functionality
- **Leaf Switches** (`leaf0`, `leaf1`, ...): Access layer
- **Servers** (`srv{leaf}_{id}`, ...): Compute servers

## Installation

The IPAM_Manager requires only standard Python libraries:

```python
import networkx as nx
import ipaddress
```

Make sure you have NetworkX installed:
```bash
pip install networkx
```

## Quick Start

### Basic Usage

```python
import networkx as nx
from ipam_manager import IPAM_Manager

# 1. Create your network topology using NetworkX
G = nx.Graph()

# Add nodes and edges (example for simple 3-tier)
G.add_nodes_from(['csw0', 'csw1', 'asw0', 'asw1', 'esw0', 'ep0_0', 'ep0_1'])
G.add_edges_from([
    ('csw0', 'asw0'), ('csw1', 'asw0'),
    ('asw0', 'esw0'), ('esw0', 'ep0_0'), ('esw0', 'ep0_1')
])

# 2. Initialize IPAM Manager
ipam = IPAM_Manager(G)

# 3. Assign network attributes
ipam.assign_network_attributes('3-tier')

# 4. Access the configured network
print(G.nodes['asw0'])  # View aggregation switch configuration
print(G.nodes['ep0_0'])  # View endpoint IP configuration
```

### Running with Existing Topologies

```python
from resilient_3tier_network import create_3tier_network
from ipam_manager import IPAM_Manager

# Create network topology
G = create_3tier_network()

# Apply IPAM
ipam = IPAM_Manager(G)
ipam.assign_network_attributes('3-tier')

# Print summary
ipam.print_summary(verbose=True)
```

## API Reference

### Class: `IPAM_Manager`

#### Constructor

```python
IPAM_Manager(graph: nx.Graph)
```

**Parameters:**
- `graph` (nx.Graph): NetworkX graph object representing the network topology

**Example:**
```python
G = nx.Graph()
ipam = IPAM_Manager(G)
```

#### Method: `assign_network_attributes()`

```python
assign_network_attributes(topology_type: str) -> None
```

Main method that assigns all network attributes (VLANs, IPs, gateways) to the graph.

**Parameters:**
- `topology_type` (str): Type of network topology
  - Supported values: `'3-tier'`, `'fat-tree'`, `'spine-leaf'`

**Raises:**
- `ValueError`: If topology_type is not supported

**Example:**
```python
ipam.assign_network_attributes('3-tier')
```

**What it does:**
1. Identifies node types (core, aggregation, spine, leaf, access, endpoints, servers)
2. Assigns VLANs to switches
3. Creates Interface VLANs (SVIs) on aggregation/spine switches
4. Assigns IP addresses to endpoints/servers
5. Sets up default gateways for endpoints/servers

#### Method: `print_summary()`

```python
print_summary(verbose: bool = False) -> None
```

Prints a summary of IPAM assignments.

**Parameters:**
- `verbose` (bool): If True, prints detailed information for all nodes (default: False)

**Example:**
```python
ipam.print_summary(verbose=True)
```

## Node Attributes Assigned

### Switch Nodes (Core, Aggregation, Spine, Leaf, Access, Edge)

All switches receive:
- `vlans_supported` (List[int]): List of VLAN IDs supported by this switch

Aggregation and Spine switches additionally receive:
- `interface_vlan` (int): Interface VLAN (SVI) ID for gateway functionality
- `interface_vlan_gateway` (str): Gateway IP address (e.g., "10.10.0.1")

**Example:**
```python
# Aggregation switch attributes
{
    'vlans_supported': [10, 20, 30],
    'interface_vlan': 10,
    'interface_vlan_gateway': '10.10.0.1'
}

# Access switch attributes
{
    'vlans_supported': [10, 20]
}
```

### Endpoint/Server Nodes

All endpoints and servers receive:
- `ip_address` (str): Assigned IP address (e.g., "10.10.0.5")
- `default_gateway` (str): Default gateway IP address (e.g., "10.10.0.1")
- `vlan_id` (int): VLAN ID this endpoint belongs to
- `subnet` (str): Subnet in CIDR notation (e.g., "10.10.0.0/24")

**Example:**
```python
{
    'ip_address': '10.10.0.5',
    'default_gateway': '10.10.0.1',
    'vlan_id': 10,
    'subnet': '10.10.0.0/24'
}
```

## Edge Attributes Assigned

### Switch-to-Endpoint/Server Links

Links between switches and endpoints/servers receive:
- `vlan_id` (int): VLAN ID for this link

**Example:**
```python
G.edges['esw0', 'ep0_0']['vlan_id']  # Returns: 10
```

## IP Address Allocation

### Subnet Scheme

The IPAM_Manager uses the following subnet allocation scheme:
- Base network: `10.0.0.0/8`
- Per-VLAN subnets: `10.{vlan_id}.0.0/24`
- Gateway IP: First usable IP in subnet (typically `.1`)
- Endpoint IPs: Allocated sequentially starting from `.2`

**Example:**
```
VLAN 10: 10.10.0.0/24
  - Gateway: 10.10.0.1
  - Endpoints: 10.10.0.2, 10.10.0.3, 10.10.0.4, ...

VLAN 11: 10.11.0.0/24
  - Gateway: 10.11.0.1
  - Endpoints: 10.11.0.2, 10.11.0.3, 10.11.0.4, ...
```

### VLAN Pool

Default VLAN pool: VLANs 10-199 (configurable)
- Avoids reserved VLANs (0, 1, 4095)
- Can be extended by modifying `self.vlan_pool` in the constructor

## Examples

### Example 1: 3-Tier Network

```python
from resilient_3tier_network import create_3tier_network
from ipam_manager import IPAM_Manager

# Create network
G = create_3tier_network()

# Apply IPAM
ipam = IPAM_Manager(G)
ipam.assign_network_attributes('3-tier')

# Access configurations
agg_switch = G.nodes['asw0']
print(f"Aggregation Switch Gateway: {agg_switch['interface_vlan_gateway']}")

endpoint = G.nodes['ep0_0']
print(f"Endpoint IP: {endpoint['ip_address']}")
print(f"Endpoint Gateway: {endpoint['default_gateway']}")
```

### Example 2: Spine-Leaf Network

```python
from spine_leaf_network import create_spine_leaf_network
from ipam_manager import IPAM_Manager

# Create network
G = create_spine_leaf_network()

# Apply IPAM
ipam = IPAM_Manager(G)
ipam.assign_network_attributes('spine-leaf')

# Print summary
ipam.print_summary()

# Check server configuration
server = G.nodes['srv0_0']
print(f"Server IP: {server['ip_address']}")
print(f"Server Subnet: {server['subnet']}")
```

### Example 3: Fat-Tree Network

```python
from fat_tree_network import create_fat_tree_network, calculate_topology_counts
from ipam_manager import IPAM_Manager

# Create network
counts = calculate_topology_counts()
G = create_fat_tree_network(counts)

# Apply IPAM
ipam = IPAM_Manager(G)
ipam.assign_network_attributes('fat-tree')

# Verify IP uniqueness
ip_addresses = [G.nodes[n]['ip_address'] for n in G.nodes() if 'ip_address' in G.nodes[n]]
print(f"Total IPs: {len(ip_addresses)}")
print(f"Unique IPs: {len(set(ip_addresses))}")
```

## Testing

Run the comprehensive integration test:

```bash
python3 test_ipam_integration.py
```

This will test IPAM_Manager with all three topology types and verify:
- Successful IPAM assignment
- IP address uniqueness (no conflicts)
- Proper gateway assignment
- VLAN allocation

Run the basic demonstration:

```bash
python3 ipam_manager.py
```

## Configuration

### Customizing VLAN Pool

Modify the VLAN pool in the constructor:

```python
class IPAM_Manager:
    def __init__(self, graph: nx.Graph):
        self.graph = graph
        # Customize VLAN pool (e.g., use VLANs 100-500)
        self.vlan_pool = list(range(100, 501))
        # ... rest of initialization
```

### Customizing Subnet Scheme

Modify the base network and subnet mask:

```python
class IPAM_Manager:
    def __init__(self, graph: nx.Graph):
        self.graph = graph
        # Use 172.16.0.0/12 private range with /16 subnets
        self.base_network = ipaddress.IPv4Network('172.16.0.0/12')
        self.subnet_mask = 16
        # ... rest of initialization
```

## Limitations

1. **Subnet Exhaustion**: Each VLAN uses a /24 subnet (254 usable IPs). For larger deployments, consider:
   - Using larger subnets (e.g., /23, /22)
   - Implementing multiple subnets per VLAN
   - Using hierarchical addressing schemes

2. **VLAN Pool**: Default pool has 190 VLANs (10-199). Extend if needed for very large topologies.

3. **Gateway Assignment**: Currently assigns one gateway per aggregation/spine switch. For redundancy scenarios, consider implementing HSRP/VRRP gateway pairs.

## Troubleshooting

### Issue: "VLAN pool exhausted!"

**Solution:** Increase the VLAN pool size:
```python
self.vlan_pool = list(range(10, 1000))  # Increase upper limit
```

### Issue: "IP address pool exhausted for VLAN X"

**Solution:** Use larger subnets:
```python
self.subnet_mask = 23  # /23 gives 510 usable IPs instead of 254
```

### Issue: No gateway found for endpoints

**Verification:** Ensure the topology has proper switch hierarchy:
- 3-Tier: endpoints → access switches → aggregation switches
- Spine-Leaf: servers → leaf switches → spine switches
- Fat-Tree: servers → edge switches → aggregation switches

## Advanced Usage

### Exporting Configuration

```python
import json

# Export endpoint configurations
endpoint_configs = {}
for node in G.nodes():
    if 'ip_address' in G.nodes[node]:
        endpoint_configs[node] = {
            'ip_address': G.nodes[node]['ip_address'],
            'gateway': G.nodes[node]['default_gateway'],
            'vlan': G.nodes[node]['vlan_id'],
            'subnet': G.nodes[node]['subnet']
        }

# Save to JSON
with open('endpoint_config.json', 'w') as f:
    json.dump(endpoint_configs, f, indent=2)
```

### Generating Configuration Files

```python
# Generate Cisco switch configuration snippet
def generate_cisco_config(G, switch_name):
    attrs = G.nodes[switch_name]
    if 'interface_vlan' in attrs:
        vlan_id = attrs['interface_vlan']
        gateway_ip = attrs['interface_vlan_gateway']
        return f"""
interface Vlan{vlan_id}
 ip address {gateway_ip} 255.255.255.0
 no shutdown
!
        """
    return ""

# Print config for aggregation switches
for node in G.nodes():
    if node.startswith('asw'):
        print(generate_cisco_config(G, node))
```

## License

This code is provided as-is for educational and network automation purposes.

## Contributing

To extend IPAM_Manager for additional features:

1. **Add IPv6 support**: Extend `_create_subnet_for_vlan()` to handle IPv6 networks
2. **Add HSRP/VRRP**: Modify gateway assignment to include virtual IP pairs
3. **Add QoS VLAN tagging**: Extend edge attributes with QoS parameters
4. **Add DNS/DHCP config**: Track DNS/DHCP server assignments per subnet

## References

- [NetworkX Documentation](https://networkx.org/)
- [Python ipaddress Module](https://docs.python.org/3/library/ipaddress.html)
- [VLAN Standards (IEEE 802.1Q)](https://en.wikipedia.org/wiki/IEEE_802.1Q)
- [Fat-Tree Topology](https://en.wikipedia.org/wiki/Fat_tree)
- [Spine-Leaf Architecture](https://en.wikipedia.org/wiki/Spine_and_leaf)

