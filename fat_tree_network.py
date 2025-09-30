#!/usr/bin/env python3
"""
Classic k-ary Fat-Tree Data Center Network Topology Generator using NetworkX

This script generates an undirected graph representing a Classic three-tier k-ary 
Fat-Tree topology with pod-based structure and non-blocking connectivity.
"""

import networkx as nx
import matplotlib.pyplot as plt
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Input Variables (Must be defined at the start of the script)
K_VALUE = 4                   # The single parameter k defining topology size (must be even)
NUM_SRV_PER_ESW = K_VALUE // 2          # Number of Servers connected to each Edge Switch (must be ≤k/2)
SWITCH_PORT_CAPACITY = K_VALUE    # Ports available on ALL switches (must be ≥k)

def print_input_parameters():
    """Print all input parameters for verification"""
    print("=" * 80)
    print("CLASSIC k-ary FAT-TREE NETWORK TOPOLOGY GENERATOR")
    print("=" * 80)
    print("INPUT PARAMETERS")
    print("=" * 80)
    print(f"K_VALUE: {K_VALUE}")
    print(f"NUM_SRV_PER_ESW: {NUM_SRV_PER_ESW}")
    print(f"SWITCH_PORT_CAPACITY: {SWITCH_PORT_CAPACITY}")
    print("=" * 80)

def validate_constraints():
    """Validate input constraints and exit with fatal error if violated"""
    print("\nCONSTRAINT VALIDATION")
    print("-" * 50)
    
    constraint_violated = False
    
    # Check if K_VALUE is even (critical requirement)
    if K_VALUE % 2 != 0:
        logging.error(f"FATAL ERROR: K_VALUE ({K_VALUE}) must be an even number!")
        logging.error("k-ary Fat-Tree topology requires k to be even for proper pod structure")
        constraint_violated = True
    else:
        print(f"✓ K_VALUE constraint satisfied: {K_VALUE} is even")
    
    # Check switch port capacity constraint: SWITCH_PORT_CAPACITY >= K_VALUE
    if SWITCH_PORT_CAPACITY < K_VALUE:
        logging.error(f"FATAL ERROR: SWITCH_PORT_CAPACITY ({SWITCH_PORT_CAPACITY}) < K_VALUE ({K_VALUE})")
        logging.error("All switches in k-ary Fat-Tree must have at least k ports")
        constraint_violated = True
    else:
        print(f"✓ Switch capacity constraint satisfied: {SWITCH_PORT_CAPACITY} >= {K_VALUE}")
    
    # Check server constraint: NUM_SRV_PER_ESW <= K_VALUE/2
    max_servers = K_VALUE // 2
    if NUM_SRV_PER_ESW > max_servers:
        logging.error(f"FATAL ERROR: NUM_SRV_PER_ESW ({NUM_SRV_PER_ESW}) > K_VALUE/2 ({max_servers})")
        logging.error("Edge switches can only support K_VALUE/2 servers for proper Fat-Tree structure")
        constraint_violated = True
    else:
        print(f"✓ Server capacity constraint satisfied: {NUM_SRV_PER_ESW} <= {max_servers}")
    
    if constraint_violated:
        logging.error("\nCONSTRAINT VALIDATION FAILED!")
        logging.error("Please adjust the input parameters to satisfy all constraints.")
        sys.exit(1)
    
    print("\n✓ All constraints satisfied! Proceeding with Fat-Tree generation...")
    return True

def calculate_topology_counts():
    """Calculate all topology counts based on K_VALUE"""
    print("\nTOPOLOGY CALCULATIONS")
    print("-" * 50)
    
    # Calculate derived counts
    k = K_VALUE
    k_half = k // 2
    
    num_pods = k
    num_core_switches = (k_half) ** 2
    num_agg_per_pod = k_half
    num_edge_per_pod = k_half
    total_agg_switches = k * num_agg_per_pod
    total_edge_switches = k * num_edge_per_pod
    total_servers = total_edge_switches * NUM_SRV_PER_ESW
    
    print(f"Number of Pods: {num_pods}")
    print(f"Core Switches (csw): {num_core_switches}")
    print(f"Aggregation Switches per Pod: {num_agg_per_pod}")
    print(f"Edge Switches per Pod: {num_edge_per_pod}")
    print(f"Total Aggregation Switches: {total_agg_switches}")
    print(f"Total Edge Switches: {total_edge_switches}")
    print(f"Total Servers: {total_servers}")
    
    return {
        'num_pods': num_pods,
        'num_core_switches': num_core_switches,
        'num_agg_per_pod': num_agg_per_pod,
        'num_edge_per_pod': num_edge_per_pod,
        'total_agg_switches': total_agg_switches,
        'total_edge_switches': total_edge_switches,
        'total_servers': total_servers,
        'k_half': k_half
    }

