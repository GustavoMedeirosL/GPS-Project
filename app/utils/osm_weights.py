"""
OpenRoute Navigator - OSM Weight Configurations

Configurable weight mappings for different road attributes
"""

# Highway type weights (lower is better for routing)
HIGHWAY_WEIGHTS = {
    # Major roads
    "motorway": 1.0,
    "motorway_link": 1.1,
    "trunk": 1.2,
    "trunk_link": 1.3,
    "primary": 1.4,
    "primary_link": 1.5,
    "secondary": 1.6,
    "secondary_link": 1.7,
    "tertiary": 1.8,
    "tertiary_link": 1.9,
    
    # Local roads
    "unclassified": 2.0,
    "residential": 2.1,
    "living_street": 2.5,
    
    # Service roads
    "service": 3.0,
    
    # Low quality
    "track": 5.0,
    "path": 10.0,
    "footway": 15.0,
    
    # Default for unknown types
    "default": 2.5
}


# Surface quality weights
SURFACE_WEIGHTS = {
    # Excellent surfaces
    "asphalt": 1.0,
    "concrete": 1.0,
    "paved": 1.1,
    
    # Good surfaces
    "concrete:plates": 1.3,
    "paving_stones": 1.4,
    
    # Moderate surfaces
    "compacted": 2.0,
    "fine_gravel": 2.2,
    
    # Poor surfaces
    "gravel": 3.0,
    "unpaved": 3.5,
    "dirt": 4.0,
    "ground": 4.5,
    "grass": 5.0,
    "sand": 6.0,
    
    # Very poor
    "mud": 8.0,
    
    # Default
    "default": 2.0
}


# Smoothness quality weights
SMOOTHNESS_WEIGHTS = {
    "excellent": 1.0,
    "good": 1.2,
    "intermediate": 1.5,
    "bad": 3.0,
    "very_bad": 5.0,
    "horrible": 8.0,
    "very_horrible": 10.0,
    "impassable": 100.0,
    "default": 1.5
}


# Track type weights (for unpaved roads)
TRACKTYPE_WEIGHTS = {
    "grade1": 1.5,  # Solid surface
    "grade2": 2.0,  # Mostly solid
    "grade3": 3.0,  # Mixed
    "grade4": 4.5,  # Mostly soft
    "grade5": 6.0,  # Soft
    "default": 2.5
}


# Safety factors
SAFETY_FACTORS = {
    "lit": {
        "yes": 0.8,     # 20% bonus for lit roads
        "no": 1.3,      # 30% penalty for unlit roads
        "default": 1.0
    },
    "traffic_signals": {
        "yes": 0.9,     # 10% bonus for traffic signals
        "default": 1.0
    }
}


# Speed-based safety penalties (for high-speed roads)
def get_speed_penalty(maxspeed: int) -> float:
    """
    Calculate safety penalty based on speed limit
    Higher speeds = higher penalty for safety-conscious routing
    """
    if maxspeed <= 40:
        return 1.0
    elif maxspeed <= 60:
        return 1.2
    elif maxspeed <= 80:
        return 1.5
    elif maxspeed <= 100:
        return 2.0
    else:
        return 3.0


# Truck restriction factors
TRUCK_RESTRICTIONS = {
    "hgv": {
        "no": "restricted",
        "designated": "allowed",
        "destination": "limited",
        "default": "check_limits"
    },
    "access": {
        "private": "restricted",
        "no": "restricted",
        "delivery": "limited",
        "destination": "limited",
        "default": "allowed"
    }
}


# Default values for missing tags
DEFAULTS = {
    "maxspeed": 50,  # km/h
    "lanes": 1,
    "surface": "default",
    "smoothness": "default",
    "highway": "default"
}


# Criteria weight multipliers
CRITERIA_MULTIPLIERS = {
    "fastest": {
        "distance": 1.0,
        "highway_type": 0.5,
        "surface": 0.1,
        "smoothness": 0.1,
        "safety": 0.0
    },
    "best_surface": {
        "distance": 1.0,
        "highway_type": 0.3,
        "surface": 2.0,
        "smoothness": 2.0,
        "safety": 0.1
    },
    "safest": {
        "distance": 1.0,
        "highway_type": 0.5,
        "surface": 0.5,
        "smoothness": 0.5,
        "safety": 3.0
    },
    "truck_compatible": {
        "distance": 1.0,
        "highway_type": 1.0,
        "surface": 1.5,
        "smoothness": 1.0,
        "safety": 0.5
    }
}
