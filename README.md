# _AppLauncher

_AppLauncher_ is a Python module designed to help in the smooth launch and management of microservices. It includes utility functions and classes to set up, run, and register services with a health check system, simplifying deployment in distributed systems.

## Key Features

- **BaseAppLauncher**: A base class for managing microservices, including automatic socket binding, service registration with Consul, and initialization tasks.
- **AppStarter**: Utility to run services using `uvicorn` or `gunicorn`, commonly used for ASGI and WSGI applications respectively.
- **Consul Integration**: Enables automatic registration and health checks for services with Consul.
- **Socket Management**: Includes methods for managing socket ports dynamically.
- **Health Checks**: Automatic integration with health check paths to ensure service availability.

## Installation

To install, simply use pip:

```bash
pip install git+https://github.com/Patisson-Company/_AppLauncher
```

## Framework support

- **FastApi**: The logic of the basic launcher has been updated for the framework. Use the `patisson_appLauncher.fastapi_app_launcher`