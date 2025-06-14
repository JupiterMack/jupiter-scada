# -*- coding: utf-8 -*-
"""
Main FastAPI application for Jupiter SCADA.

This module initializes the FastAPI application, includes the API routers,
configures static file serving for the web frontend, and manages the
lifecycle of the OPC UA client connection.
"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from jupiter_scada import __version__
from jupiter_scada.api.endpoints import router as api_router
# This import assumes the OPC UA client logic is structured in a dedicated package.
# This client is responsible for all communication with the OPC UA server.
from jupiter_scada.opcua.client import OpcuaClient

# --- Setup Logging ---
logger = logging.getLogger(__name__)

# --- Path Definitions ---
# Define paths relative to this file's location to ensure they work correctly
# regardless of the current working directory.
# `server.py` is in `src/jupiter_scada/api/`
# The project root for assets (static, templates) is `src/jupiter_scada/`
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


# --- FastAPI Application Initialization ---
app = FastAPI(
    title="Jupiter SCADA",
    description="A simple open-source SCADA software for OPC UA communication.",
    version=__version__,
    # Customize the docs URLs to be nested under the API prefix for consistency
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# --- OPC UA Client Lifecycle Management ---
# The OpcuaClient is a singleton; we get its single instance here.
opcua_client = OpcuaClient.get_instance()

@app.on_event("startup")
async def startup_event():
    """
    Application startup logic:
    - Connects the OPC UA client to the configured server.
    - Starts the background subscription task to monitor tags.
    """
    logger.info("Application starting up...")
    try:
        await opcua_client.connect()
        # The subscription is started after the config is loaded,
        # which happens during client initialization.
        await opcua_client.start_subscription()
        logger.info("OPC UA client connected and subscription started.")
    except Exception as e:
        logger.critical(f"Failed to connect to OPC UA server on startup: {e}", exc_info=True)
        # In a production environment, you might want to implement a retry mechanism
        # or prevent the application from starting if the connection is critical.

@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown logic:
    - Disconnects the OPC UA client gracefully.
    """
    logger.info("Application shutting down...")
    await opcua_client.disconnect()
    logger.info("OPC UA client disconnected.")


# --- Mount Static Files for Frontend ---
# This serves files like CSS, JavaScript, and images for the web UI.
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info(f"Mounted static files directory: {STATIC_DIR}")
else:
    logger.warning(
        f"Static files directory not found at '{STATIC_DIR}'. "
        "Frontend assets will not be served."
    )

# --- Setup Template Engine for index.html ---
# Jinja2 is used to serve the main entrypoint of the frontend.
if TEMPLATES_DIR.is_dir():
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    logger.info(f"Initialized Jinja2 templates from: {TEMPLATES_DIR}")

    # --- Root Endpoint to Serve Frontend ---
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def serve_frontend(request: Request):
        """
        Serves the main `index.html` file which acts as the entry point
        for the web-based user interface (e.g., a single-page application).
        """
        logger.debug("Request for root path, serving index.html")
        return templates.TemplateResponse(
            "index.html", {"request": request, "title": "Jupiter SCADA"}
        )
else:
    logger.warning(
        f"Templates directory not found at '{TEMPLATES_DIR}'. "
        "The root '/' endpoint will not serve a web page."
    )
    # Provide a fallback JSON response if templates are not found.
    @app.get("/", include_in_schema=False)
    async def root_fallback():
        return {
            "message": "Jupiter SCADA API is running.",
            "api_docs": "/api/docs"
        }


# --- Include API Routers ---
# All routes from `endpoints.py` are included under the `/api` prefix.
# This keeps the API versionable and separate from the frontend routes.
app.include_router(api_router, prefix="/api")
logger.info("API router included with prefix '/api'.")
```