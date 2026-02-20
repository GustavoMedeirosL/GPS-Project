"""
OpenRoute Navigator - API Routes

FastAPI route definitions
"""

from fastapi import APIRouter, HTTPException, status
from typing import Union
from app.models.schemas import (
    RouteRequest,
    RouteResponse,
    ErrorResponse,
    Coordinates,
    VehicleParams
)
from app.services.geocoding import GeocodingService
from app.services.routing import RoutingService


router = APIRouter(prefix="/route", tags=["routing"])

geocoding_service = GeocodingService()
routing_service = RoutingService()


@router.post(
    "/calculate",
    response_model=RouteResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Calculate multi-criteria routes",
    description="""
    Calculate multiple route alternatives between origin and destination.
    
    Supports 4 optimization criteria:
    - **Fastest**: Minimizes travel time/distance
    - **Best Surface**: Prioritizes paved roads with good quality
    - **Safest**: Prefers lit roads with traffic controls
    - **Truck Compatible**: Only for trucks, excludes restricted roads
    
    Returns routes with geometry and alerts (green/yellow/red).
    """
)
async def calculate_route(request: RouteRequest):
    """
    Calculate routes between origin and destination
    
    Args:
        request: RouteRequest with origin, destination, and vehicle params
        
    Returns:
        RouteResponse with multiple route alternatives
    """
    try:
        # Resolve origin coordinates
        if isinstance(request.origin, str):
            origin_coords = geocoding_service.geocode(request.origin)
            if not origin_coords:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Could not geocode origin address: {request.origin}"
                )
        else:
            origin_coords = request.origin
            if not geocoding_service.validate_coordinates(origin_coords):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid origin coordinates"
                )
        
        # Resolve destination coordinates
        if isinstance(request.destination, str):
            dest_coords = geocoding_service.geocode(request.destination)
            if not dest_coords:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Could not geocode destination address: {request.destination}"
                )
        else:
            dest_coords = request.destination
            if not geocoding_service.validate_coordinates(dest_coords):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid destination coordinates"
                )
        
        # Calculate routes
        routes = routing_service.calculate_routes(
            origin=origin_coords,
            destination=dest_coords,
            vehicle=request.vehicle
        )
        
        return RouteResponse(
            routes=routes,
            origin_coords=origin_coords,
            destination_coords=dest_coords
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route calculation failed: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check if the routing service is operational"
)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "OpenRoute Navigator",
        "version": "1.0.0"
    }
