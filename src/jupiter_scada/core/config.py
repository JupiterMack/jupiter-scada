# -*- coding: utf-8 -*-
"""
Configuration loading and management for the Jupiter SCADA application.

This module provides a centralized configuration object (`settings`) that loads
settings from environment variables and a YAML configuration file. It is
implemented as a singleton class to ensure configuration is loaded only once.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Set up a logger for this module
logger = logging.getLogger(__name__)


class Settings:
    """
    A singleton class to manage application configuration.

    It loads settings from the following sources:
    1. A `config.yaml` file located in the `config/` directory at the project root.
    2. Environment variables (e.g., for sensitive data like server URLs).
    """

    _instance = None

    def __new__(cls):
        """Ensures that only one instance of the Settings class is created."""
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            # Call an internal initializer to avoid re-initialization on every access
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """
        Initializes the configuration by loading all sources.
        This method is called only once when the instance is created.
        """
        logger.info("Initializing application settings...")

        # 1. Define project root and configuration paths
        self.project_root: Path = self._find_project_root()
        self.config_file_path: Path = self.project_root / "config" / "config.yaml"
        logger.info(f"Project root identified as: {self.project_root}")
        logger.info(f"Expecting configuration file at: {self.config_file_path}")

        # 2. Load settings from environment variables
        self._load_env_vars()

        # 3. Load settings from YAML file
        self._load_yaml_config()

        logger.info("Settings initialization complete.")

    def _find_project_root(self) -> Path:
        """
        Finds the project root directory by searching upwards for a marker file.
        The marker file is `.gitignore` in this case.
        """
        current_path = Path(__file__).resolve()
        # Search up the directory tree from the current file's location
        while current_path != current_path.parent:
            if (current_path / ".gitignore").exists():
                return current_path
            current_path = current_path.parent
        raise FileNotFoundError(
            "Could not find project root. The '.gitignore' marker file was not found."
        )

    def _load_env_vars(self) -> None:
        """Loads configuration from environment variables."""
        # Note: Uvicorn/FastAPI can load .env files automatically if specified.
        # We just read the loaded environment variables here.
        default_url = "opc.tcp://localhost:4840/"
        self.opcua_server_url: str = os.getenv("OPCUA_SERVER_URL", default_url)

        if self.opcua_server_url == default_url:
            logger.warning(
                "OPCUA_SERVER_URL not set in environment. Using default: %s",
                self.opcua_server_url,
            )
        else:
            logger.info("Loaded OPCUA_SERVER_URL from environment.")

    def _load_yaml_config(self) -> None:
        """Loads the main configuration from the `config.yaml` file."""
        # Set default empty values
        self.tags: List[Dict[str, Any]] = []
        self.raw_yaml_config: Optional[Dict[str, Any]] = None

        if not self.config_file_path.is_file():
            logger.error(
                "Configuration file not found at '%s'.", self.config_file_path
            )
            logger.error(
                "Please create 'config.yaml' from 'config/config.yaml.example' "
                "and define your OPC UA tags."
            )
            # Return with empty defaults to allow the application to start,
            # though it will not monitor any tags.
            return

        try:
            with open(self.config_file_path, "r", encoding="utf-8") as f:
                self.raw_yaml_config = yaml.safe_load(f)

            if self.raw_yaml_config:
                # Get the list of tags, default to an empty list if 'tags' key is missing
                self.tags = self.raw_yaml_config.get("tags", [])
                if not self.tags:
                    logger.warning(
                        "No 'tags' defined in '%s'. The application will run but monitor no data.",
                        self.config_file_path
                    )
                else:
                    logger.info(
                        "Successfully loaded %d tags from '%s'.",
                        len(self.tags),
                        self.config_file_path,
                    )
            else:
                logger.warning("Configuration file '%s' is empty.", self.config_file_path)

        except yaml.YAMLError as e:
            logger.exception(
                "Error parsing YAML configuration file '%s'. Please check its syntax.",
                self.config_file_path,
            )
        except Exception as e:
            logger.exception(
                "An unexpected error occurred while reading '%s'.",
                self.config_file_path,
            )


# Create a single, globally accessible instance of the Settings class.
# Other modules can import this object to access configuration values.
# e.g., from jupiter_scada.core.config import settings
settings = Settings()