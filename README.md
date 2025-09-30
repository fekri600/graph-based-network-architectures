# Resilient 3-Tier Network Topology Generator

This repository contains a Python script for generating and visualizing resilient 3-tier network topologies using NetworkX and matplotlib.

## Features

- **Resilient 3-Tier Architecture**: Core, Aggregation, and Access layers with full redundancy
- **Configurable Parameters**: Easily modify network size and port capacities
- **Constraint Validation**: Automatic validation of port capacity constraints
- **Visual Network Representation**: Color-coded visualization with distinct node types
- **Comprehensive Statistics**: Detailed breakdown of nodes and connections

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip3 install -r requirements.txt
```

## Usage

Simply run the script:

```bash
python3 resilient_3tier_network.py
```

The script will:
1. Display input parameters
2. Validate constraints
3. Generate the network topology
4. Print detailed statistics
5. Display a visual graph of the network

## Network Architecture

### Layers

1. **Core Layer**: 2 core switches (csw0, csw1)
2. **Aggregation Layer**: Configurable number of aggregation switches (asw0, asw1, ...)
3. **Access Layer**: Configurable number of access switches (esw0, esw1, ...)
4. **Endpoint Layer**: PCs connected to each access switch (ep0_0, ep0_1, ...)

### Redundancy

- **Core-Aggregation**: Every aggregation switch connects to both core switches
- **Aggregation-Access**: Access switches are grouped into redundant pairs
- **N+1 Redundancy**: Each ASW pair serves a block of access switches based on port capacity

### Configuration Parameters

| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `NUM_ASW` | Number of Aggregation Switches (must be even) | 6 |
| `NUM_ESW` | Number of Access/Edge Switches | 15 |
| `NUM_PCS_PER_ESW` | PCs per Access Switch | 5 |
| `CORE_PORT_CAPACITY` | Max ports per Core Switch | 24 |
| `AGG_PORT_CAPACITY` | Max ports per Aggregation Switch | 16 |
| `ACCESS_PORT_CAPACITY` | Max ports per Access Switch | 10 |

## Visualization

The generated network is visualized with:
- **Red nodes**: Core switches (large)
- **Blue nodes**: Aggregation switches (medium-large)
- **Green nodes**: Access switches (medium)
- **Orange nodes**: Endpoints (small)

## Example Output

The script generates a network with:
- 98 total nodes (2 core + 6 aggregation + 15 access + 75 endpoints)
- 117 total edges
- Full redundancy at each layer
- Visual representation with color-coded node types

## Requirements

- Python 3.7+
- NetworkX 3.0+
- matplotlib 3.5.0+
