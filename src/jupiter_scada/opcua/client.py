# -*- coding: utf-8 -*-
"""
OPC UA Client for Jupiter SCADA.

This module provides the `OpcuaClient` class, which handles all interactions
with the OPC UA server. It uses the `asyncua` library to manage connections,
subscriptions, and data handling in an asynchronous manner.

The client is designed as a singleton, with a single instance (`opcua_client`)
instantiated at the module level for use throughout the application.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from asyncua import Client, ua
from asyncua.common.subscription import Subscription

from jupiter_scada.core.config import settings
from jupiter_scada.models.opc import LiveTag, Tag

# --- Constants ---
RECONNECT_INTERVAL_SECONDS = 10

# --- Logger ---
logger = logging.getLogger(__name__)


class SubscriptionHandler:
    """
    Handles data change notifications from an OPC UA subscription.
    This class is instantiated by the OpcuaClient and its methods are
    called by the asyncua library when new data is available.
    """

    def __init__(self, client: 'OpcuaClient'):
        """
        Initializes the subscription handler.

        Args:
            client: The OpcuaClient instance that owns this handler.
        """
        self._client = client
        logger.info("SubscriptionHandler initialized.")

    def datachange_notification(self, node: ua.Node, val: Any, data: ua.DataChangeNotification):
        """
        Callback for data change events.

        Args:
            node: The node that has changed.
            val: The new value of the node.
            data: The full data change notification object.
        """
        asyncio.create_task(self._client.update_tag_value_from_node(node, data.monitored_item.Value))
        logger.debug(f"Data change: Node={node}, Value={val}")

    def event_notification(self, event: ua.EventNotificationList):
        """Callback for event notifications."""
        logger.info(f"Event notification received: {event}")


class OpcuaClient:
    """
    Manages the connection and data exchange with an OPC UA server.
    """

    def __init__(self):
        """Initializes the OpcuaClient."""
        self.server_url: str = settings.opcua.server_url
        self.client: Client = Client(url=self.server_url)
        self.subscription: Optional[Subscription] = None
        self.sub_handler: SubscriptionHandler = SubscriptionHandler(self)

        self._is_connected: bool = False
        self._running: bool = False
        self._connection_task: Optional[asyncio.Task] = None
        self._data_store: Dict[str, LiveTag] = {}
        self._node_map: Dict[ua.Node, str] = {}  # Maps asyncua.Node back to tag name
        self._lock = asyncio.Lock()

        logger.info(f"OpcuaClient initialized for server: {self.server_url}")
        self._initialize_data_store()

    def _initialize_data_store(self):
        """Populates the data store with tags from config, setting initial null state."""
        for group in settings.opc_tags:
            for tag in group.tags:
                self._data_store[tag.name] = LiveTag(
                    name=tag.name,
                    node_id=tag.node_id,
                    value=None,
                    status="Uncertain",
                    timestamp=datetime.utcnow()
                )

    @property
    def is_connected(self) -> bool:
        """Returns the current connection status."""
        return self._is_connected

    async def start(self):
        """Starts the client's connection management loop."""
        if self._running:
            logger.warning("Client is already running.")
            return

        logger.info("Starting OpcuaClient...")
        self._running = True
        self._connection_task = asyncio.create_task(self._connection_manager())

    async def stop(self):
        """Stops the client and disconnects from the server."""
        if not self._running:
            logger.warning("Client is not running.")
            return

        logger.info("Stopping OpcuaClient...")
        self._running = False
        if self._connection_task:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                logger.info("Connection manager task cancelled.")
        await self.disconnect()

    async def _connection_manager(self):
        """A background task to manage the connection state."""
        logger.info("Connection manager started.")
        while self._running:
            if not self.is_connected:
                try:
                    await self.connect()
                    await self._initialize_subscriptions()
                except Exception as e:
                    logger.error(f"Connection failed: {e}. Retrying in {RECONNECT_INTERVAL_SECONDS}s...")
                    await self.disconnect()  # Ensure clean state
            await asyncio.sleep(RECONNECT_INTERVAL_SECONDS)
        logger.info("Connection manager stopped.")

    async def connect(self):
        """Establishes a connection to the OPC UA server."""
        logger.info(f"Attempting to connect to {self.server_url}...")
        await self.client.connect()
        self._is_connected = True
        logger.info("Successfully connected to OPC UA server.")

    async def disconnect(self):
        """Disconnects from the OPC UA server."""
        if self.is_connected:
            try:
                await self.client.disconnect()
                logger.info("Successfully disconnected from OPC UA server.")
            except Exception as e:
                logger.error(f"Error during disconnection: {e}")
            finally:
                self._is_connected = False
                self.subscription = None
                self._node_map = {}

    async def _initialize_subscriptions(self):
        """Creates subscriptions for all configured tags."""
        if not self.is_connected:
            logger.warning("Cannot initialize subscriptions, client not connected.")
            return

        logger.info("Initializing subscriptions...")
        try:
            self.subscription = await self.client.create_subscription(500, self.sub_handler)
            nodes_to_subscribe = []
            tags_to_process: List[Tag] = [tag for group in settings.opc_tags for tag in group.tags]

            for tag_config in tags_to_process:
                try:
                    node = self.client.get_node(tag_config.node_id)
                    nodes_to_subscribe.append(node)
                    self._node_map[node] = tag_config.name
                except ua.UaError as e:
                    logger.error(f"Failed to get node for tag '{tag_config.name}' ({tag_config.node_id}): {e}")

            if nodes_to_subscribe:
                await self.subscription.subscribe_data_change(nodes_to_subscribe)
                logger.info(f"Subscribed to {len(nodes_to_subscribe)} nodes.")
                # Perform an initial read to populate data immediately
                await self._populate_initial_data(nodes_to_subscribe)

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            await self.disconnect()

    async def _populate_initial_data(self, nodes: List[ua.Node]):
        """Performs an initial read of all subscribed nodes."""
        logger.info("Performing initial data read for all subscribed nodes.")
        try:
            values = await self.client.read_values(nodes)
            data_values = await self.client.read_data_values(nodes)

            for i, node in enumerate(nodes):
                await self.update_tag_value_from_node(node, data_values[i])

        except Exception as e:
            logger.error(f"Error during initial data population: {e}")

    async def update_tag_value_from_node(self, node: ua.Node, data_value: ua.DataValue):
        """Updates the internal data store for a given tag based on a new DataValue."""
        tag_name = self._node_map.get(node)
        if not tag_name:
            logger.warning(f"Received update for an unmapped node: {node}")
            return

        async with self._lock:
            if tag_name in self._data_store:
                live_tag = self._data_store[tag_name]
                live_tag.value = data_value.Value.Value
                live_tag.status = data_value.StatusCode.name
                live_tag.timestamp = data_value.SourceTimestamp or datetime.utcnow()
                logger.debug(f"Updated tag '{tag_name}': Value={live_tag.value}, Status={live_tag.status}")
            else:
                logger.warning(f"Received update for tag '{tag_name}' not in data store.")

    async def get_all_tags(self) -> List[LiveTag]:
        """
        Retrieves a list of all monitored tags with their current data.

        Returns:
            A list of LiveTag objects.
        """
        async with self._lock:
            # Return a copy to prevent mutation outside the client
            return list(self._data_store.values())

    async def get_tag_by_name(self, name: str) -> Optional[LiveTag]:
        """
        Retrieves a single tag by its configured name.

        Args:
            name: The unique name of the tag.

        Returns:
            A LiveTag object if found, otherwise None.
        """
        async with self._lock:
            # Return a copy
            return self._data_store.get(name)

    async def read_value(self, node_id: str) -> Any:
        """
        Performs a one-off read of a specific node.

        Args:
            node_id: The NodeId string to read.

        Returns:
            The value of the node.
        """
        if not self.is_connected:
            raise ConnectionError("OPC UA client is not connected.")
        try:
            node = self.client.get_node(node_id)
            value = await node.read_value()
            logger.info(f"Read value from {node_id}: {value}")
            return value
        except Exception as e:
            logger.error(f"Failed to read value from {node_id}: {e}")
            raise

    async def write_value(self, node_id: str, value: Any, variant_type: ua.VariantType):
        """
        Writes a value to a specific node.

        Args:
            node_id: The NodeId string to write to.
            value: The value to write.
            variant_type: The ua.VariantType of the value.
        """
        if not self.is_connected:
            raise ConnectionError("OPC UA client is not connected.")
        try:
            node = self.client.get_node(node_id)
            variant = ua.Variant(value, variant_type)
            await node.write_value(variant)
            logger.info(f"Wrote value to {node_id}: {value}")
        except Exception as e:
            logger.error(f"Failed to write value to {node_id}: {e}")
            raise


# --- Singleton Instance ---
# This single instance will be imported and used by other modules (e.g., API).
opcua_client = OpcuaClient()