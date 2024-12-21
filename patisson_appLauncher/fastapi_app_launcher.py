"""Complements the basic module, simplifying integration with fastapi."""

from dataclasses import dataclass
from typing import Awaitable, Callable, Collection, Optional

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

from patisson_appLauncher.base_app_launcher import AppStarter, BaseAppLauncher
from patisson_appLauncher.printX import block_decorator


def consul_health_check() -> JSONResponse:
    """
    Perform a health check for Consul.

    Returns:
        JSONResponse: A JSON response with status 200 if successful, or 503 if an error occurs.
    """
    try:
        return JSONResponse(status_code=200, content={"status": "ok"})
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unavailable", "error": str(e)})


@dataclass
class BaseFastapiAppLauncher(BaseAppLauncher):
    """
    A base launcher class for setting up and running a FastAPI application.

    Attributes:
        app (FastAPI): The FastAPI application instance.
        router (APIRouter): The API router instance.
    """

    app: FastAPI
    router: APIRouter

    def add_route(self, **kwargs) -> None:
        """
        Add a route to the FastAPI application.

        This method serves as a wrapper around FastAPI's `add_api_route` method,
        allowing you to dynamically add routes to the application.

        Args:
            **kwargs: Arbitrary keyword arguments accepted by FastAPI's `add_api_route` method.
                Common arguments include:
                - **path** (str): The URL path for the route.
                - **endpoint** (Callable): The function to handle requests to the route.
                - **methods** (List[str]): List of HTTP methods (e.g., ["GET", "POST"]).
                - **name** (str): A name for the route.
                - **tags** (List[str]): Tags for grouping routes in the OpenAPI documentation.
                - **dependencies** (List[Depends]): Dependencies for the route.

        Returns:
            None
        """
        self.router.add_api_route(**kwargs)

    @block_decorator(["add token middleware"])
    def add_token_middleware(
        self, get_token: Callable[..., Awaitable[str]], excluded_paths: Optional[Collection[str]] = None
    ) -> None:
        """
        Add middleware to include an Authorization token in responses.

        Args:
            get_token (Callable[..., Awaitable[str]]): Function to retrieve the token.
            excluded_paths (Collection[str]): A collection of paths to exclude from token addition.
        """
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.types import ASGIApp

        class AuthMiddleware(BaseHTTPMiddleware):
            """
            Middleware to handle adding Authorization headers to responses.

            Args:
                app (ASGIApp): The ASGI application.
                excluded_paths (Collection[str]): Paths to exclude from token addition.
            """

            def __init__(self, app: ASGIApp, excluded_paths: Collection[str]) -> None:
                super().__init__(app)
                self.excluded_paths = excluded_paths

            async def dispatch(self, request: Request, call_next) -> Response:
                response = await call_next(request)
                if request.url.path not in self.excluded_paths:
                    response.headers["Authorization"] = await get_token()
                return response

        self.app.add_middleware(AuthMiddleware, excluded_paths=excluded_paths if excluded_paths else [])

    @block_decorator(["Connecting to Jaeger"])
    def add_jaeger(
        self,
        add_validation_exception_handler: bool = True,
        validation_exception_handler: Optional[ExceptionHandler] = None,
    ) -> None:
        """
        Configure OpenTelemetry and connects to Jaeger for tracing.

        Args:
            add_validation_exception_handler (bool): Whether to add a handler for validation exceptions.
            validation_exception_handler (Optional[ExceptionHandler]): Custom handler for
                validation exceptions.
        """
        from opentelemetry import trace
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.trace import Status, StatusCode

        async def validation_exception_handler_(
            request: Request, exc: RequestValidationError
        ) -> JSONResponse:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("validation-error") as span:
                span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                span.set_attribute("http.url", str(request.url))
                span.set_attribute("http.method", request.method)
            return JSONResponse(
                status_code=422,
                content={"detail": exc.errors()},
            )

        trace.set_tracer_provider(TracerProvider(resource=Resource.create({SERVICE_NAME: self.service_name})))
        jaeger_exporter = JaegerExporter()
        trace.get_tracer_provider().add_span_processor(  # type: ignore[reportAttributeAccessIssue]
            BatchSpanProcessor(jaeger_exporter)
        )
        FastAPIInstrumentor.instrument_app(self.app)

        if add_validation_exception_handler:
            self.app.add_exception_handler(
                RequestValidationError,
                (
                    validation_exception_handler
                    if validation_exception_handler is not None
                    else validation_exception_handler_
                ),  # type: ignore[reportArgumentType]
            )

    @block_decorator(["Added a synchronous health check route for Consul"])
    def add_sync_consul_health_path(
        self, path: Optional[str] = None, rout_func: Callable = consul_health_check
    ) -> None:
        """
        Add a synchronous health check route for Consul.

        Args:
            path (str | None): The path for the health check route.
                        If the value is None, the string f'/health' is used
            rout_func (Callable): The function to execute for the health check.
        """
        self.health_path = path if path else "/health"
        self.router.add_api_route(self.health_path, rout_func, methods=["GET"])

    @block_decorator(["Include router in app"])
    def include_router(self, *args, prefix="", **kwargs):
        """
        Includes the API router in the FastAPI application.

        Args:
            prefix (str): URL prefix for the router.
            *args: Additional positional arguments for the router.
            **kwargs: Additional keyword arguments for the router.
        """
        self.app.include_router(self.router, *args, prefix=prefix, **kwargs)


class UvicornFastapiAppLauncher(BaseFastapiAppLauncher):
    """Launcher class for running a FastAPI application with Uvicorn."""

    def app_run(self) -> None:
        """Run the FastAPI application using Uvicorn."""
        AppStarter.uvicorn_run(
            asgi_app=self.app, host=self.host, port=self.socket_close(self.socket_, self.port)
        )
