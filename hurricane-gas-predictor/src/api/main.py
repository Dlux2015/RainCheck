"""FastAPI application — Hurricane Gas Predictor API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .routers import storm, signal, prices

load_dotenv()

app = FastAPI(
    title="Hurricane Gas Predictor",
    description="Predicts optimal gas buying windows during Atlantic hurricane events",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(storm.router, prefix="/storm", tags=["storm"])
app.include_router(signal.router, prefix="/signal", tags=["signal"])
app.include_router(prices.router, prefix="/prices", tags=["prices"])


@app.get("/health")
def health():
    return {"status": "ok"}
