"""
OpenRoute Navigator - Scoring Service

Handles route scoring and alert generation based on different criteria
"""

from typing import Dict, List, Optional
from app.models.schemas import Alert, VehicleParams, Coordinates
from app.utils.osm_weights import (
    HIGHWAY_WEIGHTS,
    SURFACE_WEIGHTS,
    SMOOTHNESS_WEIGHTS,
    TRACKTYPE_WEIGHTS,
    SAFETY_FACTORS,
    TRUCK_RESTRICTIONS,
    DEFAULTS,
    CRITERIA_MULTIPLIERS,
    get_speed_penalty
)


class ScoringService:
    """Service for calculating edge weights and generating alerts"""
    
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
        """Get safety-based weight"""
        weight_factor = 1.0
        
        # Lighting factor
        lit = edge_data.get("lit")
        if lit:
            lit_factor = SAFETY_FACTORS["lit"].get(lit, SAFETY_FACTORS["lit"]["default"])
            weight_factor *= lit_factor
        else:
            weight_factor *= SAFETY_FACTORS["lit"]["default"]
        
        # Traffic signals factor
        if edge_data.get("traffic_signals"):
            weight_factor *= SAFETY_FACTORS["traffic_signals"]["yes"]
        
        # Speed penalty
        maxspeed = edge_data.get("maxspeed", DEFAULTS["maxspeed"])
        if maxspeed:
            speed_factor = get_speed_penalty(maxspeed)
            weight_factor *= speed_factor
        
        return weight_factor - 1.0
    
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
        
        # Lighting alerts
        lit = edge_data.get("lit")
        if lit == "no":
            alerts.append(Alert(
                level="yellow",
                message="No street lighting",
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
