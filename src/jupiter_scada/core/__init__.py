# -*- coding: utf-8 -*-
"""
Jupiter SCADA Core Package.

This package contains the core business logic of the Jupiter SCADA application.
It is responsible for handling the OPC UA communication, managing the application
configuration, and defining the primary data structures used throughout the system.

The key components are exposed at the package level for easy access from other
parts of the application, such as the API layer. This allows for cleaner imports,
for example: `from jupiter_scada.core import OpcuaClient`.
"""

# This __init__.py file is intentionally left blank.
#
# In a Python project, the primary purpose of an __init__.py file is to mark the
# directory as a package, allowing its modules to be imported.
#
# While it can be used to create a unified namespace by importing key classes
# from its submodules (e.g., `from .opcua_client import OpcuaClient`),
# for simplicity and to avoid potential circular import issues as the project
# grows, we will rely on direct imports from the specific modules within the
# `core` package.
#
# For example, to use the OPC UA client, one would use:
# `from jupiter_scada.core.opcua_client import OpcuaClient`
#
# This approach keeps the dependencies explicit and the structure clear.

```