from dataclasses import dataclass
from typing import Callable

from fastapi.responses import JSONResponse
from patisson_appLauncher.base_app_launcher import AppStarter, BaseAppLauncher
from abc import ABC
from fastapi import FastAPI, APIRouter
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from fastapi.exceptions import RequestValidationError
from patisson_errors.fastapi import validation_exception_handler


def consul_health_check():
    try:
        return JSONResponse(status_code=200, content={"status": "ok"})
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unavailable", "error": str(e)})


@dataclass
class BaseFastapiAppLauncher(BaseAppLauncher):
    app: FastAPI
    router: APIRouter
    
    def add_jaeger(self, add_validation_exception_handler: bool = True,
                   validation_exception_handler: Callable = validation_exception_handler):
        
        trace.set_tracer_provider(
            TracerProvider(
                resource=Resource.create({SERVICE_NAME: self.service_name})
            )
        )
        jaeger_exporter = JaegerExporter()
        trace.get_tracer_provider().add_span_processor(  # type: ignore[reportAttributeAccessIssue]
            BatchSpanProcessor(jaeger_exporter)
        )
        FastAPIInstrumentor.instrument_app(self.app)
        
        if add_validation_exception_handler:
            self.app.add_exception_handler(RequestValidationError, validation_exception_handler)


    def add_consul_health_path(self, path: str = '/health', 
                               rout_func: Callable = consul_health_check):
        @self.app.get(path)
        def wrapper(): rout_func()
            

class UvicornFastapiAppLauncher(BaseFastapiAppLauncher):
    
    def app_run(self):
        AppStarter.uvicorn_run(
            asgi_app=self.app, 
            host=self.host, 
            port=self.socket_close(self.socket_, self.port)
            )
    
    
