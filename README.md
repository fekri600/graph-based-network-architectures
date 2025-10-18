# Resilient 3-Tier Network Topology Generator

This repository contains a Python script for generating and visualizing resilient 3-tier network topologies using NetworkX and matplotlib.

## Features

- **Multiple Network Architectures**: 3-Tier, Spine-Leaf, Fat-Tree, and Collapsed Core topologies
- **IP Address Management (IPAM)**: Automated VLAN and IP address assignment with `IPAM_Manager`
- **Resilient Design**: Full redundancy at each layer with N+1 or full mesh connectivity
- **Configurable Parameters**: Easily modify network size and port capacities
- **Constraint Validation**: Automatic validation of port capacity constraints
- **Visual Network Representation**: Color-coded visualization with distinct node types
- **Configuration Export**: Export network configurations to JSON and device-specific formats
- **Comprehensive Statistics**: Detailed breakdown of nodes and connections

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip3 install -r requirements.txt
```

## Usage

### 3-Tier Network Topology
Simply run the script:

```bash
python3 resilient_3tier_network.py
```

### Spine-Leaf Network Topology
Run the spine-leaf topology script:

```bash
python3 spine_leaf_network.py
```

### k-ary Fat-Tree Network Topology
Run the Fat-Tree topology script:

```bash
python3 fat_tree_network.py
```

### Collapsed Core (2-Tier) Network Topology
Run the Collapsed Core topology script:

```bash
python3 collapsed_core_network.py
```

All scripts will:
1. Display input parameters
2. Validate constraints
3. Generate the network topology
4. Print detailed statistics
5. Display a visual graph of the network

## IP Address Management (IPAM)

The `IPAM_Manager` class provides automated IP address and VLAN assignment for all network topologies.

### Using IPAM_Manager

```python
from resilient_3tier_network import create_3tier_network
from ipam_manager import IPAM_Manager

# Create network topology
G = create_3tier_network()

# Apply IPAM configuration
ipam = IPAM_Manager(G)
ipam.assign_network_attributes('3-tier')  # or 'spine-leaf', 'fat-tree'

# Access the configured network
print(G.nodes['asw0'])  # View switch configuration
print(G.nodes['ep0_0'])  # View endpoint IP configuration
```

### IPAM Features

- **Automated VLAN Assignment**: Assigns VLANs to switches and links automatically
- **IP Address Allocation**: Assigns unique IP addresses from managed subnet pools
- **Gateway Configuration**: Configures Interface VLANs (SVIs) on aggregation/spine switches
- **Conflict-Free**: Ensures no IP address conflicts through systematic tracking
- **Configuration Export**: Export to JSON and device-specific configuration formats

### Running IPAM Examples

```bash
# Run basic demonstration
python3 ipam_manager.py

# Run comprehensive integration tests
python3 test_ipam_integration.py

