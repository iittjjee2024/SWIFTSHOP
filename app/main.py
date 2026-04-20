from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware
from app.middleware.logging import logging_middleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routes import users, products, orders, payments, admin, recommend
from app.database import create_tables
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="SwiftShop API",
    description="E-commerce backend API for SwiftShop",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(recommend.router, prefix="/api/v1")

@app.get("/api/v1")
async def api_root():
    return {
        "message": "SwiftShop Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

# Serve frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")

@app.get("/")
async def serve_root():
    frontend_file = os.path.join(frontend_dir, "swift.html")
    if os.path.exists(frontend_file):
        return FileResponse(frontend_file, media_type="text/html")
    return {"detail": "Frontend not found"}

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Override OpenAPI schema to use simple HTTPBearer instead of OAuth2
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste your token from POST /api/v1/users/login"
        }
    }
    for path in schema.get("paths", {}).values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi
