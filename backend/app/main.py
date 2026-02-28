from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from .database import engine, Base
from .routes import router
from .auth_routes import router as auth_router
from .limiter import limiter
from .logging_config import setup_logging
from .middleware import register_middlewares


app = FastAPI()

# Setup logging
logger = setup_logging()

# Register custom middleware (logging + security headers + global error handler)
register_middlewares(app, logger)

# Rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://velosv2.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Vehicle Telemetry SQL Backend Running"}