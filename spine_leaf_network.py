#!/usr/bin/env python3
"""
Spine-Leaf Data Center Network Topology Generator using NetworkX

This script generates an undirected graph representing a resilient, two-tier 
Spine-Leaf Data Center Network Topology with full mesh connectivity between layers.
"""

import networkx as nx
import matplotlib.pyplot as plt
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Input Variables (Must be defined at the start of the script)
NUM_SPINE = 4               # Total number of Spine Switches (should be even)
NUM_LEAF = 8                # Total number of Leaf Switches (should be even)
NUM_SRV_PER_LEAF = 10       # Number of Servers connected to each Leaf Switch
SPINE_PORT_CAPACITY = 8     # Max ports available on each Spine Switch
LEAF_PORT_CAPACITY = 24     # Max ports available on each Leaf Switch
ACCESS_PORT_CAPACITY = 10   # Reference: Typical max ports for comparison (not used for connectivity limits)

def print_input_parameters():
    """Print all input parameters for verification"""
    print("=" * 70)
    print("SPINE-LEAF NETWORK TOPOLOGY GENERATOR")
    print("=" * 70)
    print("INPUT PARAMETERS")
    print("=" * 70)
    print(f"NUM_SPINE (Spine Switches): {NUM_SPINE}")
    print(f"NUM_LEAF (Leaf Switches): {NUM_LEAF}")
    print(f"NUM_SRV_PER_LEAF (Servers per Leaf Switch): {NUM_SRV_PER_LEAF}")
    print(f"SPINE_PORT_CAPACITY: {SPINE_PORT_CAPACITY}")
    print(f"LEAF_PORT_CAPACITY: {LEAF_PORT_CAPACITY}")
    print(f"ACCESS_PORT_CAPACITY: {ACCESS_PORT_CAPACITY}")
    print("=" * 70)

def validate_constraints():
    """Validate input constraints and exit with fatal error if violated"""
    print("\nCONSTRAINT VALIDATION")
    print("-" * 40)
    
    constraint_violated = False
    
    # Check if NUM_SPINE is even (recommended)
    if NUM_SPINE % 2 != 0:
        logging.warning(f"NUM_SPINE ({NUM_SPINE}) should be an even number for optimal redundancy")
    
    # Check if NUM_LEAF is even (recommended)
    if NUM_LEAF % 2 != 0:
        logging.warning(f"NUM_LEAF ({NUM_LEAF}) should be an even number for optimal redundancy")
    
    # Check spine port capacity constraint: SPINE_PORT_CAPACITY >= NUM_LEAF
    if SPINE_PORT_CAPACITY < NUM_LEAF:
        logging.error(f"FATAL ERROR: SPINE_PORT_CAPACITY ({SPINE_PORT_CAPACITY}) < NUM_LEAF ({NUM_LEAF})")
        logging.error("Each spine switch must have at least NUM_LEAF ports to connect to all leaf switches")
        constraint_violated = True
    else:
        print(f"✓ Spine capacity constraint satisfied: {SPINE_PORT_CAPACITY} >= {NUM_LEAF}")
    
    # Check leaf port capacity constraint: LEAF_PORT_CAPACITY >= NUM_SPINE + NUM_SRV_PER_LEAF
    required_leaf_ports = NUM_SPINE + NUM_SRV_PER_LEAF
    if LEAF_PORT_CAPACITY < required_leaf_ports:
        logging.error(f"FATAL ERROR: LEAF_PORT_CAPACITY ({LEAF_PORT_CAPACITY}) < required ports ({required_leaf_ports})")
        logging.error(f"Each leaf switch needs {NUM_SPINE} ports for spine connections + {NUM_SRV_PER_LEAF} ports for servers")
        constraint_violated = True
    else:
        print(f"✓ Leaf capacity constraint satisfied: {LEAF_PORT_CAPACITY} >= {required_leaf_ports}")
    
    # Check server constraint: NUM_SRV_PER_LEAF <= LEAF_PORT_CAPACITY - NUM_SPINE
    max_servers = LEAF_PORT_CAPACITY - NUM_SPINE
    if NUM_SRV_PER_LEAF > max_servers:
        logging.error(f"FATAL ERROR: NUM_SRV_PER_LEAF ({NUM_SRV_PER_LEAF}) > available leaf ports ({max_servers})")
        logging.error(f"Leaf switches can only support {max_servers} servers after reserving {NUM_SPINE} ports for spine connections")
        constraint_violated = True
    else:
        print(f"✓ Server capacity constraint satisfied: {NUM_SRV_PER_LEAF} <= {max_servers}")
    
    if constraint_violated:
        logging.error("\nCONSTRAINT VALIDATION FAILED!")
        logging.error("Please adjust the input parameters to satisfy all constraints.")
        sys.exit(1)
    
    print("\n✓ All constraints satisfied! Proceeding with network generation...")
    return True

