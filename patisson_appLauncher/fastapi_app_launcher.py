from dataclasses import dataclass
from typing import Callable

from ariadne import load_schema_from_path, make_executable_schema
from ariadne.asgi import GraphQL
from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from patisson_errors.fastapi import validation_exception_handler
from patisson_graphql.fastapi_handlers import graphql_server

from patisson_appLauncher.base_app_launcher import AppStarter, BaseAppLauncher


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
            
        print(f'Successfully connected to jaeger')


    def add_sync_consul_health_path(self, path: str = '/health', 
                               rout_func: Callable = consul_health_check):
        @self.app.get(path)
        def wrapper(): rout_func()
        print('added sync consul health check path')
        
    
    def add_async_ariadne_graphql_route(self, 
            resolvers: list, session_gen,
            url_path: str = '/graphql', 
            path_to_schema: str = 'app/api/graphql/schema.graphql',
            graphql_server: Callable = graphql_server,
            debug: bool = False):
        
        type_defs = load_schema_from_path(path_to_schema)
        schema = make_executable_schema(type_defs, resolvers)  
        
        @self.router.post(url_path)
        async def graphql_route(request):
            return await graphql_server(
                request=request, 
                schema=schema, 
                session_gen=session_gen()
            )
        
        graphql_app = GraphQL(schema, debug=debug)
        self.router.add_route(url_path, graphql_app)  # type: ignore[reportArgumentType]
        
        print('added async graphql (ariadne) route')
        
    
    def include_router(self, *args, prefix='/api', **kwargs):
        self.app.include_router(self.router, *args, prefix=prefix, **kwargs)
        print('include router in app')
            

class UvicornFastapiAppLauncher(BaseFastapiAppLauncher):
    
    def app_run(self):
        AppStarter.uvicorn_run(
            asgi_app=self.app, 
            host=self.host, 
            port=self.socket_close(self.socket_, self.port)
            )
    
    
