#!/usr/bin/env python3
"""
Resilient 3-Tier Network Topology Generator using NetworkX

This script generates an undirected graph representing a resilient, 3-Tier Network Topology
with Core, Aggregation, and Access layers, including endpoint connections.
"""

import networkx as nx
import matplotlib.pyplot as plt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Input Variables (Must be defined at the start of the script)
NUM_ASW = 2             # Total number of Aggregation Switches (must be even)
NUM_ESW =  3         # Total number of Access/Edge Switches
NUM_PCS_PER_ESW = 12      # Number of Endpoints connected to each Access Switch
CORE_PORT_CAPACITY = 24  # Max ports available on each Core Switch
AGG_PORT_CAPACITY = 24   # Max ports available on each Aggregation Switch
ACCESS_PORT_CAPACITY = 24 # Max ports available on each Access Switch

def print_input_parameters():
    """Print all input parameters for verification"""
    print("=" * 60)
    print("INPUT PARAMETERS")
    print("=" * 60)
    print(f"NUM_ASW (Aggregation Switches): {NUM_ASW}")
    print(f"NUM_ESW (Access/Edge Switches): {NUM_ESW}")
    print(f"NUM_PCS_PER_ESW (PCs per Access Switch): {NUM_PCS_PER_ESW}")
    print(f"CORE_PORT_CAPACITY: {CORE_PORT_CAPACITY}")
    print(f"AGG_PORT_CAPACITY: {AGG_PORT_CAPACITY}")
    print(f"ACCESS_PORT_CAPACITY: {ACCESS_PORT_CAPACITY}")
    print("=" * 60)

def validate_constraints():
    """Validate input constraints and log warnings if needed"""
    print("\nCONSTRAINT VALIDATION")
    print("-" * 30)
    
    # Check if NUM_ASW is even
    if NUM_ASW % 2 != 0:
        logging.error(f"NUM_ASW ({NUM_ASW}) must be an even number for redundancy pairing!")
        return False
    
    # Check core port capacity constraint
    if NUM_ASW > CORE_PORT_CAPACITY:
        logging.warning(f"NUM_ASW ({NUM_ASW}) > CORE_PORT_CAPACITY ({CORE_PORT_CAPACITY})")
        logging.warning("Proceeding with specified NUM_ASW despite constraint violation")
    else:
        print(f"✓ Core capacity constraint satisfied: {NUM_ASW} <= {CORE_PORT_CAPACITY}")
    
    # Check access port capacity constraint
    if NUM_PCS_PER_ESW > ACCESS_PORT_CAPACITY:
        logging.warning(f"NUM_PCS_PER_ESW ({NUM_PCS_PER_ESW}) > ACCESS_PORT_CAPACITY ({ACCESS_PORT_CAPACITY})")
        logging.warning("Proceeding with specified NUM_PCS_PER_ESW despite constraint violation")
    else:
        print(f"✓ Access capacity constraint satisfied: {NUM_PCS_PER_ESW} <= {ACCESS_PORT_CAPACITY}")
    
    return True

def create_3tier_network():
    """Create the resilient 3-tier network topology"""
    print("\nNETWORK CONSTRUCTION")
    print("-" * 30)
    
    # Create undirected graph
    G = nx.Graph()
    
    # 1. Create Core Layer (2 switches)
    print("Creating Core Layer...")
    core_switches = ['csw0', 'csw1']
    G.add_nodes_from(core_switches)
    print(f"✓ Added core switches: {core_switches}")
    
    # 2. Create Aggregation Layer
    print("Creating Aggregation Layer...")
    aggregation_switches = [f'asw{i}' for i in range(NUM_ASW)]
    G.add_nodes_from(aggregation_switches)
    print(f"✓ Added aggregation switches: {aggregation_switches}")
    
    # 3. Core-Aggregation Layer Redundancy (Northbound)
    print("Creating Core-Aggregation connections...")
    core_connections = 0
    for asw in aggregation_switches:
        # Connect each aggregation switch to both core switches
        G.add_edge(asw, 'csw0')
        G.add_edge(asw, 'csw1')
        core_connections += 2
    
    print(f"✓ Added {core_connections} core-aggregation connections")
    print(f"  - Core switch port utilization: {core_connections//2} ports per core switch")
    
    # 4. Create Access Layer
    print("Creating Access Layer...")
    access_switches = [f'esw{i}' for i in range(NUM_ESW)]
    G.add_nodes_from(access_switches)
    print(f"✓ Added access switches: {access_switches}")
    
    # 5. Aggregation-Access Layer Redundancy (Southbound - CRITICAL LOGIC)
    print("Creating Aggregation-Access connections...")
    agg_access_connections = 0
    
    # Process aggregation switches in pairs
    for pair_index in range(0, NUM_ASW, 2):
        asw1 = f'asw{pair_index}'
        asw2 = f'asw{pair_index + 1}'
        
        # Calculate which access switches this pair serves
        start_esw = pair_index // 2 * AGG_PORT_CAPACITY
        end_esw = min(start_esw + AGG_PORT_CAPACITY, NUM_ESW)
        
        print(f"  ASW Pair {pair_index//2} ({asw1}, {asw2}) serves ESW {start_esw} to {end_esw-1}")
        
        # Connect each access switch in this block to both aggregation switches in the pair
        for esw_index in range(start_esw, end_esw):
            esw = f'esw{esw_index}'
            G.add_edge(esw, asw1)
            G.add_edge(esw, asw2)
            agg_access_connections += 2
    
    print(f"✓ Added {agg_access_connections} aggregation-access connections")
    
    # 6. Create Endpoint Layer and Access-Endpoint connections
    print("Creating Endpoint Layer and connections...")
    endpoint_count = 0
    access_endpoint_connections = 0
    
    for esw_index in range(NUM_ESW):
        esw = f'esw{esw_index}'
        
        # Create endpoints for this access switch
        for pc_index in range(NUM_PCS_PER_ESW):
            ep = f'ep{esw_index}_{pc_index}'
            G.add_node(ep)
            G.add_edge(esw, ep)
            endpoint_count += 1
            access_endpoint_connections += 1
    
    print(f"✓ Added {endpoint_count} endpoints")
    print(f"✓ Added {access_endpoint_connections} access-endpoint connections")
    
    return G

