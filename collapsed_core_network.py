#!/usr/bin/env python3
"""
Collapsed Core (2-Tier) Data Center Network Topology Generator using NetworkX

This script generates an undirected graph representing a resilient, two-tier 
Collapsed Core topology with full redundancy between core and edge layers.
"""

import networkx as nx
import matplotlib.pyplot as plt
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Input Variables (Must be defined at the start of the script)
NUM_CORE_SWITCHES = 2         # Number of switches in Collapsed Core Layer (must be 2)
NUM_EDGE_SWITCHES = 16        # Total number of Edge (Access) Switches
NUM_PCS_PER_ESW = 24          # Number of Endpoints connected to each Edge Switch
CORE_PORT_CAPACITY = 32       # Max ports available on each Collapsed Core Switch
EDGE_PORT_CAPACITY = 48       # Max ports available on each Edge Switch

def print_input_parameters():
    """Print all input parameters for verification"""
    print("=" * 80)
    print("COLLAPSED CORE (2-TIER) NETWORK TOPOLOGY GENERATOR")
    print("=" * 80)
    print("INPUT PARAMETERS")
    print("=" * 80)
    print(f"NUM_CORE_SWITCHES: {NUM_CORE_SWITCHES}")
    print(f"NUM_EDGE_SWITCHES: {NUM_EDGE_SWITCHES}")
    print(f"NUM_PCS_PER_ESW: {NUM_PCS_PER_ESW}")
    print(f"CORE_PORT_CAPACITY: {CORE_PORT_CAPACITY}")
    print(f"EDGE_PORT_CAPACITY: {EDGE_PORT_CAPACITY}")
    print("=" * 80)

def validate_constraints():
    """Validate input constraints and exit with fatal error if violated"""
    print("\nCONSTRAINT VALIDATION")
    print("-" * 50)
    
    constraint_violated = False
    
    # Check if NUM_CORE_SWITCHES is exactly 2 (critical requirement)
    if NUM_CORE_SWITCHES != 2:
        logging.error(f"FATAL ERROR: NUM_CORE_SWITCHES ({NUM_CORE_SWITCHES}) must be exactly 2!")
        logging.error("Collapsed Core topology requires exactly 2 switches for redundancy")
        constraint_violated = True
    else:
        print(f"✓ Core switches constraint satisfied: {NUM_CORE_SWITCHES} = 2")
    
    # Check core port capacity constraint: CORE_PORT_CAPACITY >= NUM_EDGE_SWITCHES
    if CORE_PORT_CAPACITY < NUM_EDGE_SWITCHES:
        logging.error(f"FATAL ERROR: CORE_PORT_CAPACITY ({CORE_PORT_CAPACITY}) < NUM_EDGE_SWITCHES ({NUM_EDGE_SWITCHES})")
        logging.error("Each collapsed core switch must have at least NUM_EDGE_SWITCHES ports to connect to all edge switches")
        constraint_violated = True
    else:
        print(f"✓ Core capacity constraint satisfied: {CORE_PORT_CAPACITY} >= {NUM_EDGE_SWITCHES}")
    
    # Check edge port capacity constraint: EDGE_PORT_CAPACITY >= NUM_CORE_SWITCHES + NUM_PCS_PER_ESW
    required_edge_ports = NUM_CORE_SWITCHES + NUM_PCS_PER_ESW
    if EDGE_PORT_CAPACITY < required_edge_ports:
        logging.error(f"FATAL ERROR: EDGE_PORT_CAPACITY ({EDGE_PORT_CAPACITY}) < required ports ({required_edge_ports})")
        logging.error(f"Each edge switch needs {NUM_CORE_SWITCHES} ports for core connections + {NUM_PCS_PER_ESW} ports for endpoints")
        constraint_violated = True
    else:
        print(f"✓ Edge capacity constraint satisfied: {EDGE_PORT_CAPACITY} >= {required_edge_ports}")
    
    # Check endpoint constraint: NUM_PCS_PER_ESW <= EDGE_PORT_CAPACITY - NUM_CORE_SWITCHES
    max_endpoints = EDGE_PORT_CAPACITY - NUM_CORE_SWITCHES
    if NUM_PCS_PER_ESW > max_endpoints:
        logging.error(f"FATAL ERROR: NUM_PCS_PER_ESW ({NUM_PCS_PER_ESW}) > available edge ports ({max_endpoints})")
        logging.error(f"Edge switches can only support {max_endpoints} endpoints after reserving {NUM_CORE_SWITCHES} ports for core connections")
        constraint_violated = True
    else:
        print(f"✓ Endpoint capacity constraint satisfied: {NUM_PCS_PER_ESW} <= {max_endpoints}")
    
    if constraint_violated:
        logging.error("\nCONSTRAINT VALIDATION FAILED!")
        logging.error("Please adjust the input parameters to satisfy all constraints.")
        sys.exit(1)
    
    print("\n✓ All constraints satisfied! Proceeding with Collapsed Core generation...")
    return True

