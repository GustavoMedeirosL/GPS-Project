"""
OpenRoute Navigator - Overpass API Service

Handles OSM data retrieval via Overpass API
"""

import requests
import networkx as nx
from typing import Dict, List, Tuple, Optional
from app.models.schemas import Coordinates


class OverpassService:
    """Service for querying OpenStreetMap data via Overpass API"""
    
    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        self.timeout = 60
    
    def build_query(self, bbox: Tuple[float, float, float, float]) -> str:
        """
        Build Overpass QL query for road network data
        
        Args:
            bbox: Bounding box (min_lat, min_lon, max_lat, max_lon)
            
        Returns:
            Overpass QL query string
        """
        min_lat, min_lon, max_lat, max_lon = bbox
        
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          way["highway"]
              ["highway"!="footway"]
              ["highway"!="path"]
              ["highway"!="steps"]
              ["highway"!="cycleway"]
              ["highway"!="bridleway"]
              ["highway"!="construction"]
              ["highway"!="proposed"]
              ({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out body;
        >;
        out skel qt;
        """
        return query
    
    def calculate_bbox(
        self,
        origin: Coordinates,
        destination: Coordinates,
        padding: float = 0.05
    ) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box from origin and destination
        
        Args:
            origin: Origin coordinates
            destination: Destination coordinates
            padding: Padding in degrees (default: 0.05 ≈ 5.5km)
            
        Returns:
            Bounding box tuple (min_lat, min_lon, max_lat, max_lon)
        """
        min_lat = min(origin.lat, destination.lat) - padding
        max_lat = max(origin.lat, destination.lat) + padding
        min_lon = min(origin.lon, destination.lon) - padding
        max_lon = max(origin.lon, destination.lon) + padding
        
        return (min_lat, min_lon, max_lat, max_lon)
    
    def query_osm_data(self, bbox: Tuple[float, float, float, float]) -> Dict:
        """
        Query Overpass API for OSM data
        
        Args:
            bbox: Bounding box for query
            
        Returns:
            Raw OSM data dictionary
        """
        query = self.build_query(bbox)
        
        try:
            response = requests.post(
                self.base_url,
                data={"data": query},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise Exception("Overpass API timeout - try a smaller area")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Overpass API error: {e}")
    
    def extract_tags(self, way: Dict) -> Dict:
        """
        Extract relevant tags from OSM way
        
        Args:
            way: OSM way dictionary
            
        Returns:
            Dictionary of extracted tags
        """
        tags = way.get("tags", {})
        
        return {
            "highway": tags.get("highway", "unclassified"),
            "surface": tags.get("surface"),
            "smoothness": tags.get("smoothness"),
            "tracktype": tags.get("tracktype"),
            "lit": tags.get("lit"),
            "traffic_signals": tags.get("traffic_signals"),
            "maxspeed": self._parse_maxspeed(tags.get("maxspeed")),
            "maxheight": self._parse_metric(tags.get("maxheight")),
            "maxweight": self._parse_metric(tags.get("maxweight")),
            "hgv": tags.get("hgv"),
            "access": tags.get("access"),
            "lanes": self._parse_int(tags.get("lanes")),
            "oneway": tags.get("oneway") == "yes",
            "name": tags.get("name", "Unnamed")
        }
    
    def _parse_maxspeed(self, value: Optional[str]) -> Optional[int]:
        """Parse maxspeed tag to integer km/h"""
        if not value:
            return None
        
        try:
            # Handle "50 mph" or "50 km/h" or just "50"
            speed_str = value.split()[0]
            speed = int(speed_str)
            
            # Convert mph to km/h if needed
            if "mph" in value.lower():
                speed = int(speed * 1.60934)
            
            return speed
        except (ValueError, IndexError):
            return None
    
    def _parse_metric(self, value: Optional[str]) -> Optional[float]:
        """Parse metric values like '4.2', '4.2m', '4.2 m'"""
        if not value:
            return None
        
        try:
            # Remove common units and whitespace
            clean_value = value.replace("m", "").replace("t", "").strip()
            return float(clean_value)
        except ValueError:
            return None
    
    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        """Parse integer values"""
        if not value:
            return None
        
        try:
            return int(value)
        except ValueError:
            return None
    
    def build_graph(
        self,
        osm_data: Dict,
        origin: Coordinates,
        destination: Coordinates
    ) -> nx.MultiDiGraph:
        """
        Build NetworkX graph from OSM data
        
        Args:
            osm_data: Raw OSM data from Overpass
            origin: Origin coordinates
            destination: Destination coordinates
            
        Returns:
            NetworkX MultiDiGraph with road network
        """
        G = nx.MultiDiGraph()
        
        # Build node lookup
        nodes = {}
        for element in osm_data.get("elements", []):
            if element["type"] == "node":
                nodes[element["id"]] = {
                    "lat": element["lat"],
                    "lon": element["lon"]
                }
        
        # Add origin and destination as special nodes
        origin_id = "origin"
        dest_id = "destination"
        
        G.add_node(origin_id, lat=origin.lat, lon=origin.lon, is_origin=True)
        G.add_node(dest_id, lat=destination.lat, lon=destination.lon, is_destination=True)
        
        # Add ways as edges
        for element in osm_data.get("elements", []):
            if element["type"] == "way":
                way_nodes = element.get("nodes", [])
                tags = self.extract_tags(element)
                
                # Create edges between consecutive nodes
                for i in range(len(way_nodes) - 1):
                    node1_id = way_nodes[i]
                    node2_id = way_nodes[i + 1]
                    
                    if node1_id not in nodes or node2_id not in nodes:
                        continue
                    
                    node1 = nodes[node1_id]
                    node2 = nodes[node2_id]
                    
                    # Add nodes to graph
                    G.add_node(node1_id, **node1)
                    G.add_node(node2_id, **node2)
                    
                    # Calculate edge length (Haversine distance)
                    distance = self._haversine_distance(
                        node1["lat"], node1["lon"],
                        node2["lat"], node2["lon"]
                    )
                    
                    # Add edge with tags
                    edge_data = {
                        "distance": distance,
                        **tags
                    }
                    
                    G.add_edge(node1_id, node2_id, **edge_data)
                    
                    # Add reverse edge if not oneway
                    if not tags["oneway"]:
                        G.add_edge(node2_id, node1_id, **edge_data)
        
        # Connect origin and destination to nearest nodes
        self._connect_terminal_nodes(G, origin_id, nodes)
        self._connect_terminal_nodes(G, dest_id, nodes)
        
        return G
    
    def _connect_terminal_nodes(
        self,
        G: nx.MultiDiGraph,
        terminal_id: str,
        nodes: Dict
    ):
        """Connect origin/destination to nearest road nodes"""
        terminal_data = G.nodes[terminal_id]
        terminal_lat = terminal_data["lat"]
        terminal_lon = terminal_data["lon"]
        
        # Find nearest nodes
        nearest_nodes = []
        for node_id, node_data in nodes.items():
            if node_id not in G:
                continue
            
            dist = self._haversine_distance(
                terminal_lat, terminal_lon,
                node_data["lat"], node_data["lon"]
            )
            nearest_nodes.append((node_id, dist))
        
        # Connect to 5 nearest nodes
        nearest_nodes.sort(key=lambda x: x[1])
        for node_id, dist in nearest_nodes[:5]:
            # Add bidirectional edges
            G.add_edge(terminal_id, node_id, distance=dist, connector=True)
            G.add_edge(node_id, terminal_id, distance=dist, connector=True)
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