def create_fat_tree_network(counts):
    """Create the k-ary Fat-Tree network topology"""
    print("\nNETWORK CONSTRUCTION")
    print("-" * 50)
    
    # Create undirected graph
    G = nx.Graph()
    
    # Extract counts
    num_pods = counts['num_pods']
    num_core_switches = counts['num_core_switches']
    num_agg_per_pod = counts['num_agg_per_pod']
    num_edge_per_pod = counts['num_edge_per_pod']
    k_half = counts['k_half']
    
    # 1. Create Core Layer
    print("Creating Core Layer...")
    core_switches = [f'csw{i}' for i in range(num_core_switches)]
    G.add_nodes_from(core_switches)
    print(f"✓ Added core switches: {core_switches}")
    
    # 2. Create Aggregation Layer (per pod)
    print("Creating Aggregation Layer...")
    agg_switches = []
    for pod_id in range(num_pods):
        pod_agg_switches = [f'asw{pod_id}_{i}' for i in range(num_agg_per_pod)]
        agg_switches.extend(pod_agg_switches)
        G.add_nodes_from(pod_agg_switches)
        print(f"  Pod {pod_id}: {pod_agg_switches}")
    print(f"✓ Added total aggregation switches: {len(agg_switches)}")
    
    # 3. Create Edge Layer (per pod)
    print("Creating Edge Layer...")
    edge_switches = []
    for pod_id in range(num_pods):
        pod_edge_switches = [f'esw{pod_id}_{i}' for i in range(num_edge_per_pod)]
        edge_switches.extend(pod_edge_switches)
        G.add_nodes_from(pod_edge_switches)
        print(f"  Pod {pod_id}: {pod_edge_switches}")
    print(f"✓ Added total edge switches: {len(edge_switches)}")
    
    # 4. Edge-Aggregation (Intra-Pod) connections
    print("Creating Edge-Aggregation (Intra-Pod) connections...")
    edge_agg_connections = 0
    
    for pod_id in range(num_pods):
        # Get switches for this pod
        pod_edge_switches = [f'esw{pod_id}_{i}' for i in range(num_edge_per_pod)]
        pod_agg_switches = [f'asw{pod_id}_{i}' for i in range(num_agg_per_pod)]
        
        # Every edge switch connects to every aggregation switch in the same pod
        for edge_sw in pod_edge_switches:
            for agg_sw in pod_agg_switches:
                G.add_edge(edge_sw, agg_sw)
                edge_agg_connections += 1
        
        print(f"  Pod {pod_id}: {num_edge_per_pod} edge × {num_agg_per_pod} agg = {num_edge_per_pod * num_agg_per_pod} connections")
    
    print(f"✓ Added {edge_agg_connections} edge-aggregation connections")
    
    # 5. Aggregation-Core (Inter-Pod) connections
    print("Creating Aggregation-Core (Inter-Pod) connections...")
    agg_core_connections = 0
    
    for pod_id in range(num_pods):
        pod_agg_switches = [f'asw{pod_id}_{i}' for i in range(num_agg_per_pod)]
        
        # Each aggregation switch connects to k_half core switches
        # Use pod-based routing: agg switches are split into upper and lower groups
        for agg_index, agg_sw in enumerate(pod_agg_switches):
            # Calculate which core switches this aggregation switch connects to
            # Upper half of agg switches connect to first k_half core switch groups
            # Lower half of agg switches connect to last k_half core switch groups
            
            if agg_index < k_half // 2:  # Upper group
                # Connect to first k_half core switches
                for core_index in range(k_half):
                    core_sw = f'csw{core_index}'
                    G.add_edge(agg_sw, core_sw)
                    agg_core_connections += 1
            else:  # Lower group
                # Connect to last k_half core switches
                for core_index in range(k_half, num_core_switches):
                    core_sw = f'csw{core_index}'
                    G.add_edge(agg_sw, core_sw)
                    agg_core_connections += 1
    
    print(f"✓ Added {agg_core_connections} aggregation-core connections")
    
    # 6. Create Server Layer and Edge-Server connections
    print("Creating Server Layer and connections...")
    server_count = 0
    edge_server_connections = 0
    
    for pod_id in range(num_pods):
        for esw_index in range(num_edge_per_pod):
            edge_sw = f'esw{pod_id}_{esw_index}'
            
            # Create servers for this edge switch
            for srv_index in range(NUM_SRV_PER_ESW):
                srv = f'srv{pod_id}_{esw_index}_{srv_index}'
                G.add_node(srv)
                G.add_edge(edge_sw, srv)
                server_count += 1
                edge_server_connections += 1
    
    print(f"✓ Added {server_count} servers")
    print(f"✓ Added {edge_server_connections} edge-server connections")
    
    return G

