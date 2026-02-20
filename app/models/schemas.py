"""
OpenRoute Navigator - Pydantic Schemas

Data models for request/response validation
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class VehicleParams(BaseModel):
    """Vehicle parameters for route calculation"""
    vehicle_type: Literal["car", "truck", "motorcycle"] = Field(
        default="car",
        description="Type of vehicle"
    )
    height: Optional[float] = Field(
        default=None,
        description="Vehicle height in meters",
        ge=0,
        le=10
    )
    weight: Optional[float] = Field(
        default=None,
        description="Vehicle weight in metric tons",
        ge=0,
        le=100
    )


class Coordinates(BaseModel):
    """Geographic coordinates"""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class RouteRequest(BaseModel):
    """Route calculation request"""
    origin: str | Coordinates = Field(
        ...,
        description="Origin address or coordinates"
    )
    destination: str | Coordinates = Field(
        ...,
        description="Destination address or coordinates"
    )
    vehicle: Optional[VehicleParams] = Field(
        default_factory=VehicleParams,
        description="Vehicle parameters"
    )

    @field_validator('origin', 'destination', mode='before')
    @classmethod
    def validate_location(cls, v):
        """Allow both string addresses and coordinate dictionaries"""
        if isinstance(v, dict):
            return Coordinates(**v)
        return v


class Alert(BaseModel):
    """Route alert"""
    level: Literal["green", "yellow", "red"] = Field(
        ...,
        description="Alert severity level"
    )
    message: str = Field(
        ...,
        description="Alert message"
    )
    location: Optional[Coordinates] = Field(
        default=None,
        description="Location where alert applies"
    )


class Route(BaseModel):
    """Individual route information"""
    type: Literal["fastest", "best_surface", "safest", "truck_compatible"] = Field(
        ...,
        description="Route optimization criterion"
    )
    distance_km: float = Field(
        ...,
        description="Total distance in kilometers",
        ge=0
    )
    geometry: List[List[float]] = Field(
        ...,
        description="Route geometry as list of [lon, lat] coordinates"
    )
    alerts: List[Alert] = Field(
        default_factory=list,
        description="Alerts along the route"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Human-readable route summary"
    )


class RouteResponse(BaseModel):
    """Route calculation response"""
    routes: List[Route] = Field(
        ...,
        description="Alternative routes with different optimization criteria"
    )
    origin_coords: Coordinates = Field(
        ...,
        description="Resolved origin coordinates"
    )
    destination_coords: Coordinates = Field(
        ...,
        description="Resolved destination coordinates"
    )


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