def create_collapsed_core_network():
    """Create the Collapsed Core (2-Tier) network topology"""
    print("\nNETWORK CONSTRUCTION")
    print("-" * 50)
    
    # Create undirected graph
    G = nx.Graph()
    
    # 1. Create Collapsed Core Layer
    print("Creating Collapsed Core Layer...")
    core_switches = [f'ccsw{i}' for i in range(NUM_CORE_SWITCHES)]
    G.add_nodes_from(core_switches)
    print(f"✓ Added collapsed core switches: {core_switches}")
    
    # 2. Create Edge Layer
    print("Creating Edge Layer...")
    edge_switches = [f'esw{i}' for i in range(NUM_EDGE_SWITCHES)]
    G.add_nodes_from(edge_switches)
    print(f"✓ Added edge switches: {edge_switches}")
    
    # 3. Core-Edge Redundancy (Full Redundant Mesh)
    print("Creating Core-Edge Full Redundant Mesh connections...")
    core_edge_connections = 0
    
    for core_sw in core_switches:
        for edge_sw in edge_switches:
            G.add_edge(core_sw, edge_sw)
            core_edge_connections += 1
    
    print(f"✓ Added {core_edge_connections} core-edge connections")
    print(f"  - Total links: {NUM_EDGE_SWITCHES} × {NUM_CORE_SWITCHES} = {core_edge_connections}")
    print(f"  - Core switch port utilization: {NUM_EDGE_SWITCHES} ports per core switch")
    print(f"  - Edge switch port utilization: {NUM_CORE_SWITCHES} ports per edge switch")
    
    # 4. Create Endpoint Layer and Edge-Endpoint connections
    print("Creating Endpoint Layer and connections...")
    endpoint_count = 0
    edge_endpoint_connections = 0
    
    for esw_index in range(NUM_EDGE_SWITCHES):
        edge_sw = f'esw{esw_index}'
        
        # Create endpoints for this edge switch
        for pc_index in range(NUM_PCS_PER_ESW):
            ep = f'ep{esw_index}_{pc_index}'
            G.add_node(ep)
            G.add_edge(edge_sw, ep)
            endpoint_count += 1
            edge_endpoint_connections += 1
    
    print(f"✓ Added {endpoint_count} endpoints")
    print(f"✓ Added {edge_endpoint_connections} edge-endpoint connections")
    print(f"  - Endpoints per edge switch: {NUM_PCS_PER_ESW}")
    print(f"  - Total edge switch port utilization: {NUM_CORE_SWITCHES} (core) + {NUM_PCS_PER_ESW} (endpoints) = {NUM_CORE_SWITCHES + NUM_PCS_PER_ESW} ports")
    
    return G

def visualize_collapsed_core_network(G):
    """Visualize the Collapsed Core network with hierarchical layout and distinct colors/sizes"""
    print("\nVISUALIZATION")
    print("-" * 50)
    
    # Define node colors and sizes
    node_colors = []
    node_sizes = []
    
    for node in G.nodes():
        if node.startswith('ccsw'):
            node_colors.append('red')      # Collapsed Core switches - Red
            node_sizes.append(800)
        elif node.startswith('esw'):
            node_colors.append('blue')     # Edge switches - Blue
            node_sizes.append(600)
        elif node.startswith('ep'):
            node_colors.append('green')    # Endpoints - Green
            node_sizes.append(300)
    
    # Create hierarchical positioning
    pos = create_collapsed_core_layout(G)
    
    # Create visualization
    plt.figure(figsize=(20, 12))
    
    # Draw the graph
    nx.draw(G, pos, 
            node_color=node_colors,
            node_size=node_sizes,
            with_labels=True,
            font_size=8,
            font_weight='bold',
            edge_color='gray',
            alpha=0.8,
            width=1.5)
    
    # Add layer labels
    add_collapsed_core_layer_labels(pos)
    
    # Create legend
    legend_elements = [
        plt.scatter([], [], c='red', s=800, label='Collapsed Core Switches (ccsw)'),
        plt.scatter([], [], c='blue', s=600, label='Edge Switches (esw)'),
        plt.scatter([], [], c='green', s=300, label='Endpoints (ep)')
    ]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    plt.title('Collapsed Core (2-Tier) Network Topology', fontsize=18, fontweight='bold', pad=20)
    plt.axis('off')  # Remove axes for cleaner look
    plt.tight_layout()
    plt.show()