def visualize_fat_tree_network(G):
    """Visualize the Fat-Tree network with hierarchical layout and distinct colors/sizes"""
    print("\nVISUALIZATION")
    print("-" * 50)
    
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
            node_colors.append('green')    # Edge switches - Green
            node_sizes.append(400)
        elif node.startswith('srv'):
            node_colors.append('orange')   # Servers - Orange
            node_sizes.append(200)
    
    # Create hierarchical positioning
    pos = create_fat_tree_layout(G)
    
    # Create visualization
    plt.figure(figsize=(24, 16))
    
    # Draw the graph
    nx.draw(G, pos, 
            node_color=node_colors,
            node_size=node_sizes,
            with_labels=True,
            font_size=6,
            font_weight='bold',
            edge_color='gray',
            alpha=0.8,
            width=1.0)
    
    # Add layer labels
    add_fat_tree_layer_labels(pos)
    
    # Create legend
    legend_elements = [
        plt.scatter([], [], c='red', s=800, label='Core Switches (csw)'),
        plt.scatter([], [], c='blue', s=600, label='Aggregation Switches (asw)'),
        plt.scatter([], [], c='green', s=400, label='Edge Switches (esw)'),
        plt.scatter([], [], c='orange', s=200, label='Servers (srv)')
    ]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    plt.title(f'Classic k-ary Fat-Tree Network Topology (k={K_VALUE})', fontsize=18, fontweight='bold', pad=20)
    plt.axis('off')  # Remove axes for cleaner look
    plt.tight_layout()
    plt.show()

def create_fat_tree_layout(G):
    """Create hierarchical positioning for the Fat-Tree network topology with pod structure"""
    pos = {}
    
    # Layer spacing
    layer_spacing = 4
    pod_spacing = 3
    node_spacing = 1.5
    
    # Get all nodes and sort them
    core_nodes = sorted([n for n in G.nodes() if n.startswith('csw')])
    agg_nodes = sorted([n for n in G.nodes() if n.startswith('asw')])
    edge_nodes = sorted([n for n in G.nodes() if n.startswith('esw')])
    srv_nodes = sorted([n for n in G.nodes() if n.startswith('srv')])
    
    # Calculate layout dimensions
    num_pods = K_VALUE
    nodes_per_pod = K_VALUE // 2  # Both agg and edge switches per pod
    
    # Layer 1: Core Switches (top) - centered
    core_start_x = (len(core_nodes) - 1) * node_spacing / 2
    for i, node in enumerate(core_nodes):
        pos[node] = (i * node_spacing - core_start_x, 3 * layer_spacing)
    
    # Layer 2: Aggregation Switches (second from top) - organized by pods
    agg_y = 2 * layer_spacing
    for pod_id in range(num_pods):
        pod_agg_nodes = [n for n in agg_nodes if n.startswith(f'asw{pod_id}_')]
        pod_start_x = (pod_id - num_pods/2) * pod_spacing
        
        for i, node in enumerate(pod_agg_nodes):
            pos[node] = (pod_start_x + i * node_spacing * 0.8, agg_y)
    
    # Layer 3: Edge Switches (third from top) - organized by pods
    edge_y = 1 * layer_spacing
    for pod_id in range(num_pods):
        pod_edge_nodes = [n for n in edge_nodes if n.startswith(f'esw{pod_id}_')]
        pod_start_x = (pod_id - num_pods/2) * pod_spacing
        
        for i, node in enumerate(pod_edge_nodes):
            pos[node] = (pod_start_x + i * node_spacing * 0.8, edge_y)
    
    # Layer 4: Servers (bottom) - grouped under edge switches
    srv_y = 0
    for pod_id in range(num_pods):
        pod_srv_nodes = [n for n in srv_nodes if n.startswith(f'srv{pod_id}_')]
        pod_start_x = (pod_id - num_pods/2) * pod_spacing
        
        # Group servers by edge switch
        srv_groups = {}
        for srv in pod_srv_nodes:
            parts = srv.split('_')
            esw_id = int(parts[1])
            if esw_id not in srv_groups:
                srv_groups[esw_id] = []
            srv_groups[esw_id].append(srv)
        
        # Position servers under their edge switches
        for esw_id in sorted(srv_groups.keys()):
            group_servers = sorted(srv_groups[esw_id])
            group_size = len(group_servers)
            
            # Get the x position of the corresponding edge switch
            edge_switch_x = pod_start_x + esw_id * node_spacing * 0.8
            
            # Center the server group under the edge switch
            group_width = (group_size - 1) * (node_spacing * 0.3)
            srv_group_start_x = edge_switch_x - (group_width / 2)
            
            for i, srv in enumerate(group_servers):
                pos[srv] = (srv_group_start_x + i * (node_spacing * 0.3), srv_y)
    
    return pos

