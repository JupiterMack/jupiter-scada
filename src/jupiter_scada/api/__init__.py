# -*- coding: utf-8 -*-
"""
Jupiter SCADA API Package.

This package contains the FastAPI application that exposes the SCADA data
and functionality over a RESTful API. It includes endpoint definitions,
data models (Pydantic), and other API-related utilities.

The main FastAPI application instance is typically created and configured in a
submodule within this package (e.g., `main.py` or `app.py`) and then imported
into other parts of the application.
"""

# This file makes the 'src/jupiter_scada/api' directory a Python package.
# It can be left empty, or it can be used to expose key components from
# its submodules to create a cleaner import path.
#
# For example, if you have a file `src/jupiter_scada/api/main.py` that
# creates the FastAPI app instance like `app = FastAPI()`, you could add
# the following line here:
#
# from .main import app
#
# This would allow other parts of the application to import the app via:
# `from jupiter_scada.api import app`
# instead of:
# `from jupiter_scada.api.main import app`