"""
OpenRoute Navigator - Scoring Service

Handles route scoring and alert generation based on different criteria
"""

from typing import Dict, List, Optional, Tuple
from math import radians
import numpy as np
from scipy.spatial import KDTree
from app.models.schemas import Alert, VehicleParams, Coordinates
from app.utils.osm_weights import (
    HIGHWAY_WEIGHTS,
    SURFACE_WEIGHTS,
    SMOOTHNESS_WEIGHTS,
    TRACKTYPE_WEIGHTS,
    SERVICE_PROXIMITY_FACTORS,
    TRUCK_RESTRICTIONS,
    DEFAULTS,
    CRITERIA_MULTIPLIERS,
    get_speed_penalty
)


class ScoringService:
    """
    Service for calculating edge weights and generating alerts.
    
    To use automotive-service-based safety scoring, supply the lists of
    fuel station and repair shop coordinates (from OverpassService) via
    set_automotive_services() before calling calculate_edge_weight().
    """

    # Proximity radius (km) within which a service is considered "nearby"
    SERVICE_RADIUS_KM: float = 0.5

    def __init__(self) -> None:
        # Raw coordinate lists — stored so callers can inspect them if needed
        self._fuel_stations: List[Tuple[float, float]] = []
        self._repair_shops: List[Tuple[float, float]] = []

        # KDTree spatial indices built from the coordinate lists.
        # Querying a KDTree is O(log N) vs O(N) for a linear scan.
        # Trees are (re)built once per route request in set_automotive_services().
        self._fuel_tree: Optional[KDTree] = None
        self._repair_tree: Optional[KDTree] = None

        # Radius in radians used for KDTree ball queries.
        # KDTree with radian coords on unit sphere: r_rad = r_km / R_earth
        self._radius_rad: float = self.SERVICE_RADIUS_KM / 6371.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_automotive_services(
        self,
        fuel_stations: List[Tuple[float, float]],
        repair_shops: List[Tuple[float, float]]
    ) -> None:
        """
        Update the service location lists and rebuild the KDTree indices.

        Called once per route request after OverpassService.query_osm_data().
        The KDTree is built here (O(S log S)) so that per-edge lookups are
        O(log S) instead of O(S).

        Args:
            fuel_stations: List of (lat, lon) tuples for fuel stations.
            repair_shops:  List of (lat, lon) tuples for car repair shops.
        """
        self._fuel_stations = fuel_stations
        self._repair_shops = repair_shops
        self._fuel_tree = self._build_kdtree(fuel_stations)
        self._repair_tree = self._build_kdtree(repair_shops)
    
    def calculate_edge_weight(
        self,
        edge_data: Dict,
        criterion: str,
        vehicle: Optional[VehicleParams] = None
    ) -> float:
        """
        Calculate edge weight based on criterion
        
        Args:
            edge_data: Edge data dictionary with OSM tags
            criterion: Routing criterion (fastest, best_surface, safest, truck_compatible)
            vehicle: Vehicle parameters
            
        Returns:
            Edge weight (lower is better)
        """
        # Get base distance
        distance = edge_data.get("distance", 1.0)
        
        # Skip connector edges (origin/destination connectors)
        if edge_data.get("connector"):
            return distance
        
        # Get criterion multipliers
        multipliers = CRITERIA_MULTIPLIERS.get(criterion, CRITERIA_MULTIPLIERS["fastest"])
        
        # Calculate component weights
        highway_weight = self._get_highway_weight(edge_data)
        surface_weight = self._get_surface_weight(edge_data)
        smoothness_weight = self._get_smoothness_weight(edge_data)
        safety_weight = self._get_safety_weight(edge_data)
        
        # Combine weights based on criterion
        total_weight = (
            distance * multipliers["distance"] *
            (1 + highway_weight * multipliers["highway_type"]) *
            (1 + surface_weight * multipliers["surface"]) *
            (1 + smoothness_weight * multipliers["smoothness"]) *
            (1 + safety_weight * multipliers["safety"])
        )
        
        # Apply truck restrictions if applicable
        if criterion == "truck_compatible" and vehicle:
            restriction_penalty = self._get_truck_restriction_penalty(edge_data, vehicle)
            if restriction_penalty == float('inf'):
                return float('inf')  # Blocked edge
            total_weight *= restriction_penalty
        
        return total_weight
    
    def _get_highway_weight(self, edge_data: Dict) -> float:
        """Get highway type weight"""
        highway = edge_data.get("highway", DEFAULTS["highway"])
        return HIGHWAY_WEIGHTS.get(highway, HIGHWAY_WEIGHTS["default"]) - 1.0
    
    def _get_surface_weight(self, edge_data: Dict) -> float:
        """Get surface quality weight"""
        surface = edge_data.get("surface")
        if not surface:
            return 0.0
        
        weight = SURFACE_WEIGHTS.get(surface, SURFACE_WEIGHTS["default"])
        return weight - 1.0
    
    def _get_smoothness_weight(self, edge_data: Dict) -> float:
        """Get smoothness weight"""
        smoothness = edge_data.get("smoothness")
        if not smoothness:
            return 0.0
        
        weight = SMOOTHNESS_WEIGHTS.get(smoothness, SMOOTHNESS_WEIGHTS["default"])
        return weight - 1.0
    
    def _get_safety_weight(self, edge_data: Dict) -> float:
        """
        Calculate safety weight based on the presence of automotive services
        (fuel stations and car repair shops) near the road segment.

        The midpoint of the edge is used as the reference coordinate for
        proximity checks. If no geometry is available, the weight defaults
        to the no-service penalty.

        Weight factors (from SERVICE_PROXIMITY_FACTORS):
            - fuel_station_bonus : multiplied in when a fuel station is nearby
            - repair_shop_bonus  : multiplied in when a repair shop is nearby
            - no_service_penalty : multiplied in when neither service is nearby

        Returns:
            float: service_factor - 1.0  (compatible with calculate_edge_weight)
        """
        # Retrieve the segment midpoint from edge data (set during graph build)
        # If not available, we cannot do proximity checks — apply a neutral weight.
        seg_lat: Optional[float] = edge_data.get("seg_lat")
        seg_lon: Optional[float] = edge_data.get("seg_lon")

        if seg_lat is None or seg_lon is None:
            # No positional information available: use neutral factor
            return 0.0

        # Check proximity to each service type using the pre-built KDTrees
        fuel_nearby = self._has_service_nearby(
            seg_lat, seg_lon, self._fuel_tree
        )
        repair_nearby = self._has_service_nearby(
            seg_lat, seg_lon, self._repair_tree
        )

        service_factor = 1.0

        if fuel_nearby:
            service_factor *= SERVICE_PROXIMITY_FACTORS["fuel_station_bonus"]

        if repair_nearby:
            service_factor *= SERVICE_PROXIMITY_FACTORS["repair_shop_bonus"]

        if not fuel_nearby and not repair_nearby:
            service_factor *= SERVICE_PROXIMITY_FACTORS["no_service_penalty"]

        return service_factor - 1.0

    def _has_service_nearby(
        self,
        lat: float,
        lon: float,
        tree: Optional[KDTree]
    ) -> bool:
        """
        Return True if any service location is within SERVICE_RADIUS_KM of
        (lat, lon), using a pre-built KDTree for O(log S) lookup.

        Args:
            lat, lon: Query point in degrees.
            tree: KDTree built from service coordinates in radians.
                  If None (no services exist), returns False immediately.
        """
        if tree is None:
            return False

        # Convert query point to radians on unit sphere
        point = np.array([[radians(lat), radians(lon)]])
        matches = tree.query_ball_point(point, r=self._radius_rad)
        return len(matches[0]) > 0

    @staticmethod
    def _build_kdtree(
        locations: List[Tuple[float, float]]
    ) -> Optional[KDTree]:
        """
        Build a KDTree from a list of (lat, lon) coordinate pairs.
        Coordinates are converted to radians so that Euclidean distance in
        radian-space approximates arc length on the unit sphere within small
        areas (valid for the proximity radii used here: ≤0.5 km).

        Returns None if the location list is empty (avoids TypeError in scipy).
        """
        if not locations:
            return None
        coords_rad = np.array(
            [[radians(lat), radians(lon)] for lat, lon in locations]
        )
        return KDTree(coords_rad)
    
    def _get_truck_restriction_penalty(
        self,
        edge_data: Dict,
        vehicle: VehicleParams
    ) -> float:
        """
        Get truck restriction penalty
        
        Returns:
            Penalty multiplier or inf if road is blocked
        """
        # Check height restriction
        maxheight = edge_data.get("maxheight")
        if maxheight and vehicle.height and vehicle.height > maxheight:
            return float('inf')  # Cannot pass
        
        # Check weight restriction
        maxweight = edge_data.get("maxweight")
        if maxweight and vehicle.weight and vehicle.weight > maxweight:
            return float('inf')  # Cannot pass
        
        # Check HGV (Heavy Goods Vehicle) restriction
        hgv = edge_data.get("hgv")
        if hgv == "no" and vehicle.vehicle_type == "truck":
            return float('inf')  # Trucks not allowed
        
        # Check access restriction
        access = edge_data.get("access")
        if access in ["private", "no"] and vehicle.vehicle_type == "truck":
            return float('inf')  # Access denied
        
        # Apply penalties for limited access
        penalty = 1.0
        
        if hgv == "destination":
            penalty *= 2.0  # Discourage but allow
        
        if access == "delivery":
            penalty *= 1.5
        
        return penalty
    
    def generate_alerts_for_edge(
        self,
        edge_data: Dict,
        vehicle: Optional[VehicleParams] = None,
        node_lat: Optional[float] = None,
        node_lon: Optional[float] = None
    ) -> List[Alert]:
        """
        Generate alerts for a road segment
        
        Args:
            edge_data: Edge data dictionary
            vehicle: Vehicle parameters
            node_lat: Node latitude for alert location
            node_lon: Node longitude for alert location
            
        Returns:
            List of alerts
        """
        alerts = []
        location = None
        
        if node_lat is not None and node_lon is not None:
            location = Coordinates(lat=node_lat, lon=node_lon)
        
        # Skip connector edges
        if edge_data.get("connector"):
            return alerts
        
        # Surface quality alerts
        surface = edge_data.get("surface")
        if surface in ["unpaved", "dirt", "gravel", "mud"]:
            alerts.append(Alert(
                level="yellow",
                message=f"Unpaved road: {surface}",
                location=location
            ))
        elif surface in ["mud", "sand"]:
            alerts.append(Alert(
                level="red",
                message=f"Poor surface condition: {surface}",
                location=location
            ))
        
        # Smoothness alerts
        smoothness = edge_data.get("smoothness")
        if smoothness in ["bad", "very_bad"]:
            alerts.append(Alert(
                level="yellow",
                message=f"Road quality: {smoothness}",
                location=location
            ))
        elif smoothness in ["horrible", "very_horrible", "impassable"]:
            alerts.append(Alert(
                level="red",
                message=f"Very poor road quality: {smoothness}",
                location=location
            ))
        
        # Safety / service-infrastructure alerts
        seg_lat: Optional[float] = edge_data.get("seg_lat")
        seg_lon: Optional[float] = edge_data.get("seg_lon")

        if seg_lat is not None and seg_lon is not None:
            fuel_nearby = self._has_service_nearby(
                seg_lat, seg_lon, self._fuel_tree
            )
            repair_nearby = self._has_service_nearby(
                seg_lat, seg_lon, self._repair_tree
            )

            if fuel_nearby and repair_nearby:
                alerts.append(Alert(
                    level="green",
                    message="Service-rich segment: fuel station and repair shop nearby",
                    location=location
                ))
            elif fuel_nearby:
                alerts.append(Alert(
                    level="green",
                    message="Fuel station nearby",
                    location=location
                ))
            elif repair_nearby:
                alerts.append(Alert(
                    level="green",
                    message="Car repair service nearby",
                    location=location
                ))
            else:
                alerts.append(Alert(
                    level="yellow",
                    message="No fuel stations or repair services nearby",
                    location=location
                ))

        # Speed alerts
        maxspeed = edge_data.get("maxspeed")
        if maxspeed and maxspeed > 100:
            alerts.append(Alert(
                level="yellow",
                message=f"High speed road: {maxspeed} km/h",
                location=location
            ))
        
        # Truck-specific alerts
        if vehicle and vehicle.vehicle_type == "truck":
            # Height restriction
            maxheight = edge_data.get("maxheight")
            if maxheight:
                if vehicle.height and vehicle.height > maxheight:
                    alerts.append(Alert(
                        level="red",
                        message=f"Height restriction: {maxheight}m (vehicle: {vehicle.height}m)",
                        location=location
                    ))
                elif vehicle.height and vehicle.height > maxheight * 0.9:
                    alerts.append(Alert(
                        level="yellow",
                        message=f"Tight clearance: {maxheight}m (vehicle: {vehicle.height}m)",
                        location=location
                    ))
            
            # Weight restriction
            maxweight = edge_data.get("maxweight")
            if maxweight:
                if vehicle.weight and vehicle.weight > maxweight:
                    alerts.append(Alert(
                        level="red",
                        message=f"Weight restriction: {maxweight}t (vehicle: {vehicle.weight}t)",
                        location=location
                    ))
                elif vehicle.weight and vehicle.weight > maxweight * 0.9:
                    alerts.append(Alert(
                        level="yellow",
                        message=f"Near weight limit: {maxweight}t (vehicle: {vehicle.weight}t)",
                        location=location
                    ))
            
            # HGV restriction
            hgv = edge_data.get("hgv")
            if hgv == "no":
                alerts.append(Alert(
                    level="red",
                    message="Trucks not allowed (HGV restriction)",
                    location=location
                ))
            elif hgv == "destination":
                alerts.append(Alert(
                    level="yellow",
                    message="Destination traffic only for trucks",
                    location=location
                ))
            
            # Access restriction
            access = edge_data.get("access")
            if access in ["private", "no"]:
                alerts.append(Alert(
                    level="red",
                    message=f"Access restricted: {access}",
                    location=location
                ))
            elif access in ["delivery", "destination"]:
                alerts.append(Alert(
                    level="yellow",
                    message=f"Limited access: {access}",
                    location=location
                ))
        
        return alerts
    
    def summarize_alerts(self, alerts: List[Alert]) -> str:
        """
        Create a human-readable summary of alerts
        
        Args:
            alerts: List of alerts
            
        Returns:
            Summary string
        """
        if not alerts:
            return "Route is clear with no warnings"
        
        red_count = sum(1 for a in alerts if a.level == "red")
        yellow_count = sum(1 for a in alerts if a.level == "yellow")
        
        parts = []
        if red_count > 0:
            parts.append(f"{red_count} critical alert(s)")
        if yellow_count > 0:
            parts.append(f"{yellow_count} caution(s)")
        
        return ", ".join(parts) if parts else "Route is clear"
