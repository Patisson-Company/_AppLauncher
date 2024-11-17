import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, TypeVar

import httpx

from patisson_appLauncher.printX import (Block, BlockType, CallableWrapper,
                                         block_decorator)

SocketPort = TypeVar("SocketPort")


@dataclass(kw_only=True)
class BaseAppLauncher(ABC):
    service_name: str
    host: str
    app_port: Optional[str | int] = None

    @staticmethod
    def get_socket(port: Optional[str| int]) -> tuple[socket.socket, int]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', int(port) if port else 0))
        return sock, sock.getsockname()[1]
    
    @staticmethod
    def socket_close(socket: socket.socket, port: SocketPort) -> SocketPort:
        socket.close()
        return port
    
    def __post_init__(self) -> None:
        self.socket_, self.port = self.get_socket(self.app_port)
        Block(
            text=['App Launcher: Start setting up',
                  f'{self.host}:{self.port}/{self.service_name}'],
            block_type=BlockType.HEAD
            )()
    
    def consul_register(self, check_path: str = '/health',
                        check_interval: str = '30s',
                        check_timeout: str = '3s',
                        consul_register_address: str = 'http://localhost:8500/v1/agent/service/register'):
        service_id = f"{self.service_name}:{self.port}"
        http_ = f"http://{self.host}:{self.port}{check_path}"
        payload = {
            "Name": self.service_name,
            "ID": service_id,
            "Port": self.port,
            "Address": self.host,
            "Check": {
                "http": http_,
                "interval": check_interval,
                "timeout": check_timeout
                }
            }
        block = Block(
            text=['Registration in Consul', consul_register_address, 
                  f'{service_id=}, {self.port=}, {self.host=}',
                  f'{check_interval=}, {check_timeout=}',
                  f'check path: {http_}'
                  ],
            func=CallableWrapper(
                func=httpx.put,
                args=[consul_register_address],
                kwargs={'json': payload}
            )
            )
        response = block()
        if response.status_code != 200:
            raise ConnectionError(response.text)
        httpx.put(f"http://localhost:8500/v1/agent/check/pass/{service_id}")
            
            
    @abstractmethod
    def app_run(): 
        ''' '''
    

class AppStarter:
    
    @staticmethod
    @block_decorator(
        ['App Launcher: The setup is completed successfully', 'Uvicorn run'], 
        block_type=BlockType.TAIL
        )
    def uvicorn_run(asgi_app, host: str, port: int):
        import uvicorn
        uvicorn.run(asgi_app, host=host, port=port)
    
    @staticmethod
    @block_decorator(
        ['App Launcher: The setup is completed successfully', 'Gunicorn run'], 
        block_type=BlockType.TAIL
        )
    def gunicorn_run(host: str, port: int, app_path: str, workers: str = '1'):
        import subprocess
        command = [
            "gunicorn",
            "--bind", f"{host}:{port}",
            "--workers", workers,
            app_path
        ]
        subprocess.run(command)
    