"""
OpenRoute Navigator - Routing Service

Core routing engine using NetworkX for multi-criteria pathfinding
"""

import networkx as nx
from typing import List, Dict, Optional, Tuple
from app.models.schemas import Route, Alert, VehicleParams, Coordinates
from app.services.overpass import OverpassService
from app.services.scoring import ScoringService


class RoutingService:
    """Service for calculating routes with different optimization criteria"""
    
    def __init__(self):
        self.overpass = OverpassService()
        self.scorer = ScoringService()
    
    def calculate_routes(
        self,
        origin: Coordinates,
        destination: Coordinates,
        vehicle: Optional[VehicleParams] = None
    ) -> List[Route]:
        """
        Calculate multiple routes with different optimization criteria
        
        Args:
            origin: Origin coordinates
            destination: Destination coordinates
            vehicle: Vehicle parameters
            
        Returns:
            List of Route objects
        """
        # Query OSM data
        bbox = self.overpass.calculate_bbox(origin, destination)
        osm_data = self.overpass.query_osm_data(bbox)
        
        # Build graph
        G = self.overpass.build_graph(osm_data, origin, destination)
        
        if not G.has_node("origin") or not G.has_node("destination"):
            raise Exception("Failed to connect origin or destination to road network")
        
        # Calculate routes for different criteria
        routes = []
        
        criteria = ["fastest", "best_surface", "safest"]
        
        # Only add truck_compatible if vehicle is a truck
        if vehicle and vehicle.vehicle_type == "truck":
            criteria.append("truck_compatible")
        
        for criterion in criteria:
            try:
                route = self._calculate_single_route(
                    G, criterion, vehicle, origin, destination
                )
                if route:
                    routes.append(route)
            except nx.NetworkXNoPath:
                # No path found for this criterion (e.g., no truck-compatible route)
                print(f"No path found for criterion: {criterion}")
                continue
            except Exception as e:
                print(f"Error calculating {criterion} route: {e}")
                continue
        
        if not routes:
            raise Exception("No valid routes found")
        
        return routes
    
    def _calculate_single_route(
        self,
        G: nx.MultiDiGraph,
        criterion: str,
        vehicle: Optional[VehicleParams],
        origin: Coordinates,
        destination: Coordinates
    ) -> Optional[Route]:
        """
        Calculate a single route for a specific criterion
        
        Args:
            G: NetworkX graph
            criterion: Routing criterion
            vehicle: Vehicle parameters
            origin: Origin coordinates
            destination: Destination coordinates
            
        Returns:
            Route object or None if no path found
        """
        # Create weighted graph for this criterion
        weighted_graph = self._create_weighted_graph(G, criterion, vehicle)
        
        # Find shortest path
        try:
            path = nx.shortest_path(
                weighted_graph,
                source="origin",
                target="destination",
                weight="weight"
            )
        except nx.NetworkXNoPath:
            return None
        
        # Calculate route metrics
        total_distance = 0.0
        geometry = []
        all_alerts = []
        
        for i in range(len(path) - 1):
            node1 = path[i]
            node2 = path[i + 1]
            
            # Get node coordinates
            node1_data = G.nodes[node1]
            node2_data = G.nodes[node2]
            
            # Add to geometry
            geometry.append([node1_data["lon"], node1_data["lat"]])
            
            # Get edge data (use first edge if multiple)
            edge_data = G.get_edge_data(node1, node2)
            if isinstance(edge_data, dict):
                # MultiDiGraph returns dict of dicts
                edge_data = list(edge_data.values())[0]
            
            # Accumulate distance
            distance = edge_data.get("distance", 0)
            total_distance += distance
            
            # Generate alerts for this edge
            if not edge_data.get("connector"):
                edge_alerts = self.scorer.generate_alerts_for_edge(
                    edge_data,
                    vehicle,
                    node2_data["lat"],
                    node2_data["lon"]
                )
                all_alerts.extend(edge_alerts)
        
        # Add final destination to geometry
        dest_data = G.nodes["destination"]
        geometry.append([dest_data["lon"], dest_data["lat"]])
        
        # Deduplicate alerts by message
        unique_alerts = self._deduplicate_alerts(all_alerts)
        
        # Map criterion to route type
        route_type_map = {
            "fastest": "fastest",
            "best_surface": "best_surface",
            "safest": "safest",
            "truck_compatible": "truck_compatible"
        }
        
        # Create summary
        summary = self.scorer.summarize_alerts(unique_alerts)
        
        return Route(
            type=route_type_map[criterion],
            distance_km=round(total_distance, 2),
            geometry=geometry,
            alerts=unique_alerts,
            summary=summary
        )
    
    def _create_weighted_graph(
        self,
        G: nx.MultiDiGraph,
        criterion: str,
        vehicle: Optional[VehicleParams]
    ) -> nx.DiGraph:
        """
        Create a weighted graph based on criterion
        
        Args:
            G: Original MultiDiGraph
            criterion: Routing criterion
            vehicle: Vehicle parameters
            
        Returns:
            Weighted DiGraph
        """
        weighted = nx.DiGraph()
        
        # Copy nodes
        for node, data in G.nodes(data=True):
            weighted.add_node(node, **data)
        
        # Add weighted edges
        for u, v, data in G.edges(data=True):
            weight = self.scorer.calculate_edge_weight(data, criterion, vehicle)
            
            # Skip infinite weight edges (blocked roads)
            if weight == float('inf'):
                continue
            
            # Add edge with calculated weight
            weighted.add_edge(u, v, weight=weight, **data)
        
        return weighted
    
    def _deduplicate_alerts(self, alerts: List[Alert]) -> List[Alert]:
        """
        Remove duplicate alerts based on message
        
        Args:
            alerts: List of alerts
            
        Returns:
            Deduplicated list of alerts
        """
        seen_messages = set()
        unique_alerts = []
        
        # Prioritize red alerts
        sorted_alerts = sorted(alerts, key=lambda a: {"red": 0, "yellow": 1, "green": 2}[a.level])
        
        for alert in sorted_alerts:
            if alert.message not in seen_messages:
                seen_messages.add(alert.message)
                unique_alerts.append(alert)
        
        return unique_alerts[:10]  # Limit to 10 most important alerts