def create_spine_leaf_network():
    """Create the spine-leaf network topology"""
    print("\nNETWORK CONSTRUCTION")
    print("-" * 40)
    
    # Create undirected graph
    G = nx.Graph()
    
    # 1. Create Spine Layer
    print("Creating Spine Layer...")
    spine_switches = [f'spine{i}' for i in range(NUM_SPINE)]
    G.add_nodes_from(spine_switches)
    print(f"✓ Added spine switches: {spine_switches}")
    
    # 2. Create Leaf Layer
    print("Creating Leaf Layer...")
    leaf_switches = [f'leaf{i}' for i in range(NUM_LEAF)]
    G.add_nodes_from(leaf_switches)
    print(f"✓ Added leaf switches: {leaf_switches}")
    
    # 3. Spine-Leaf Full Mesh Connectivity (Northbound)
    print("Creating Spine-Leaf Full Mesh connections...")
    spine_leaf_connections = 0
    
    for spine in spine_switches:
        for leaf in leaf_switches:
            G.add_edge(spine, leaf)
            spine_leaf_connections += 1
    
    print(f"✓ Added {spine_leaf_connections} spine-leaf connections")
    print(f"  - Total links: {NUM_SPINE} × {NUM_LEAF} = {spine_leaf_connections}")
    print(f"  - Spine switch port utilization: {NUM_LEAF} ports per spine switch")
    print(f"  - Leaf switch port utilization: {NUM_SPINE} ports per leaf switch")
    
    # 4. Create Server Layer and Leaf-Server connections
    print("Creating Server Layer and connections...")
    server_count = 0
    leaf_server_connections = 0
    
    for leaf_index in range(NUM_LEAF):
        leaf = f'leaf{leaf_index}'
        
        # Create servers for this leaf switch
        for srv_index in range(NUM_SRV_PER_LEAF):
            srv = f'srv{leaf_index}_{srv_index}'
            G.add_node(srv)
            G.add_edge(leaf, srv)
            server_count += 1
            leaf_server_connections += 1
    
    print(f"✓ Added {server_count} servers")
    print(f"✓ Added {leaf_server_connections} leaf-server connections")
    print(f"  - Servers per leaf switch: {NUM_SRV_PER_LEAF}")
    print(f"  - Total leaf switch port utilization: {NUM_SPINE} (spine) + {NUM_SRV_PER_LEAF} (servers) = {NUM_SPINE + NUM_SRV_PER_LEAF} ports")
    
    return G

def visualize_spine_leaf_network(G):
    """Visualize the spine-leaf network with hierarchical layout and distinct colors/sizes"""
    print("\nVISUALIZATION")
    print("-" * 40)
    
    # Define node colors and sizes
    node_colors = []
    node_sizes = []
    
    for node in G.nodes():
        if node.startswith('spine'):
            node_colors.append('red')      # Spine switches - Red
            node_sizes.append(800)
        elif node.startswith('leaf'):
            node_colors.append('blue')     # Leaf switches - Blue
            node_sizes.append(600)
        elif node.startswith('srv'):
            node_colors.append('green')    # Servers - Green
            node_sizes.append(300)
    
    # Create hierarchical positioning
    pos = create_spine_leaf_layout(G)
    
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
    add_spine_leaf_layer_labels(pos)
    
    # Create legend
    legend_elements = [
        plt.scatter([], [], c='red', s=800, label='Spine Switches (spine)'),
        plt.scatter([], [], c='blue', s=600, label='Leaf Switches (leaf)'),
        plt.scatter([], [], c='green', s=300, label='Servers (srv)')
    ]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    plt.title('Spine-Leaf Data Center Network Topology', fontsize=18, fontweight='bold', pad=20)
    plt.axis('off')  # Remove axes for cleaner look
    plt.tight_layout()
    plt.show()

