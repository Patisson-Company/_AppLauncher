import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AnyStr, Optional, TypeAlias

import requests
from uvicorn._types import ASGIApplication

ClosedSocketPort: TypeAlias = int


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
    def socket_close(socket: socket.socket, port: ClosedSocketPort) -> ClosedSocketPort:
        socket.close()
        return port
    
    
    def __post_init__(self) -> None:
        self.socket_, self.port = BaseAppLauncher.get_socket(self.app_port)
        
    
    def consul_register(self, check_path: str = '/health',
                        check_interval: str = '30s',
                        check_timeout: str = '3s',
                        consul_register_address: str = 'http://localhost:8500/v1/agent/service/register'):
        payload = {
            "Name": self.service_name,
            "ID": f"{self.service_name}:{self.port}",
            "Port": self.port,
            "Address": self.host,
            "Check": {
                "http": f"http://{self.host}:{self.port}{check_path}",
                "interval": check_interval,
                "timeout": check_timeout
                }
            }
        response = requests.put(consul_register_address, json=payload)
        if response.status_code == 200:
            print(f"{self.service_name} registered")
        else:
            print(f"Error: {response.text}")
            
            
    @abstractmethod
    def app_run(): 
        ''' '''
        

class AppStarter:
    
    @abstractmethod
    def uvicorn_run(asgi_app: ASGIApplication, host: str, port: int):
        import uvicorn
        uvicorn.run(asgi_app, host=host, port=port)
    
    def gunicorn_run(self, host: str, port: int, app_path: str, workers: str = '1'):
        import subprocess
        command = [
            "gunicorn",
            "--bind", f"{host}:{port}",
            "--workers", workers,
            app_path
        ]
        subprocess.run(command)
    