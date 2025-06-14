# -*- coding: utf-8 -*-
"""
Jupiter SCADA Package Initializer.

This file initializes the `jupiter_scada` Python package, making its
modules available for import.

It also sets up package-level constants and a basic logging configuration.
"""

import logging
import os

# --- Package Information ---
# PEP 396: Defining a __version__ attribute in a package's __init__.py
# This is the single source of truth for the package version.
__version__ = "0.1.0"
__author__ = "Jupiter SCADA Development Team"
__email__ = ""  # Add a contact email if desired
__description__ = "A simple open source SCADA software for OPC UA communication."


# --- Basic Logging Configuration ---
# Configure a basic logger for the entire application. Sub-modules can get this
# logger by calling `logging.getLogger(__name__)`.
# The logging level can be controlled via an environment variable for flexibility
# in different environments (e.g., DEBUG in development, INFO in production).
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Get a logger for the package
logger = logging.getLogger(__name__)
logger.info(f"Initializing Jupiter SCADA v{__version__}")
logger.debug(f"Logging level set to '{LOG_LEVEL}'")


# --- Public API Exports (optional) ---
# This section can be used to expose key classes or functions from sub-modules
# at the top level of the package, simplifying imports for users of the package.
# For example:
#
# from .web.app import app
# from .opcua.client import OpcuaClient
#
# __all__ = [
#     "app",
#     "OpcuaClient",
# ]
#
# For now, we will let users import directly from the sub-modules.