def create_spine_leaf_layout(G):
    """Create hierarchical positioning for the spine-leaf network topology"""
    pos = {}
    
    # Layer spacing
    layer_spacing = 4
    node_spacing = 2
    
    # Get all nodes and sort them to ensure left-to-right ordering
    spine_nodes = sorted([n for n in G.nodes() if n.startswith('spine')])
    leaf_nodes = sorted([n for n in G.nodes() if n.startswith('leaf')])
    srv_nodes = sorted([n for n in G.nodes() if n.startswith('srv')])
    
    # Calculate maximum width needed for centering (based on widest layer)
    max_nodes_per_layer = max(len(spine_nodes), len(leaf_nodes))
    total_width = (max_nodes_per_layer - 1) * node_spacing
    
    # Layer 1: Spine Switches (top) - centered with left-to-right order
    spine_start_x = (total_width - (len(spine_nodes) - 1) * node_spacing) / 2
    for i, node in enumerate(spine_nodes):
        pos[node] = (spine_start_x + i * node_spacing, 2 * layer_spacing)
    
    # Layer 2: Leaf Switches (middle) - centered with left-to-right order
    leaf_start_x = (total_width - (len(leaf_nodes) - 1) * node_spacing) / 2
    for i, node in enumerate(leaf_nodes):
        pos[node] = (leaf_start_x + i * node_spacing, 1 * layer_spacing)
    
    # Layer 3: Servers (bottom) - grouped under leaf switches with left-to-right order
    # Group servers by their leaf switch
    srv_groups = {}
    for srv in srv_nodes:
        leaf_index = int(srv.split('_')[0].replace('srv', ''))
        if leaf_index not in srv_groups:
            srv_groups[leaf_index] = []
        srv_groups[leaf_index].append(srv)
    
    # Sort server groups by leaf switch index to maintain left-to-right order
    y_srv = 0
    for leaf_index in sorted(srv_groups.keys()):
        # Sort servers within each group to maintain left-to-right order
        group_servers = sorted(srv_groups[leaf_index])
        group_size = len(group_servers)
        
        # Get the x position of the corresponding leaf switch
        leaf_switch_x = leaf_start_x + leaf_index * node_spacing
        
        # Center the server group under the leaf switch
        group_width = (group_size - 1) * (node_spacing * 0.4)
        srv_group_start_x = leaf_switch_x - (group_width / 2)
        
        # Position each server in left-to-right order within the group
        for i, srv in enumerate(group_servers):
            pos[srv] = (srv_group_start_x + i * (node_spacing * 0.4), y_srv)
    
    return pos

def add_spine_leaf_layer_labels(pos):
    """Add layer labels to the spine-leaf visualization"""
    # Find the extent of each layer
    spine_y = max([pos[n][1] for n in pos.keys() if n.startswith('spine')])
    leaf_y = max([pos[n][1] for n in pos.keys() if n.startswith('leaf')])
    srv_y = max([pos[n][1] for n in pos.keys() if n.startswith('srv')])
    
    # Get the overall x extent for positioning labels
    all_x = [pos[n][0] for n in pos.keys()]
    min_x, max_x = min(all_x), max(all_x)
    
    # Position labels to the left of the plot with consistent spacing
    label_x = min_x - 4
    
    # Add layer labels
    plt.text(label_x, spine_y, 'Spine Layer', fontsize=14, fontweight='bold', 
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.7))
    
    plt.text(label_x, leaf_y, 'Leaf Layer', fontsize=14, fontweight='bold',
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
    
    plt.text(label_x, srv_y, 'Server Layer', fontsize=14, fontweight='bold',
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.7))

def print_graph_statistics(G):
    """Print final graph statistics"""
    print("\nGRAPH STATISTICS")
    print("=" * 70)
    print(f"Total Nodes: {G.number_of_nodes()}")
    print(f"Total Edges: {G.number_of_edges()}")
    
    # Count nodes by type
    spine_nodes = [n for n in G.nodes() if n.startswith('spine')]
    leaf_nodes = [n for n in G.nodes() if n.startswith('leaf')]
    server_nodes = [n for n in G.nodes() if n.startswith('srv')]
    
    print(f"\nNode Breakdown:")
    print(f"  Spine Switches (spine): {len(spine_nodes)}")
    print(f"  Leaf Switches (leaf): {len(leaf_nodes)}")
    print(f"  Servers (srv): {len(server_nodes)}")
    
    print(f"\nEdge Breakdown:")
    print(f"  Spine-Leaf edges: {len(spine_nodes) * len(leaf_nodes)}")
    print(f"  Leaf-Server edges: {len([e for e in G.edges() if e[0].startswith('leaf') and e[1].startswith('srv')])}")
    
    print(f"\nNetwork Characteristics:")
    print(f"  Full Mesh Connectivity: Every spine connects to every leaf")
    print(f"  Redundancy: {len(spine_nodes)}-way redundancy between spine and leaf layers")
    print(f"  Scalability: Non-blocking east-west traffic within the fabric")
    print("=" * 70)

def main():
    """Main function to orchestrate the spine-leaf network generation"""
    print_input_parameters()
    
    # Validate constraints (exits if violated)
    validate_constraints()
    
    # Create the network
    G = create_spine_leaf_network()
    
    # Print graph statistics
    print_graph_statistics(G)
    
    # Visualize the network
    visualize_spine_leaf_network(G)

if __name__ == "__main__":
    main()
