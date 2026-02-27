from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .models import Telemetry
from .routes import router

app = FastAPI()

allow_origins=[
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://velosv2.netlify.app/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Vehicle Telemetry SQL Backend Running"}