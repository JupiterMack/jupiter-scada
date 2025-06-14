# -*- coding: utf-8 -*-
"""
Jupiter SCADA OPC UA Communication Package.

This package encapsulates all the logic for interacting with an OPC UA server.
It provides a high-level client for connecting, subscribing to data changes,
and managing the communication lifecycle.

The primary component is the `OpcuaClient`, which acts as the main interface
for the rest of the application to communicate with the OPC UA server.
"""

from .client import OpcuaClient
from .handler import SubscriptionHandler

__all__ = [
    "OpcuaClient",
    "SubscriptionHandler",
]