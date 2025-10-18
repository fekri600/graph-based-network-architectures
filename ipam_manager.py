#!/usr/bin/env python3
"""
IPAM_Manager: IP Address Management and VLAN Assignment for Network Topologies

This module provides automated IP address and VLAN assignment functionality for
NetworkX-based network topologies, specifically supporting Fat-Tree, 3-Tier,
and Spine-Leaf architectures.
"""

import networkx as nx
import ipaddress
from typing import Dict, List, Set, Optional
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class IPAM_Manager:
    """
    IP Address Management (IPAM) and VLAN assignment manager for network topologies.
    
    This class handles the assignment of:
    - VLAN IDs to switches and links
    - Interface VLANs (SVIs) as gateways for aggregation/spine switches
    - IP addresses and default gateways to endpoint devices
    
    Supports: Fat-Tree, 3-Tier, and Spine-Leaf network architectures.
    """
    
    def __init__(self, graph: nx.Graph, vlan_list: List[int] = None, 
                 pc_distribution: str = 'single', endpoint_vlans: List[int] = None,
                 unique_switch_vlans: bool = True, reserved_ips: Dict[int, List[str]] = None):
        """
        Initialize the IPAM Manager with a NetworkX graph.
        
        Args:
            graph (nx.Graph): NetworkX graph representing the network topology
            vlan_list (List[int], optional): Custom list of VLAN IDs to use. 
                                            If None, uses default pool (10-199)
            pc_distribution (str): Distribution strategy for endpoints ('single', 'equal', 'random')
            endpoint_vlans (List[int], optional): Specific VLANs for endpoint distribution
            unique_switch_vlans (bool): If True, each switch gets unique VLAN. If False, switches share VLANs.
            reserved_ips (Dict[int, List[str]], optional): Reserved IPs per VLAN
                                                          Format: {vlan_id: ['10.10.0.2', '10.10.0.100']}
        """
        self.graph = graph
        
        # VLAN ID pool (VLANs 10-4094 are available, avoiding reserved VLANs)
        if vlan_list is not None:
            self.vlan_pool = vlan_list.copy()  # Use custom VLAN list
        else:
            self.vlan_pool = list(range(10, 200))  # Default: VLANs 10-199
        self.vlan_index = 0
        
        # Switch VLAN configuration
        self.unique_switch_vlans = unique_switch_vlans
        self.shared_vlans = {}  # Cache for shared VLANs by switch type
        
        # PC distribution configuration
        self.pc_distribution = pc_distribution
        self.endpoint_vlans = endpoint_vlans.copy() if endpoint_vlans else None
        self.endpoint_vlan_assignments = {}  # Track which VLANs are used for endpoints
        
        # Reserved IP addresses
        self.reserved_ips = reserved_ips if reserved_ips else {}
        self.reserved_ip_set = {}  # Parsed reserved IPs per VLAN as sets
        self._parse_reserved_ips()
        
        # IP subnet pool - Using /24 subnets from 10.0.0.0/8 private range
        # Each VLAN gets its own /24 subnet
        self.base_network = ipaddress.IPv4Network('10.0.0.0/8')
        self.subnet_mask = 24  # /24 subnets
        
        # Tracking structures
        self.vlan_to_subnet: Dict[int, ipaddress.IPv4Network] = {}
        self.vlan_to_gateway: Dict[int, ipaddress.IPv4Address] = {}
        self.subnet_ip_tracker: Dict[int, int] = {}  # VLAN -> next available IP index
        
        # Track which VLANs are assigned to which switches
        self.switch_vlans: Dict[str, List[int]] = {}
        
        logging.info(f"IPAM_Manager initialized with {self.graph.number_of_nodes()} nodes "
                     f"and {self.graph.number_of_edges()} edges")
        
        if self.reserved_ips:
            logging.info(f"Reserved IPs configured for VLANs: {list(self.reserved_ips.keys())}")
    
    def _parse_reserved_ips(self):
        """
        Parse reserved IP addresses from string format to IPv4Address sets.
        Supports single IPs and ranges (e.g., '10.10.0.10-10.10.0.20').
        """
        for vlan_id, ip_list in self.reserved_ips.items():
            if vlan_id not in self.reserved_ip_set:
                self.reserved_ip_set[vlan_id] = set()
            
            for ip_spec in ip_list:
                if '-' in ip_spec:
                    # IP range: '10.10.0.10-10.10.0.20'
                    try:
                        start_ip, end_ip = ip_spec.split('-')
                        start_addr = ipaddress.IPv4Address(start_ip.strip())
                        end_addr = ipaddress.IPv4Address(end_ip.strip())
                        
                        # Add all IPs in the range
                        current = start_addr
                        while current <= end_addr:
                            self.reserved_ip_set[vlan_id].add(current)
                            current += 1
                        
                        logging.debug(f"Reserved IP range {ip_spec} in VLAN {vlan_id}")
                    except Exception as e:
                        logging.warning(f"Invalid IP range format '{ip_spec}': {e}")
                else:
                    # Single IP: '10.10.0.2'
                    try:
                        ip_addr = ipaddress.IPv4Address(ip_spec.strip())
                        self.reserved_ip_set[vlan_id].add(ip_addr)
                        logging.debug(f"Reserved IP {ip_addr} in VLAN {vlan_id}")
                    except Exception as e:
                        logging.warning(f"Invalid IP address '{ip_spec}': {e}")
    
    def _is_ip_reserved(self, vlan_id: int, ip_addr: ipaddress.IPv4Address) -> bool:
        """
        Check if an IP address is reserved in a VLAN.
        
        Args:
            vlan_id (int): VLAN ID
            ip_addr (ipaddress.IPv4Address): IP address to check
            
        Returns:
            bool: True if IP is reserved, False otherwise
        """
        if vlan_id in self.reserved_ip_set:
            return ip_addr in self.reserved_ip_set[vlan_id]
        return False
    
    def _get_next_vlan(self) -> int:
        """
        Get the next available VLAN ID from the pool.
        
        Returns:
            int: Next available VLAN ID
        """
        if self.vlan_index >= len(self.vlan_pool):
            raise ValueError("VLAN pool exhausted! Increase VLAN pool size.")
        
        vlan_id = self.vlan_pool[self.vlan_index]
        self.vlan_index += 1
        return vlan_id
    
    def _get_vlan_for_switch_type(self, switch_type: str) -> int:
        """
        Get a VLAN for a switch, either unique or shared based on configuration.
        
        Args:
            switch_type (str): Type of switch ('core', 'aggregation', 'access', 'spine', 'leaf', 'edge')
            
        Returns:
            int: VLAN ID for this switch
        """
        if self.unique_switch_vlans:
            # Each switch gets its own VLAN
            return self._get_next_vlan()
        else:
            # All switches share VLANs - use 'all' as the key so everyone shares
            if 'all' not in self.shared_vlans:
                self.shared_vlans['all'] = self._get_next_vlan()
            return self.shared_vlans['all']
    
    def _create_subnet_for_vlan(self, vlan_id: int) -> ipaddress.IPv4Network:
        """
        Create and assign a unique /24 subnet for a given VLAN.
        
        Args:
            vlan_id (int): VLAN ID to assign subnet to
            
        Returns:
            ipaddress.IPv4Network: Assigned subnet
        """
        if vlan_id in self.vlan_to_subnet:
            return self.vlan_to_subnet[vlan_id]
        
        # Create subnet: 10.{vlan_id}.0.0/24
        # This ensures each VLAN gets a unique subnet
        subnet = ipaddress.IPv4Network(f'10.{vlan_id}.0.0/{self.subnet_mask}')
        self.vlan_to_subnet[vlan_id] = subnet
        
        # Initialize IP tracker for this subnet (start from .1, .1 will be gateway)
        self.subnet_ip_tracker[vlan_id] = 1
        
        logging.debug(f"Created subnet {subnet} for VLAN {vlan_id}")
        return subnet
    
    def _get_gateway_for_vlan(self, vlan_id: int) -> ipaddress.IPv4Address:
        """
        Get or create the gateway IP address for a VLAN (typically .1 of the subnet).
        
        Args:
            vlan_id (int): VLAN ID
            
        Returns:
            ipaddress.IPv4Address: Gateway IP address
        """
        if vlan_id in self.vlan_to_gateway:
            return self.vlan_to_gateway[vlan_id]
        
        # Ensure subnet exists
        subnet = self._create_subnet_for_vlan(vlan_id)
        
        # Gateway is typically the first usable IP (.1)
        gateway = list(subnet.hosts())[0]
        self.vlan_to_gateway[vlan_id] = gateway
        
        # Update IP tracker to skip gateway IP
        self.subnet_ip_tracker[vlan_id] = 2  # Next IP will be .2
        
        logging.debug(f"Assigned gateway {gateway} for VLAN {vlan_id}")
        return gateway
    
    def _get_unique_ip_for_vlan(self, vlan_id: int) -> ipaddress.IPv4Address:
        """
        Get a unique IP address from a VLAN's subnet (for switch management IPs).
        Each call returns the next available IP in sequence.
        
        Args:
            vlan_id (int): VLAN ID
            
        Returns:
            ipaddress.IPv4Address: Unique IP address from the VLAN's subnet
        """
        # Ensure subnet exists and gateway is reserved
        if vlan_id not in self.vlan_to_subnet:
            self._create_subnet_for_vlan(vlan_id)
        
        if vlan_id not in self.vlan_to_gateway:
            self._get_gateway_for_vlan(vlan_id)
        
        # Get the next available IP
        return self._get_next_ip_for_vlan(vlan_id)
    
    def _get_next_ip_for_vlan(self, vlan_id: int) -> ipaddress.IPv4Address:
        """
        Get the next available IP address from a VLAN's subnet, skipping reserved IPs.
        
        Args:
            vlan_id (int): VLAN ID
            
        Returns:
            ipaddress.IPv4Address: Next available IP address
        """
        subnet = self.vlan_to_subnet[vlan_id]
        host_list = list(subnet.hosts())
        
        current_index = self.subnet_ip_tracker[vlan_id]
        
        # Find the next non-reserved IP
        while current_index < len(host_list):
            ip_address = host_list[current_index]
            
            # Check if this IP is reserved
            if not self._is_ip_reserved(vlan_id, ip_address):
                # IP is not reserved, use it
                self.subnet_ip_tracker[vlan_id] = current_index + 1
                return ip_address
            
            # IP is reserved, skip it
            logging.debug(f"Skipping reserved IP {ip_address} in VLAN {vlan_id}")
            current_index += 1
        
        # No available IPs left
        raise ValueError(f"IP address pool exhausted for VLAN {vlan_id} subnet {subnet} "
                        f"(including reserved IPs)")
    
    def _identify_node_types(self) -> Dict[str, List[str]]:
        """
        Identify and categorize nodes in the graph by their type/role.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping node types to lists of node names
        """
        node_types = {
            'core': [],
            'aggregation': [],
            'spine': [],
            'leaf': [],
            'access': [],
            'edge': [],
            'endpoint': [],
            'server': []
        }
        
        for node in self.graph.nodes():
            if node.startswith('csw'):
                node_types['core'].append(node)
            elif node.startswith('asw'):
                node_types['aggregation'].append(node)
            elif node.startswith('spine'):
                node_types['spine'].append(node)
            elif node.startswith('leaf'):
                node_types['leaf'].append(node)
            elif node.startswith('esw'):
                # In 3-tier: esw = access switch, in Fat-Tree: esw = edge switch
                node_types['access'].append(node)
                node_types['edge'].append(node)
            elif node.startswith('ep'):
                node_types['endpoint'].append(node)
            elif node.startswith('srv'):
                node_types['server'].append(node)
        
        return node_types
    
    def _assign_vlans_to_switches(self, node_types: Dict[str, List[str]], 
                                   topology_type: str) -> None:
        """
        Assign VLAN IDs to switch nodes based on topology type.
        
        Args:
            node_types (Dict[str, List[str]]): Categorized node types
            topology_type (str): Type of topology ('3-tier', 'fat-tree', 'spine-leaf')
        """
        logging.info(f"Assigning VLANs to switches for {topology_type} topology...")
        
        if topology_type == '3-tier':
            # Core switches: assign Interface VLAN for management/routing
            for core in node_types['core']:
                self.switch_vlans[core] = []
                self.graph.nodes[core]['vlans_supported'] = []
                
                # Assign Interface VLAN (SVI) for management/routing functionality
                interface_vlan = self._get_vlan_for_switch_type('core')
                # Core switches get unique management IPs (not gateway)
                mgmt_ip = self._get_unique_ip_for_vlan(interface_vlan)
                self.graph.nodes[core]['interface_vlan'] = interface_vlan
                self.graph.nodes[core]['interface_vlan_ip'] = str(mgmt_ip)
                self.switch_vlans[core].append(interface_vlan)
                logging.debug(f"{core}: Interface VLAN {interface_vlan}, IP {mgmt_ip}")
            
            # Aggregation switches: each gets a set of VLANs and an Interface VLAN
            for agg in node_types['aggregation']:
                self.switch_vlans[agg] = []
                self.graph.nodes[agg]['vlans_supported'] = []
                
                # Assign Interface VLAN (SVI) for gateway functionality
                interface_vlan = self._get_vlan_for_switch_type('aggregation')
                # Reserve the gateway IP (.1) but don't assign it to any switch
                # Each aggregation switch gets its own unique IP
                if interface_vlan not in self.vlan_to_gateway:
                    self._get_gateway_for_vlan(interface_vlan)  # Reserve .1 as virtual gateway
                agg_ip = self._get_unique_ip_for_vlan(interface_vlan)
                gateway_reserved = str(self.vlan_to_gateway[interface_vlan])
                
                self.graph.nodes[agg]['interface_vlan'] = interface_vlan
                self.graph.nodes[agg]['interface_vlan_ip'] = str(agg_ip)
                self.graph.nodes[agg]['interface_vlan_gateway'] = gateway_reserved
                self.switch_vlans[agg].append(interface_vlan)
                logging.debug(f"{agg}: Interface VLAN {interface_vlan}, IP {agg_ip}, Virtual Gateway {gateway_reserved}")
            
            # Access switches: assign Interface VLAN for management and support VLANs for connected endpoints
            for access in node_types['access']:
                self.switch_vlans[access] = []
                self.graph.nodes[access]['vlans_supported'] = []
                
                # Assign Interface VLAN (SVI) for management functionality
                interface_vlan = self._get_vlan_for_switch_type('access')
                # Access switches get unique management IPs (not gateway)
                mgmt_ip = self._get_unique_ip_for_vlan(interface_vlan)
                self.graph.nodes[access]['interface_vlan'] = interface_vlan
                self.graph.nodes[access]['interface_vlan_ip'] = str(mgmt_ip)
                self.switch_vlans[access].append(interface_vlan)
                logging.debug(f"{access}: Interface VLAN {interface_vlan}, IP {mgmt_ip}")
        
        elif topology_type == 'spine-leaf':
            # Spine switches support all VLANs (backbone)
            for spine in node_types['spine']:
                self.switch_vlans[spine] = []
                self.graph.nodes[spine]['vlans_supported'] = []
                
                # Assign Interface VLAN (SVI) for routing functionality
                interface_vlan = self._get_vlan_for_switch_type('spine')
                # Reserve the gateway IP (.1) but each spine gets unique IP
                if interface_vlan not in self.vlan_to_gateway:
                    self._get_gateway_for_vlan(interface_vlan)  # Reserve .1 as virtual gateway
                spine_ip = self._get_unique_ip_for_vlan(interface_vlan)
                gateway_reserved = str(self.vlan_to_gateway[interface_vlan])
                
                self.graph.nodes[spine]['interface_vlan'] = interface_vlan
                self.graph.nodes[spine]['interface_vlan_ip'] = str(spine_ip)
                self.graph.nodes[spine]['interface_vlan_gateway'] = gateway_reserved
                self.switch_vlans[spine].append(interface_vlan)
                logging.debug(f"{spine}: Interface VLAN {interface_vlan}, IP {spine_ip}, Virtual Gateway {gateway_reserved}")
            
            # Leaf switches: assign Interface VLAN for management and support VLANs for connected servers
            for leaf in node_types['leaf']:
                self.switch_vlans[leaf] = []
                self.graph.nodes[leaf]['vlans_supported'] = []
                
                # Assign Interface VLAN (SVI) for management functionality
                interface_vlan = self._get_vlan_for_switch_type('leaf')
                # Leaf switches get unique management IPs (not gateway)
                mgmt_ip = self._get_unique_ip_for_vlan(interface_vlan)
                self.graph.nodes[leaf]['interface_vlan'] = interface_vlan
                self.graph.nodes[leaf]['interface_vlan_ip'] = str(mgmt_ip)
                self.switch_vlans[leaf].append(interface_vlan)
                logging.debug(f"{leaf}: Interface VLAN {interface_vlan}, IP {mgmt_ip}")
        
        elif topology_type == 'fat-tree':
            # Core switches: assign Interface VLAN for management/routing
            for core in node_types['core']:
                self.switch_vlans[core] = []
                self.graph.nodes[core]['vlans_supported'] = []
                
                # Assign Interface VLAN (SVI) for management/routing functionality
                interface_vlan = self._get_vlan_for_switch_type('core')
                # Core switches get unique management IPs (not gateway)
                mgmt_ip = self._get_unique_ip_for_vlan(interface_vlan)
                self.graph.nodes[core]['interface_vlan'] = interface_vlan
                self.graph.nodes[core]['interface_vlan_ip'] = str(mgmt_ip)
                self.switch_vlans[core].append(interface_vlan)
                logging.debug(f"{core}: Interface VLAN {interface_vlan}, IP {mgmt_ip}")
            
            # Aggregation switches: Interface VLAN for routing
            for agg in node_types['aggregation']:
                self.switch_vlans[agg] = []
                self.graph.nodes[agg]['vlans_supported'] = []
                
                # Assign Interface VLAN (SVI)
                interface_vlan = self._get_vlan_for_switch_type('aggregation')
                # Reserve the gateway IP (.1) but each aggregation switch gets unique IP
                if interface_vlan not in self.vlan_to_gateway:
                    self._get_gateway_for_vlan(interface_vlan)  # Reserve .1 as virtual gateway
                agg_ip = self._get_unique_ip_for_vlan(interface_vlan)
                gateway_reserved = str(self.vlan_to_gateway[interface_vlan])
                
                self.graph.nodes[agg]['interface_vlan'] = interface_vlan
                self.graph.nodes[agg]['interface_vlan_ip'] = str(agg_ip)
                self.graph.nodes[agg]['interface_vlan_gateway'] = gateway_reserved
                self.switch_vlans[agg].append(interface_vlan)
                logging.debug(f"{agg}: Interface VLAN {interface_vlan}, IP {agg_ip}, Virtual Gateway {gateway_reserved}")
            
            # Edge switches: assign Interface VLAN for management and support VLANs for connected servers
            for edge in node_types['edge']:
                self.switch_vlans[edge] = []
                self.graph.nodes[edge]['vlans_supported'] = []
                
                # Assign Interface VLAN (SVI) for management functionality
                interface_vlan = self._get_vlan_for_switch_type('edge')
                # Edge switches get unique management IPs (not gateway)
                mgmt_ip = self._get_unique_ip_for_vlan(interface_vlan)
                self.graph.nodes[edge]['interface_vlan'] = interface_vlan
                self.graph.nodes[edge]['interface_vlan_ip'] = str(mgmt_ip)
                self.switch_vlans[edge].append(interface_vlan)
                logging.debug(f"{edge}: Interface VLAN {interface_vlan}, IP {mgmt_ip}")
    
    def _assign_endpoint_networks(self, node_types: Dict[str, List[str]], 
                                   topology_type: str) -> None:
        """
        Assign VLAN IDs, IP addresses, and gateways to endpoints/servers.
        
        Args:
            node_types (Dict[str, List[str]]): Categorized node types
            topology_type (str): Type of topology ('3-tier', 'fat-tree', 'spine-leaf')
        """
        logging.info(f"Assigning IP addresses to endpoints for {topology_type} topology...")
        
        # Get endpoint and server nodes
        endpoints = node_types['endpoint'] + node_types['server']
        
        if not endpoints:
            logging.warning("No endpoints or servers found in the graph!")
            return
        
        # Process each endpoint
        total_endpoints = len(endpoints)
        for idx, endpoint in enumerate(endpoints):
            # Find the connected switch (should be access/edge/leaf switch)
            neighbors = list(self.graph.neighbors(endpoint))
            
            if not neighbors:
                logging.warning(f"Endpoint {endpoint} has no connections!")
                continue
            
            # Get the first neighbor (should be the connecting switch)
            connected_switch = neighbors[0]
            
            # Determine the gateway switch (aggregation/spine) for this endpoint
            gateway_switch = self._find_gateway_switch(connected_switch, topology_type, node_types)
            
            if not gateway_switch:
                logging.warning(f"No gateway switch found for {endpoint}")
                continue
            
            # Get or assign a VLAN for this endpoint's link based on distribution strategy
            vlan_id = self._get_or_assign_link_vlan(endpoint, connected_switch, gateway_switch, 
                                                     endpoint_index=idx, total_endpoints=total_endpoints)
            
            # Assign VLAN to the edge
            self.graph.edges[connected_switch, endpoint]['vlan_id'] = vlan_id
            
            # Update switch VLAN support
            if vlan_id not in self.switch_vlans[connected_switch]:
                self.switch_vlans[connected_switch].append(vlan_id)
            
            # Get gateway IP from the gateway switch
            gateway_ip = self.graph.nodes[gateway_switch].get('interface_vlan_gateway')
            
            if not gateway_ip:
                logging.warning(f"No gateway IP found for switch {gateway_switch}")
                continue
            
            # Assign IP address to endpoint
            endpoint_ip = self._get_next_ip_for_vlan(vlan_id)
            
            # Set endpoint attributes
            self.graph.nodes[endpoint]['ip_address'] = str(endpoint_ip)
            self.graph.nodes[endpoint]['default_gateway'] = gateway_ip
            self.graph.nodes[endpoint]['vlan_id'] = vlan_id
            self.graph.nodes[endpoint]['subnet'] = str(self.vlan_to_subnet[vlan_id])
            
            logging.debug(f"{endpoint}: IP={endpoint_ip}, Gateway={gateway_ip}, VLAN={vlan_id}")
        
        # Update all switch vlans_supported attributes
        for switch, vlans in self.switch_vlans.items():
            self.graph.nodes[switch]['vlans_supported'] = sorted(vlans)
    
    def _find_gateway_switch(self, access_switch: str, topology_type: str, 
                            node_types: Dict[str, List[str]]) -> Optional[str]:
        """
        Find the gateway switch (aggregation/spine) for a given access/edge/leaf switch.
        
        Args:
            access_switch (str): Name of the access/edge/leaf switch
            topology_type (str): Type of topology
            node_types (Dict[str, List[str]]): Categorized node types
            
        Returns:
            Optional[str]: Name of the gateway switch, or None if not found
        """
        if topology_type == '3-tier' or topology_type == 'fat-tree':
            # Find connected aggregation switch
            neighbors = list(self.graph.neighbors(access_switch))
            for neighbor in neighbors:
                if neighbor in node_types['aggregation']:
                    return neighbor
        
        elif topology_type == 'spine-leaf':
            # Find connected spine switch (use first one for simplicity)
            neighbors = list(self.graph.neighbors(access_switch))
            for neighbor in neighbors:
                if neighbor in node_types['spine']:
                    return neighbor
        
        return None
    
    def _get_endpoint_vlan_for_distribution(self, endpoint_index: int, 
                                             total_endpoints: int, 
                                             gateway_switch: str) -> int:
        """
        Get VLAN ID for an endpoint based on the distribution strategy.
        
        Args:
            endpoint_index (int): Index of the current endpoint
            total_endpoints (int): Total number of endpoints
            gateway_switch (str): Gateway switch name
            
        Returns:
            int: VLAN ID for this endpoint
        """
        if self.pc_distribution == 'single':
            # All endpoints use the gateway's VLAN
            gateway_vlan = self.graph.nodes[gateway_switch].get('interface_vlan')
            if gateway_vlan:
                return gateway_vlan
            # Fallback: create new VLAN
            vlan_id = self._get_next_vlan()
            self._create_subnet_for_vlan(vlan_id)
            self._get_gateway_for_vlan(vlan_id)
            return vlan_id
        
        elif self.pc_distribution == 'equal':
            # Distribute equally across endpoint VLANs
            if self.endpoint_vlans:
                # Use pre-configured endpoint VLANs
                if gateway_switch not in self.endpoint_vlan_assignments:
                    # Initialize endpoint VLANs for this gateway
                    self.endpoint_vlan_assignments[gateway_switch] = []
                    for vlan_id in self.endpoint_vlans:
                        self.endpoint_vlan_assignments[gateway_switch].append(vlan_id)
                        self._create_subnet_for_vlan(vlan_id)
                        # Set gateway for this VLAN to the gateway switch's IP
                        gateway_ip_addr = self.graph.nodes[gateway_switch].get('interface_vlan_gateway')
                        if gateway_ip_addr and vlan_id not in self.vlan_to_gateway:
                            # Parse gateway IP and use it for this VLAN
                            self.vlan_to_gateway[vlan_id] = ipaddress.IPv4Address(gateway_ip_addr)
                
                # Distribute equally across available VLANs
                vlans = self.endpoint_vlan_assignments[gateway_switch]
                vlan_index = endpoint_index % len(vlans)
                return vlans[vlan_index]
            else:
                # No endpoint VLANs specified, use gateway's VLAN
                return self.graph.nodes[gateway_switch].get('interface_vlan')
        
        elif self.pc_distribution == 'random':
            # Randomly assign to endpoint VLANs
            if self.endpoint_vlans:
                # Use pre-configured endpoint VLANs
                if gateway_switch not in self.endpoint_vlan_assignments:
                    # Initialize endpoint VLANs for this gateway
                    self.endpoint_vlan_assignments[gateway_switch] = []
                    for vlan_id in self.endpoint_vlans:
                        self.endpoint_vlan_assignments[gateway_switch].append(vlan_id)
                        self._create_subnet_for_vlan(vlan_id)
                        # Set gateway for this VLAN to the gateway switch's IP
                        gateway_ip_addr = self.graph.nodes[gateway_switch].get('interface_vlan_gateway')
                        if gateway_ip_addr and vlan_id not in self.vlan_to_gateway:
                            # Parse gateway IP and use it for this VLAN
                            self.vlan_to_gateway[vlan_id] = ipaddress.IPv4Address(gateway_ip_addr)
                
                # Randomly select a VLAN
                vlans = self.endpoint_vlan_assignments[gateway_switch]
                return random.choice(vlans)
            else:
                # No endpoint VLANs specified, use gateway's VLAN
                return self.graph.nodes[gateway_switch].get('interface_vlan')
        
        else:
            # Default to single distribution
            return self.graph.nodes[gateway_switch].get('interface_vlan')
    
    def _get_or_assign_link_vlan(self, endpoint: str, access_switch: str, 
                                  gateway_switch: str, endpoint_index: int = 0,
                                  total_endpoints: int = 1) -> int:
        """
        Get or assign a VLAN ID for an endpoint link.
        
        Args:
            endpoint (str): Endpoint node name
            access_switch (str): Access/edge/leaf switch name
            gateway_switch (str): Gateway switch name
            endpoint_index (int): Index of the current endpoint (for distribution)
            total_endpoints (int): Total number of endpoints (for distribution)
            
        Returns:
            int: VLAN ID for this link
        """
        # Use the distribution strategy to get the VLAN
        return self._get_endpoint_vlan_for_distribution(endpoint_index, total_endpoints, gateway_switch)
    
    def assign_network_attributes(self, topology_type: str) -> None:
        """
        Assign network attributes (VLANs, IPs, gateways) to the graph based on topology type.
        
        This is the main method that orchestrates the entire IPAM assignment process.
        
        Args:
            topology_type (str): Type of topology - '3-tier', 'fat-tree', or 'spine-leaf'
            
        Raises:
            ValueError: If topology_type is not supported
        """
        supported_topologies = ['3-tier', 'fat-tree', 'spine-leaf']
        
        if topology_type not in supported_topologies:
            raise ValueError(f"Unsupported topology type: {topology_type}. "
                           f"Supported types: {supported_topologies}")
        
        logging.info("=" * 80)
        logging.info(f"Starting IPAM assignment for {topology_type} topology")
        logging.info("=" * 80)
        
        # Step 1: Identify node types
        node_types = self._identify_node_types()
        logging.info(f"Node types identified: "
                    f"Core={len(node_types['core'])}, "
                    f"Aggregation={len(node_types['aggregation'])}, "
                    f"Spine={len(node_types['spine'])}, "
                    f"Leaf={len(node_types['leaf'])}, "
                    f"Access/Edge={len(node_types['access'])}, "
                    f"Endpoints={len(node_types['endpoint'])}, "
                    f"Servers={len(node_types['server'])}")
        
        # Step 2: Assign VLANs to switches
        self._assign_vlans_to_switches(node_types, topology_type)
        
        # Step 3: Assign networks to endpoints/servers
        self._assign_endpoint_networks(node_types, topology_type)
        
        logging.info("=" * 80)
        logging.info(f"IPAM assignment completed successfully!")
        logging.info(f"Total VLANs assigned: {self.vlan_index}")
        logging.info(f"Total subnets created: {len(self.vlan_to_subnet)}")
        logging.info("=" * 80)
    
    def print_summary(self, verbose: bool = False) -> None:
        """
        Print a summary of the IPAM assignments.
        
        Args:
            verbose (bool): If True, print detailed information for all nodes
        """
        print("\n" + "=" * 80)
        print("IPAM ASSIGNMENT SUMMARY")
        print("=" * 80)
        
        # Summary statistics
        print(f"\nStatistics:")
        print(f"  Total Nodes: {self.graph.number_of_nodes()}")
        print(f"  Total Edges: {self.graph.number_of_edges()}")
        print(f"  VLANs Assigned: {self.vlan_index}")
        print(f"  Subnets Created: {len(self.vlan_to_subnet)}")
        
        # VLAN to Subnet mapping
        print(f"\nVLAN to Subnet Mapping:")
        for vlan_id in sorted(self.vlan_to_subnet.keys()):
            subnet = self.vlan_to_subnet[vlan_id]
            gateway = self.vlan_to_gateway.get(vlan_id, 'N/A')
            print(f"  VLAN {vlan_id}: {subnet} (Gateway: {gateway})")
        
        if verbose:
            # Detailed node information
            print(f"\nDetailed Node Information:")
            print("-" * 80)
            
            # Switches with Interface VLANs
            print("\nSwitches with Interface VLANs (Gateways):")
            for node in self.graph.nodes():
                if 'interface_vlan_gateway' in self.graph.nodes[node]:
                    attrs = self.graph.nodes[node]
                    print(f"  {node}:")
                    print(f"    Interface VLAN: {attrs.get('interface_vlan', 'N/A')}")
                    print(f"    Gateway IP: {attrs.get('interface_vlan_gateway', 'N/A')}")
                    print(f"    VLANs Supported: {attrs.get('vlans_supported', [])}")
            
            # Endpoints with IP addresses
            print("\nEndpoints/Servers with IP Addresses:")
            for node in self.graph.nodes():
                if 'ip_address' in self.graph.nodes[node]:
                    attrs = self.graph.nodes[node]
                    print(f"  {node}:")
                    print(f"    IP Address: {attrs.get('ip_address', 'N/A')}")
                    print(f"    Default Gateway: {attrs.get('default_gateway', 'N/A')}")
                    print(f"    VLAN ID: {attrs.get('vlan_id', 'N/A')}")
                    print(f"    Subnet: {attrs.get('subnet', 'N/A')}")
        
        print("=" * 80)