def visualize_network(G):
    """Visualize the network with hierarchical layout and distinct colors/sizes for each node type"""
    print("\nVISUALIZATION")
    print("-" * 30)
    
    # Define node colors and sizes
    node_colors = []
    node_sizes = []
    
    for node in G.nodes():
        if node.startswith('csw'):
            node_colors.append('red')      # Core switches - Red
            node_sizes.append(800)
        elif node.startswith('asw'):
            node_colors.append('blue')     # Aggregation switches - Blue
            node_sizes.append(600)
        elif node.startswith('esw'):
            node_colors.append('green')    # Access switches - Green
            node_sizes.append(400)
        elif node.startswith('ep'):
            node_colors.append('orange')   # Endpoints - Orange
            node_sizes.append(200)
    
    # Create hierarchical positioning
    pos = create_hierarchical_layout(G)
    
    # Create visualization
    plt.figure(figsize=(20, 16))
    
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
    add_layer_labels(pos)
    
    # Create legend
    legend_elements = [
        plt.scatter([], [], c='red', s=800, label='Core Switches (csw)'),
        plt.scatter([], [], c='blue', s=600, label='Aggregation Switches (asw)'),
        plt.scatter([], [], c='green', s=400, label='Access Switches (esw)'),
        plt.scatter([], [], c='orange', s=200, label='Endpoints (ep)')
    ]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    plt.title('Resilient 3-Tier Network Topology - Hierarchical Layout', fontsize=18, fontweight='bold', pad=20)
    plt.axis('off')  # Remove axes for cleaner look
    plt.tight_layout()
    plt.show()

def create_hierarchical_layout(G):
    """Create hierarchical positioning for the network topology with left-to-right ordering"""
    pos = {}
    
    # Layer spacing
    layer_spacing = 3
    node_spacing = 1.5
    
    # Get all nodes and sort them to ensure left-to-right ordering
    core_nodes = sorted([n for n in G.nodes() if n.startswith('csw')])
    agg_nodes = sorted([n for n in G.nodes() if n.startswith('asw')])
    access_nodes = sorted([n for n in G.nodes() if n.startswith('esw')])
    ep_nodes = sorted([n for n in G.nodes() if n.startswith('ep')])
    
    # Calculate maximum width needed for centering (based on widest layer)
    max_nodes_per_layer = max(len(core_nodes), len(agg_nodes), len(access_nodes))
    total_width = (max_nodes_per_layer - 1) * node_spacing
    
    # Layer 1: Core Switches (top) - centered with left-to-right order
    core_start_x = (total_width - (len(core_nodes) - 1) * node_spacing) / 2
    for i, node in enumerate(core_nodes):
        pos[node] = (core_start_x + i * node_spacing, 3 * layer_spacing)
    
    # Layer 2: Aggregation Switches (second from top) - centered with left-to-right order
    agg_start_x = (total_width - (len(agg_nodes) - 1) * node_spacing) / 2
    for i, node in enumerate(agg_nodes):
        pos[node] = (agg_start_x + i * node_spacing, 2 * layer_spacing)
    
    # Layer 3: Access Switches (third from top) - centered with left-to-right order
    access_start_x = (total_width - (len(access_nodes) - 1) * node_spacing) / 2
    for i, node in enumerate(access_nodes):
        pos[node] = (access_start_x + i * node_spacing, 1 * layer_spacing)
    
    # Layer 4: Endpoints (bottom) - grouped under access switches with left-to-right order
    # Group endpoints by their access switch
    ep_groups = {}
    for ep in ep_nodes:
        esw_index = int(ep.split('_')[0].replace('ep', ''))
        if esw_index not in ep_groups:
            ep_groups[esw_index] = []
        ep_groups[esw_index].append(ep)
    
    # Sort endpoint groups by access switch index to maintain left-to-right order
    y_ep = 0
    for esw_index in sorted(ep_groups.keys()):
        # Sort endpoints within each group to maintain left-to-right order
        group_eps = sorted(ep_groups[esw_index])
        group_size = len(group_eps)
        
        # Get the x position of the corresponding access switch
        access_switch_x = access_start_x + esw_index * node_spacing
        
        # Center the endpoint group under the access switch
        group_width = (group_size - 1) * (node_spacing * 0.6)
        ep_group_start_x = access_switch_x - (group_width / 2)
        
        # Position each endpoint in left-to-right order within the group
        for i, ep in enumerate(group_eps):
            pos[ep] = (ep_group_start_x + i * (node_spacing * 0.6), y_ep)
    
    return pos