def create_collapsed_core_layout(G):
    """Create hierarchical positioning for the Collapsed Core network topology"""
    pos = {}
    
    # Layer spacing
    layer_spacing = 4
    node_spacing = 1.5
    
    # Get all nodes and sort them to ensure left-to-right ordering
    core_nodes = sorted([n for n in G.nodes() if n.startswith('ccsw')])
    edge_nodes = sorted([n for n in G.nodes() if n.startswith('esw')])
    ep_nodes = sorted([n for n in G.nodes() if n.startswith('ep')])
    
    # Calculate maximum width needed for centering (based on widest layer)
    max_nodes_per_layer = max(len(core_nodes), len(edge_nodes))
    total_width = (max_nodes_per_layer - 1) * node_spacing
    
    # Layer 1: Collapsed Core Switches (top) - centered with left-to-right order
    core_start_x = (total_width - (len(core_nodes) - 1) * node_spacing) / 2
    for i, node in enumerate(core_nodes):
        pos[node] = (core_start_x + i * node_spacing, 2 * layer_spacing)
    
    # Layer 2: Edge Switches (middle) - centered with left-to-right order
    edge_start_x = (total_width - (len(edge_nodes) - 1) * node_spacing) / 2
    for i, node in enumerate(edge_nodes):
        pos[node] = (edge_start_x + i * node_spacing, 1 * layer_spacing)
    
    # Layer 3: Endpoints (bottom) - grouped under edge switches with left-to-right order
    # Group endpoints by their edge switch
    ep_groups = {}
    for ep in ep_nodes:
        esw_index = int(ep.split('_')[0].replace('ep', ''))
        if esw_index not in ep_groups:
            ep_groups[esw_index] = []
        ep_groups[esw_index].append(ep)
    
    # Sort endpoint groups by edge switch index to maintain left-to-right order
    y_ep = 0
    for esw_index in sorted(ep_groups.keys()):
        # Sort endpoints within each group to maintain left-to-right order
        group_eps = sorted(ep_groups[esw_index])
        group_size = len(group_eps)
        
        # Get the x position of the corresponding edge switch
        edge_switch_x = edge_start_x + esw_index * node_spacing
        
        # Center the endpoint group under the edge switch
        group_width = (group_size - 1) * (node_spacing * 0.3)
        ep_group_start_x = edge_switch_x - (group_width / 2)
        
        # Position each endpoint in left-to-right order within the group
        for i, ep in enumerate(group_eps):
            pos[ep] = (ep_group_start_x + i * (node_spacing * 0.3), y_ep)
    
    return pos

def add_collapsed_core_layer_labels(pos):
    """Add layer labels to the Collapsed Core visualization"""
    # Find the extent of each layer
    core_y = max([pos[n][1] for n in pos.keys() if n.startswith('ccsw')])
    edge_y = max([pos[n][1] for n in pos.keys() if n.startswith('esw')])
    ep_y = max([pos[n][1] for n in pos.keys() if n.startswith('ep')])
    
    # Get the overall x extent for positioning labels
    all_x = [pos[n][0] for n in pos.keys()]
    min_x, max_x = min(all_x), max(all_x)
    
    # Position labels to the left of the plot with consistent spacing
    label_x = min_x - 4
    
    # Add layer labels
    plt.text(label_x, core_y, 'Collapsed Core Layer', fontsize=14, fontweight='bold', 
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.7))
    
    plt.text(label_x, edge_y, 'Edge Layer', fontsize=14, fontweight='bold',
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
    
    plt.text(label_x, ep_y, 'Endpoint Layer', fontsize=14, fontweight='bold',
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.7))

def print_graph_statistics(G):
    """Print final graph statistics"""
    print("\nGRAPH STATISTICS")
    print("=" * 80)
    print(f"Total Nodes: {G.number_of_nodes()}")
    print(f"Total Edges: {G.number_of_edges()}")
    
    # Count nodes by type
    core_nodes = [n for n in G.nodes() if n.startswith('ccsw')]
    edge_nodes = [n for n in G.nodes() if n.startswith('esw')]
    endpoint_nodes = [n for n in G.nodes() if n.startswith('ep')]
    
    print(f"\nNode Breakdown:")
    print(f"  Collapsed Core Switches (ccsw): {len(core_nodes)}")
    print(f"  Edge Switches (esw): {len(edge_nodes)}")
    print(f"  Endpoints (ep): {len(endpoint_nodes)}")
    
    print(f"\nEdge Breakdown:")
    core_edge_edges = len([e for e in G.edges() if (e[0].startswith('ccsw') and e[1].startswith('esw')) or (e[1].startswith('ccsw') and e[0].startswith('esw'))])
    edge_ep_edges = len([e for e in G.edges() if (e[0].startswith('esw') and e[1].startswith('ep')) or (e[1].startswith('esw') and e[0].startswith('ep'))])
    
    print(f"  Core-Edge edges: {core_edge_edges}")
    print(f"  Edge-Endpoint edges: {edge_ep_edges}")
    
    print(f"\nCollapsed Core Characteristics:")
    print(f"  Core Switches: {NUM_CORE_SWITCHES} (fixed for redundancy)")
    print(f"  Edge Switches: {NUM_EDGE_SWITCHES} (configurable)")
    print(f"  Full Redundant Mesh: Every edge connects to every core")
    print(f"  Layer 3 Redundancy: Dual-homed edge switches")
    print(f"  Layer 2 Link Aggregation: vPC/MC-LAG support")
    print(f"  Scalability: Supports {len(endpoint_nodes)} endpoints")
    print("=" * 80)

def main():
    """Main function to orchestrate the Collapsed Core network generation"""
    print_input_parameters()
    
    # Validate constraints (exits if violated)
    validate_constraints()
    
    # Create the network
    G = create_collapsed_core_network()
    
    # Print graph statistics
    print_graph_statistics(G)
    
    # Visualize the network
    visualize_collapsed_core_network(G)

if __name__ == "__main__":
    main()
