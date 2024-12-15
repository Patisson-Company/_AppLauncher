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

## Usage

### BaseAppLauncher

The `BaseAppLauncher` class is designed to be extended by your own application launchers. It sets up the basic infrastructure needed to launch and register services.

```python
from patisson_appLauncher.base_app_launcher import BaseAppLauncher

class MyAppLauncher(BaseAppLauncher):
    def app_run(self):
        # Implement the logic for running your app
        pass

app_launcher = MyAppLauncher(service_name="MyService", host="localhost")
```

This class will automatically handle the socket binding and service registration with Consul.

### AppStarter

For applications that use frameworks like FastAPI or Flask, `AppStarter` provides methods to run the application with `uvicorn` or `gunicorn`.

```python
from patisson_appLauncher.fastapi_app_launcher import AppStarter

AppStarter.uvicorn_run(asgi_app, host="localhost", port=8000)
```

This utility abstracts the command-line execution of your application server, providing an easy way to launch microservices.

## Example: FastAPI Application

Here’s how you can use `_AppLauncher` to start a FastAPI service with Consul registration and health checks:

```python
from fastapi import FastAPI
from patisson_appLauncher.base_app_launcher import BaseAppLauncher
from patisson_appLauncher.fastapi_app_launcher import AppStarter

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World"}

class FastAPIAppLauncher(BaseAppLauncher):
    def app_run(self):
        AppStarter.uvicorn_run(asgi_app=app, host="localhost", port=8000)

app_launcher = FastAPIAppLauncher(service_name="FastAPIService", host="localhost")
```

## Classes and Methods

### `BaseAppLauncher`

- **`get_socket(port: Optional[str | int])`**: Creates a socket, binds it to the specified port, and returns the socket and port number.
- **`socket_close(socket: socket.socket, port: SocketPort)`**: Closes the socket connection.
- **`consul_register(check_path='/health', check_interval='30s', check_timeout='3s')`**: Registers the service in Consul with a health check.
- **`app_run()`**: Abstract method that should be implemented by subclasses to define how the app runs.

### `AppStarter`

- **`uvicorn_run(asgi_app, host: str, port: int)`**: Runs the FastAPI app using `uvicorn`.
- **`gunicorn_run(host: str, port: int, app_path: str, workers: str = '1')`**: Runs the app using `gunicorn`.