def add_layer_labels(pos):
    """Add layer labels to the hierarchical visualization"""
    # Find the extent of each layer
    core_y = max([pos[n][1] for n in pos.keys() if n.startswith('csw')])
    agg_y = max([pos[n][1] for n in pos.keys() if n.startswith('asw')])
    access_y = max([pos[n][1] for n in pos.keys() if n.startswith('esw')])
    ep_y = max([pos[n][1] for n in pos.keys() if n.startswith('ep')])
    
    # Get the overall x extent for positioning labels
    all_x = [pos[n][0] for n in pos.keys()]
    min_x, max_x = min(all_x), max(all_x)
    
    # Position labels to the left of the plot with consistent spacing
    label_x = min_x - 3
    
    # Add layer labels
    plt.text(label_x, core_y, 'Core Layer', fontsize=14, fontweight='bold', 
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.7))
    
    plt.text(label_x, agg_y, 'Aggregation Layer', fontsize=14, fontweight='bold',
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
    
    plt.text(label_x, access_y, 'Access Layer', fontsize=14, fontweight='bold',
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.7))
    
    plt.text(label_x, ep_y, 'Endpoint Layer', fontsize=14, fontweight='bold',
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='moccasin', alpha=0.7))

def print_graph_statistics(G):
    """Print final graph statistics"""
    print("\nGRAPH STATISTICS")
    print("=" * 60)
    print(f"Total Nodes: {G.number_of_nodes()}")
    print(f"Total Edges: {G.number_of_edges()}")
    
    # Count nodes by type
    core_nodes = [n for n in G.nodes() if n.startswith('csw')]
    agg_nodes = [n for n in G.nodes() if n.startswith('asw')]
    access_nodes = [n for n in G.nodes() if n.startswith('esw')]
    endpoint_nodes = [n for n in G.nodes() if n.startswith('ep')]
    
    print(f"\nNode Breakdown:")
    print(f"  Core Switches (csw): {len(core_nodes)}")
    print(f"  Aggregation Switches (asw): {len(agg_nodes)}")
    print(f"  Access Switches (esw): {len(access_nodes)}")
    print(f"  Endpoints (ep): {len(endpoint_nodes)}")
    
    print(f"\nEdge Breakdown:")
    print(f"  Core-Aggregation edges: {len(core_nodes) * len(agg_nodes)}")
    print(f"  Aggregation-Access edges: {len([e for e in G.edges() if e[0].startswith('asw') and e[1].startswith('esw')])}")
    print(f"  Access-Endpoint edges: {len([e for e in G.edges() if e[0].startswith('esw') and e[1].startswith('ep')])}")
    
    print("=" * 60)

def main():
    """Main function to orchestrate the network generation"""
    print("RESILIENT 3-TIER NETWORK TOPOLOGY GENERATOR")
    print("=" * 60)
    
    # Print input parameters
    print_input_parameters()
    
    # Validate constraints
    if not validate_constraints():
        print("Constraint validation failed. Exiting.")
        return
    
    # Create the network
    G = create_3tier_network()

    print(G.nodes())
    print(G.edges())
    
    # Print graph statistics
    print_graph_statistics(G)
    
    # Visualize the network
    visualize_network(G)

if __name__ == "__main__":
    main()
