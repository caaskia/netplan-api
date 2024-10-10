#!/usr/bin/python

# Run app:
# DEV: sudo uvicorn rest:app --reload --host 0.0.0.0 --port 8080
# PROD: sudo gunicorn -w 4 -b 0.0.0.0:8080 -k uvicorn.workers.UvicornWorker main:app

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

import log
from api import netplan, station, network

logger = log.setup_custom_logger("root")

VERSION = "0.0.1"


@asynccontextmanager
async def startup_and_shutdown(app: FastAPI):
    yield


app = FastAPI(
    title="netplan_api",
    docs_url="/api",
    openapi_url="/api/api.json",
    default_response_class=ORJSONResponse,
    lifespan=startup_and_shutdown,
)

app.include_router(netplan.router, prefix="/api/netplan", tags=["netplan"])
app.include_router(network.router, prefix="/api/network", tags=["network"])
app.include_router(station.router, prefix="/api/station", tags=["station"])

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f" Netplan API REST started; version = {VERSION}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080)