def add_fat_tree_layer_labels(pos):
    """Add layer labels to the Fat-Tree visualization"""
    # Find the extent of each layer
    core_y = max([pos[n][1] for n in pos.keys() if n.startswith('csw')])
    agg_y = max([pos[n][1] for n in pos.keys() if n.startswith('asw')])
    edge_y = max([pos[n][1] for n in pos.keys() if n.startswith('esw')])
    srv_y = max([pos[n][1] for n in pos.keys() if n.startswith('srv')])
    
    # Get the overall x extent for positioning labels
    all_x = [pos[n][0] for n in pos.keys()]
    min_x, max_x = min(all_x), max(all_x)
    
    # Position labels to the left of the plot
    label_x = min_x - 4
    
    # Add layer labels
    plt.text(label_x, core_y, 'Core Layer', fontsize=14, fontweight='bold', 
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.7))
    
    plt.text(label_x, agg_y, 'Aggregation Layer', fontsize=14, fontweight='bold',
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
    
    plt.text(label_x, edge_y, 'Edge Layer', fontsize=14, fontweight='bold',
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.7))
    
    plt.text(label_x, srv_y, 'Server Layer', fontsize=14, fontweight='bold',
             ha='right', va='center', bbox=dict(boxstyle="round,pad=0.3", facecolor='moccasin', alpha=0.7))

def print_graph_statistics(G, counts):
    """Print final graph statistics"""
    print("\nGRAPH STATISTICS")
    print("=" * 80)
    print(f"Total Nodes: {G.number_of_nodes()}")
    print(f"Total Edges: {G.number_of_edges()}")
    
    # Count nodes by type
    core_nodes = [n for n in G.nodes() if n.startswith('csw')]
    agg_nodes = [n for n in G.nodes() if n.startswith('asw')]
    edge_nodes = [n for n in G.nodes() if n.startswith('esw')]
    server_nodes = [n for n in G.nodes() if n.startswith('srv')]
    
    print(f"\nNode Breakdown:")
    print(f"  Core Switches (csw): {len(core_nodes)}")
    print(f"  Aggregation Switches (asw): {len(agg_nodes)}")
    print(f"  Edge Switches (esw): {len(edge_nodes)}")
    print(f"  Servers (srv): {len(server_nodes)}")
    
    print(f"\nEdge Breakdown:")
    edge_agg_edges = len([e for e in G.edges() if (e[0].startswith('esw') and e[1].startswith('asw')) or (e[1].startswith('esw') and e[0].startswith('asw'))])
    agg_core_edges = len([e for e in G.edges() if (e[0].startswith('asw') and e[1].startswith('csw')) or (e[1].startswith('asw') and e[0].startswith('csw'))])
    edge_srv_edges = len([e for e in G.edges() if (e[0].startswith('esw') and e[1].startswith('srv')) or (e[1].startswith('esw') and e[0].startswith('srv'))])
    
    print(f"  Edge-Aggregation edges: {edge_agg_edges}")
    print(f"  Aggregation-Core edges: {agg_core_edges}")
    print(f"  Edge-Server edges: {edge_srv_edges}")
    
    print(f"\nFat-Tree Characteristics:")
    print(f"  k-ary parameter: {K_VALUE}")
    print(f"  Number of Pods: {counts['num_pods']}")
    print(f"  Non-blocking connectivity: Intra-pod and inter-pod")
    print(f"  Pod-based routing structure: {K_VALUE} pods with {K_VALUE//2} switches each")
    print(f"  Scalability: Supports {counts['total_servers']} servers")
    print("=" * 80)

def main():
    """Main function to orchestrate the Fat-Tree network generation"""
    print_input_parameters()
    
    # Validate constraints (exits if violated)
    validate_constraints()
    
    # Calculate topology counts
    counts = calculate_topology_counts()
    
    # Create the network
    G = create_fat_tree_network(counts)
    
    # Print graph statistics
    print_graph_statistics(G, counts)
    
    # Visualize the network
    visualize_fat_tree_network(G)

if __name__ == "__main__":
    main()
