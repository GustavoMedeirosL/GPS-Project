"""
OpenRoute Navigator - Geocoding Service

Handles address-to-coordinate conversion using Nominatim API
"""

import requests
from typing import Tuple, Optional
from app.models.schemas import Coordinates


class GeocodingService:
    """Service for geocoding addresses using Nominatim"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.headers = {
            "User-Agent": "OpenRouteNavigator/1.0"
        }
    
    def geocode(self, address: str) -> Optional[Coordinates]:
        """
        Convert address to coordinates
        
        Args:
            address: Address string to geocode
            
        Returns:
            Coordinates object or None if geocoding fails
        """
        try:
            params = {
                "q": address,
                "format": "json",
                "limit": 1
            }
            
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json()
            
            if not results:
                return None
            
            result = results[0]
            return Coordinates(
                lat=float(result["lat"]),
                lon=float(result["lon"])
            )
            
        except Exception as e:
            print(f"Geocoding error for '{address}': {e}")
            return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """
        Convert coordinates to address
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Address string or None if reverse geocoding fails
        """
        try:
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json"
            }
            
            response = requests.get(
                f"{self.base_url}/reverse",
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("display_name")
            
        except Exception as e:
            print(f"Reverse geocoding error for ({lat}, {lon}): {e}")
            return None
    
    def validate_coordinates(self, coords: Coordinates) -> bool:
        """
        Validate that coordinates are within valid ranges
        
        Args:
            coords: Coordinates to validate
            
        Returns:
            True if valid, False otherwise
        """
        return (
            -90 <= coords.lat <= 90 and
            -180 <= coords.lon <= 180
        )
