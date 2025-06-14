# -*- coding: utf-8 -*-
"""
Jupiter SCADA Main Application Entry Point.

This script serves as the main entry point for the Jupiter SCADA application.
It orchestrates the entire application lifecycle, including:
- Loading configuration from environment variables and YAML files.
- Initializing and running the OPC UA client as a background asyncio task.
- Starting the FastAPI web server using Uvicorn to serve the API and frontend.
- Handling graceful shutdown on system signals (SIGINT, SIGTERM).
"""

import asyncio
import logging
import signal
from contextlib import suppress

import uvicorn

from jupiter_scada.api.server import app
from jupiter_scada.core.config import settings
from jupiter_scada.core.opcua_client import OpcuaClient

# Get a logger for this module.
# Logging is configured in `jupiter_scada/__init__.py`.
log = logging.getLogger(__name__)


async def shutdown(
    sig: signal.Signals, server: uvicorn.Server, opcua_task: asyncio.Task
):
    """
    Handles graceful shutdown of the application.

    This function is registered as a signal handler and is responsible for
    stopping the Uvicorn server and cancelling the background OPC UA client task.

    Args:
        sig: The signal that triggered the shutdown.
        server: The running Uvicorn server instance.
        opcua_task: The asyncio.Task for the OPC UA client.
    """
    log.warning(f"Received exit signal {sig.name}... Shutting down.")

    # 1. Initiate Uvicorn server shutdown. This will cause `await server.serve()`
    #    in the main function to return.
    log.info("Initiating Uvicorn server shutdown...")
    server.should_exit = True

    # 2. Cancel the background OPC UA client task.
    log.info("Cancelling OPC UA client task...")
    opcua_task.cancel()

    # Wait for the task to acknowledge cancellation.
    # The `suppress` context manager prevents the `CancelledError` from propagating.
    with suppress(asyncio.CancelledError):
        await opcua_task
    log.info("OPC UA client task successfully cancelled.")


async def main():
    """
    Main asynchronous function to orchestrate the application startup.
    """
    log.info("--- Starting Jupiter SCADA Application ---")
    log.info(f"Log level set to: {settings.LOG_LEVEL}")

    # 1. Initialize the singleton OPC UA client instance.
    # The client is configured using the global `settings` object.
    opcua_client = OpcuaClient.get_instance()

    # 2. Create a background task for the OPC UA client.
    # This task will handle connecting, creating subscriptions, and monitoring tags.
    opcua_task = asyncio.create_task(opcua_client.run())
    log.info("OPC UA client task created and started in the background.")

    # 3. Configure and create the Uvicorn server instance.
    config = uvicorn.Config(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.RELOAD_APP,
    )
    server = uvicorn.Server(config)

    # 4. Set up signal handlers for graceful shutdown.
    # This ensures that when Ctrl+C is pressed or a TERM signal is received,
    # the application components are shut down cleanly.
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, server, opcua_task))
        )

    # 5. Run the Uvicorn server.
    # This call is blocking and will run until the server is stopped by the
    # shutdown signal handler.
    log.info(f"Starting Uvicorn server on http://{settings.API_HOST}:{settings.API_PORT}")
    log.info("Press CTRL+C to stop.")
    try:
        await server.serve()
    finally:
        # This finally block ensures cleanup even if the server stops unexpectedly.
        if not opcua_task.done():
            log.info("Server stopped. Ensuring OPC UA client task is cancelled.")
            opcua_task.cancel()
            with suppress(asyncio.CancelledError):
                await opcua_task

    log.info("--- Jupiter SCADA has shut down gracefully ---")


def run():
    """
    Synchronous wrapper to start the asyncio event loop.
    """
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Application shutdown initiated by user.")


if __name__ == "__main__":
    # The `run()` function is called when the script is executed directly.
    run()
```