# Run practical example with configuration export
python3 example_ipam_usage.py
```

For detailed documentation, see [IPAM_MANAGER_README.md](IPAM_MANAGER_README.md).

## Network Architectures

### 3-Tier Network Topology

#### Layers
1. **Core Layer**: 2 core switches (csw0, csw1)
2. **Aggregation Layer**: Configurable number of aggregation switches (asw0, asw1, ...)
3. **Access Layer**: Configurable number of access switches (esw0, esw1, ...)
4. **Endpoint Layer**: PCs connected to each access switch (ep0_0, ep0_1, ...)

#### Redundancy
- **Core-Aggregation**: Every aggregation switch connects to both core switches
- **Aggregation-Access**: Access switches are grouped into redundant pairs
- **N+1 Redundancy**: Each ASW pair serves a block of access switches based on port capacity

### Spine-Leaf Network Topology

#### Layers
1. **Spine Layer**: Configurable number of spine switches (spine0, spine1, ...)
2. **Leaf Layer**: Configurable number of leaf switches (leaf0, leaf1, ...)
3. **Server Layer**: Servers connected to each leaf switch (srv0_0, srv0_1, ...)

#### Key Features
- **Full Mesh Connectivity**: Every spine switch connects to every leaf switch
- **Maximum Redundancy**: N-way redundancy between spine and leaf layers
- **Non-blocking Fabric**: Optimal east-west traffic flow
- **Scalable Design**: Easy to add spine or leaf switches

### k-ary Fat-Tree Network Topology

#### Layers
1. **Core Layer**: (k/2)² core switches (csw0, csw1, ...)
2. **Aggregation Layer**: k×(k/2) aggregation switches organized in k pods (asw0_0, asw1_0, ...)
3. **Edge Layer**: k×(k/2) edge switches organized in k pods (esw0_0, esw1_0, ...)
4. **Server Layer**: Servers connected to each edge switch (srv0_0_0, srv0_0_1, ...)

#### Key Features
- **Pod-based Structure**: k pods with k/2 switches each in aggregation and edge layers
- **Non-blocking Connectivity**: Intra-pod and inter-pod connections
- **Hierarchical Routing**: Pod-based routing structure for optimal traffic flow
- **Scalable Design**: Single parameter k defines entire topology size

### Collapsed Core (2-Tier) Network Topology

#### Layers
1. **Collapsed Core Layer**: 2 collapsed core switches (ccsw0, ccsw1)
2. **Edge Layer**: Configurable number of edge switches (esw0, esw1, ...)
3. **Endpoint Layer**: Endpoints connected to each edge switch (ep0_0, ep0_1, ...)

#### Key Features
- **Collapsed Architecture**: Core and aggregation layers combined into single set
- **Full Redundant Mesh**: Every edge switch connects to both core switches
- **Layer 3 Redundancy**: Dual-homed edge switches for high availability
- **Layer 2 Link Aggregation**: vPC/MC-LAG support for bandwidth aggregation
- **Simplified Design**: Two-tier architecture with maximum redundancy

### Configuration Parameters

#### 3-Tier Network Parameters
| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `NUM_ASW` | Number of Aggregation Switches (must be even) | 6 |
| `NUM_ESW` | Number of Access/Edge Switches | 15 |
| `NUM_PCS_PER_ESW` | PCs per Access Switch | 5 |
| `CORE_PORT_CAPACITY` | Max ports per Core Switch | 24 |
| `AGG_PORT_CAPACITY` | Max ports per Aggregation Switch | 16 |
| `ACCESS_PORT_CAPACITY` | Max ports per Access Switch | 10 |

#### Spine-Leaf Network Parameters
| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `NUM_SPINE` | Number of Spine Switches (should be even) | 4 |
| `NUM_LEAF` | Number of Leaf Switches (should be even) | 8 |
| `NUM_SRV_PER_LEAF` | Servers per Leaf Switch | 10 |
| `SPINE_PORT_CAPACITY` | Max ports per Spine Switch | 8 |
| `LEAF_PORT_CAPACITY` | Max ports per Leaf Switch | 24 |
| `ACCESS_PORT_CAPACITY` | Reference max ports | 10 |

#### k-ary Fat-Tree Network Parameters
| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `K_VALUE` | k-ary parameter (must be even) | 4 |
| `NUM_SRV_PER_ESW` | Servers per Edge Switch (≤k/2) | 2 |
| `SWITCH_PORT_CAPACITY` | Ports per switch (≥k) | 16 |

#### Collapsed Core Network Parameters
| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `NUM_CORE_SWITCHES` | Number of Collapsed Core Switches (must be 2) | 2 |
| `NUM_EDGE_SWITCHES` | Number of Edge Switches | 16 |
| `NUM_PCS_PER_ESW` | Endpoints per Edge Switch | 24 |
| `CORE_PORT_CAPACITY` | Max ports per Core Switch (≥NUM_EDGE_SWITCHES) | 32 |
| `EDGE_PORT_CAPACITY` | Max ports per Edge Switch (≥NUM_CORE_SWITCHES+NUM_PCS_PER_ESW) | 48 |

## Visualization

### 3-Tier Network
The generated network is visualized with:
- **Red nodes**: Core switches (large)
- **Blue nodes**: Aggregation switches (medium-large)
- **Green nodes**: Access switches (medium)
- **Orange nodes**: Endpoints (small)

### Spine-Leaf Network
The generated network is visualized with:
- **Red nodes**: Spine switches (large)
- **Blue nodes**: Leaf switches (medium-large)
- **Green nodes**: Servers (small)

### k-ary Fat-Tree Network
The generated network is visualized with:
- **Red nodes**: Core switches (large)
- **Blue nodes**: Aggregation switches (medium-large)
- **Green nodes**: Edge switches (medium)
- **Orange nodes**: Servers (small)

### Collapsed Core Network
The generated network is visualized with:
- **Red nodes**: Collapsed Core switches (large)
- **Blue nodes**: Edge switches (medium-large)
- **Green nodes**: Endpoints (small)

## Example Output

### 3-Tier Network
The script generates a network with:
- 98 total nodes (2 core + 6 aggregation + 15 access + 75 endpoints)
- 117 total edges
- Full redundancy at each layer
- Visual representation with color-coded node types

### Spine-Leaf Network
The script generates a network with:
- 92 total nodes (4 spine + 8 leaf + 80 servers)
- 112 total edges
- Full mesh connectivity between spine and leaf layers
- 4-way redundancy and non-blocking fabric

### k-ary Fat-Tree Network
The script generates a network with:
- 36 total nodes (4 core + 8 aggregation + 8 edge + 16 servers)
- 48 total edges
- Pod-based structure with 4 pods
- Non-blocking connectivity and hierarchical routing

### Collapsed Core Network
The script generates a network with:
- 402 total nodes (2 core + 16 edge + 384 endpoints)
- 416 total edges
- Full redundant mesh between core and edge layers
- Layer 3 redundancy and Layer 2 link aggregation support

## Requirements

- Python 3.7+
- NetworkX 3.0+
- matplotlib 3.5.0+
