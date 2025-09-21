from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth.router import router as auth_router
from .companies.router import router as companies_router
from .lines.router import router as lines_router
from .stations.router import router as stations_router
from .routes.router import router as routes_router
from .tickets.router import router as tickets_router
from .journeys.router import router as journeys_router
from .distance_calculation.router import router as distance_calculation_router
from .regions.routes import router as regions_router
from .route_management.router import router as route_management_router
from .intersection_management.router import router as intersection_management_router
from .users.router import router as users_router
from .roles.router import router as roles_router
from .graph_generator.router import router as graph_generator_router
# Route segments router removed
# from .route_segments.router import router as route_segments_router

app = FastAPI(
    title="Train Transport Booking System",
    description="A comprehensive train booking system for Bangkok and Osaka",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Explicit frontend origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(regions_router, prefix="/api")
app.include_router(companies_router, prefix="/api/companies", tags=["Companies"])
app.include_router(lines_router, prefix="/api/lines", tags=["Lines"])
app.include_router(stations_router, prefix="/api/stations", tags=["Stations"])
app.include_router(routes_router, prefix="/api/routes", tags=["Routes"])
app.include_router(distance_calculation_router, prefix="/api/distance", tags=["Distance Calculation"])
app.include_router(tickets_router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(journeys_router, prefix="/api/journeys", tags=["Journeys"])
app.include_router(route_management_router, prefix="/api")
app.include_router(intersection_management_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(roles_router, prefix="/api")
app.include_router(graph_generator_router, prefix="/api")
# app.include_router(route_segments_router, prefix="/api/route-segments", tags=["route-segments"])

@app.get("/")
async def root():
    return {"message": "Train Transport Booking System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