def demonstration_example():
    """
    Demonstration example showing IPAM_Manager usage with a simple 3-Tier topology.
    """
    print("\n" + "=" * 80)
    print("IPAM_MANAGER DEMONSTRATION EXAMPLE")
    print("=" * 80)
    
    # Create a simple 3-Tier network topology
    print("\n1. Creating a simple 3-Tier network topology...")
    G = nx.Graph()
    
    # Core layer (2 switches)
    core_switches = ['csw0', 'csw1']
    G.add_nodes_from(core_switches)
    
    # Aggregation layer (2 switches)
    agg_switches = ['asw0', 'asw1']
    G.add_nodes_from(agg_switches)
    
    # Access layer (2 switches)
    access_switches = ['esw0', 'esw1']
    G.add_nodes_from(access_switches)
    
    # Endpoints (4 PCs total: 2 per access switch)
    endpoints = ['ep0_0', 'ep0_1', 'ep1_0', 'ep1_1']
    G.add_nodes_from(endpoints)
    
    # Connect core to aggregation (full mesh)
    for core in core_switches:
        for agg in agg_switches:
            G.add_edge(core, agg)
    
    # Connect aggregation to access (each access switch connects to both aggregation switches)
    for access in access_switches:
        for agg in agg_switches:
            G.add_edge(agg, access)
    
    # Connect endpoints to access switches
    G.add_edge('esw0', 'ep0_0')
    G.add_edge('esw0', 'ep0_1')
    G.add_edge('esw1', 'ep1_0')
    G.add_edge('esw1', 'ep1_1')
    
    print(f"   Created topology with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Instantiate IPAM_Manager
    print("\n2. Instantiating IPAM_Manager...")
    ipam = IPAM_Manager(G)
    
    # Assign network attributes
    print("\n3. Assigning network attributes for 3-tier topology...")
    ipam.assign_network_attributes('3-tier')
    
    # Print summary
    print("\n4. Printing assignment results...")
    ipam.print_summary(verbose=False)
    
    # Print specific examples
    print("\n5. Sample Node and Edge Attributes:")
    print("-" * 80)
    
    # Show an aggregation switch
    print("\nAggregation Switch Example (asw0):")
    asw0_attrs = G.nodes['asw0']
    for key, value in asw0_attrs.items():
        print(f"  {key}: {value}")
    
    # Show an access switch
    print("\nAccess Switch Example (esw0):")
    esw0_attrs = G.nodes['esw0']
    for key, value in esw0_attrs.items():
        print(f"  {key}: {value}")
    
    # Show an endpoint
    print("\nEndpoint Example (ep0_0):")
    ep0_0_attrs = G.nodes['ep0_0']
    for key, value in ep0_0_attrs.items():
        print(f"  {key}: {value}")
    
    # Show an edge with VLAN
    print("\nEdge Example (esw0 <-> ep0_0):")
    edge_attrs = G.edges['esw0', 'ep0_0']
    for key, value in edge_attrs.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    return G, ipam


if __name__ == "__main__":
    # Run the demonstration
    graph, ipam_manager = demonstration_example()
    
    # Additional demonstration: Print all endpoints with their networking info
    print("\n" + "=" * 80)
    print("COMPLETE ENDPOINT NETWORK CONFIGURATION")
    print("=" * 80)
    
    for node in graph.nodes():
        if node.startswith('ep'):
            attrs = graph.nodes[node]
            print(f"\n{node}:")
            print(f"  IP Address:      {attrs.get('ip_address', 'N/A')}")
            print(f"  Subnet Mask:     {attrs.get('subnet', 'N/A').split('/')[1] if 'subnet' in attrs else 'N/A'}")
            print(f"  Default Gateway: {attrs.get('default_gateway', 'N/A')}")
            print(f"  VLAN ID:         {attrs.get('vlan_id', 'N/A')}")
    
    print("\n" + "=" * 80)

