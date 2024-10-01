from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler
from patisson_appLauncher.base_app_launcher import AppStarter, BaseAppLauncher
from patisson_appLauncher.printX import (Block, BlockType, CallableWrapper,
                                         block_decorator)

def consul_health_check():
    try:
        return JSONResponse(status_code=200, content={"status": "ok"})
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unavailable", "error": str(e)})


@dataclass
class BaseFastapiAppLauncher(BaseAppLauncher):
    app: FastAPI
    router: APIRouter
    
    @block_decorator(['Connecting to Jaeger'])
    def add_jaeger(self, add_validation_exception_handler: bool = True,
                   validation_exception_handler: Optional[ExceptionHandler] = None):
        from opentelemetry import trace
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.trace import Status, StatusCode
        
        async def validation_exception_handler_(request: Request, 
                exc: RequestValidationError) -> JSONResponse:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("validation-error") as span:
                span.set_status(Status(StatusCode.ERROR, description=str(exc)))
                span.set_attribute("http.url", str(request.url))
                span.set_attribute("http.method", request.method)
            return JSONResponse(
                status_code=422,
                content={"detail": exc.errors()},
            )
        
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
            self.app.add_exception_handler(RequestValidationError, 
                validation_exception_handler if validation_exception_handler is not None
                else validation_exception_handler_)  # type: ignore[reportArgumentType]


    @block_decorator(['Added a synchronous health check route for Consul'])
    def add_sync_consul_health_path(self, path: str = '/health', 
                               rout_func: Callable = consul_health_check):
        @self.app.get(path)
        def wrapper(): rout_func()
        
    
    def add_async_ariadne_graphql_route(self, 
            resolvers: list, session_gen,
            url_path: str = '/graphql', 
            path_to_schema: str = 'app/api/graphql/schema.graphql',
            graphql_server: Optional[Callable] = None,
            debug: bool = False):
        from ariadne import load_schema_from_path, make_executable_schema, graphql
        from ariadne.asgi import GraphQL
        from graphql import GraphQLSchema
        from contextlib import _AsyncGeneratorContextManager
        
        async def graphql_server_(request: Request, schema: GraphQLSchema,
            session_gen: _AsyncGeneratorContextManager):
            data = await request.json()
            async with session_gen as session:
                success, result = await graphql(
                    schema,
                    data,
                    context_value={"db": session}, 
                    debug=True,
                )
            return result
        
        graphql_server = graphql_server if graphql_server is not None else graphql_server_
        type_defs = load_schema_from_path(path_to_schema)
        schema = make_executable_schema(type_defs, resolvers)  
        
        @self.router.post(url_path)
        async def graphql_route(request):
            return await graphql_server(
                request=request, 
                schema=schema, 
                session_gen=session_gen()
            )
        block = Block(
            text=['Adding asynchronous graphql route (ariadne)',
                  f'{url_path=}, {path_to_schema=}, {debug=}',
                  ],
            func=CallableWrapper(
                func=GraphQL,
                args=[schema],
                kwargs={'debug': debug}
            )
            )
        self.router.add_route(url_path, block())  # type: ignore[reportArgumentType]
        
    
    @block_decorator(['Include router in app'])
    def include_router(self, *args, prefix='/api', **kwargs):
        self.app.include_router(self.router, *args, prefix=prefix, **kwargs)
            

class UvicornFastapiAppLauncher(BaseFastapiAppLauncher):
    
    def app_run(self):
        AppStarter.uvicorn_run(
            asgi_app=self.app, 
            host=self.host, 
            port=self.socket_close(self.socket_, self.port)
            )
    
    
