"""
OpenRoute Navigator - Main Application

FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes


# Create FastAPI application
app = FastAPI(
    title="OpenRoute Navigator",
    description="""
    Multi-criteria routing system using OpenStreetMap data.
    
    ## Features
    - **Multi-Criteria Routing**: Calculate routes optimized for speed, quality, safety, or truck compatibility
    - **OSM Integration**: Real-time data from OpenStreetMap via Overpass API
    - **Intelligent Alerts**: Green/Yellow/Red alerts for road conditions and restrictions
    - **Vehicle Restrictions**: Automatic filtering based on height, weight, and access limitations
    
    ## Routing Criteria
    1. **Fastest**: Minimizes distance with minimal penalties
    2. **Best Surface**: Prioritizes paved roads with good smoothness
    3. **Safest**: Prefers lit roads with traffic signals, avoids high-speed roads
    4. **Truck Compatible**: Excludes roads with height/weight restrictions (trucks only)
    """,
    version="1.0.0",
    contact={
        "name": "OpenRoute Navigator Team",
        "email": "contact@openroutenav.com"
    },
    license_info={
        "name": "MIT License"
    }
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(routes.router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to OpenRoute Navigator API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["health"])
async def health():
    """Application health check"""
    return {
        "status": "healthy",
        "application": "OpenRoute Navigator"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
