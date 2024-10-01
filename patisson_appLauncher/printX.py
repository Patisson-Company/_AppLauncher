import shutil
import textwrap
from enum import Enum
from typing import Any, Callable, Generic, Mapping, Optional, Sequence, TypeVar

from colorama import Back, Fore, Style, init
from pydantic import BaseModel

init(autoreset=True)

CallableResponse = TypeVar("CallableResponse")

def none(*args, **kwargs) -> None:
    return

class BlockType(Enum):
    HEAD = "HEAD"
    BODY = "BODY"
    TAIL = "TAIL"
    
class CallableWrapper(BaseModel, Generic[CallableResponse]):
    func: Callable[..., CallableResponse]
    args: Sequence[Any] = []
    kwargs: Mapping[str, Any] = {}
    
    def __call__(self) -> CallableResponse:
        return self.func(*self.args, **self.kwargs)
    
    
class Block(Generic[CallableResponse]):
        
    def __init__(self, text: Sequence[str | tuple[str, Callable[..., CallableResponse]]], 
                 width: int = shutil.get_terminal_size().columns, 
                 block_type: BlockType = BlockType.BODY, styles: Optional[str] = None,
                 func: Callable[..., CallableResponse] = none) -> None:
        self.func = func
        self.text = text
        self.width = width
        self.styles = styles if styles is not None else self.get_styles_by_block_type(block_type)
        self.block_type = block_type
        
    @staticmethod
    def get_styles_by_block_type(block_type: BlockType) -> str:
        styles = {
            BlockType.HEAD: Style.BRIGHT + '',
            BlockType.BODY: '',
            BlockType.TAIL: Style.BRIGHT + ''
        }
        return styles[block_type]
    
    def get_vline(self) -> str:
        return Style.RESET_ALL + self.styles + '|' + Style.RESET_ALL

    @staticmethod
    def get_hline(width: int, edge_sym: str = '+') -> str:
        return edge_sym + "-" * (width - 2) + edge_sym
    
    @staticmethod
    def get_success_str(width: int, text: str = 'success') -> str:
        return Style.RESET_ALL + Style.BRIGHT + Fore.GREEN + text.center(width - 2) + Style.RESET_ALL
    
    def __call__(self, *args, **kwargs) -> CallableResponse:
        def body():
            for text_ in self.text:
                
                if isinstance(text_, str):
                    wrapped_text = textwrap.fill(text_, width=self.width)
                    for line in wrapped_text.splitlines():
                        print(self.get_vline() + self.styles +  line.center(self.width - 2) + self.get_vline())
                        
                elif isinstance(text_, Sequence):
                    wrapped_text = textwrap.fill(text_[0], width=self.width)
                    for line in wrapped_text.splitlines():
                        print(self.get_vline() + self.styles + Style.DIM +  line.center(self.width - 2) + self.get_vline())
                        text_[1]()
                        print("\033[F")
                        print(self.styles + self.get_vline() + self.get_success_str(self.width) + self.get_vline())
                        print(self.get_vline() + self.styles + Style.DIM
                              +  ('|' + int((self.width - 4) / 2) * '-' + '|').center(self.width - 2) 
                              + self.get_vline())
                        
        if self.block_type == BlockType.HEAD:
            print(self.styles + self.get_hline(self.width))
            body()
            print(self.styles + self.get_hline(self.width))
            result = self.func(*args, **kwargs)
                    
        elif self.block_type == BlockType.TAIL:
            print("\033[F\033[F")
            print(self.styles + self.get_hline(self.width))
            body()
            print(self.styles + self.get_hline(self.width))
            result = self.func(*args, **kwargs)
            
        else:  # self.block_type == BlockType.BODY:
            body()
            print(self.styles + self.get_hline(self.width, edge_sym=self.get_vline()))
            result = self.func(*args, **kwargs)
            print("\033[F\033[F")
            print(self.styles + self.get_vline() + self.get_success_str(self.width) + self.get_vline())
            print(self.styles + self.get_hline(self.width, edge_sym=self.get_vline()))
        
        return result

def block_decorator(text: Sequence[str], block_type: BlockType = BlockType.BODY, styles: Optional[str] = None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            block = Block(func=func, text=text, block_type=block_type, styles=styles)
            return block(*args, **kwargs)
        return wrapper
    return decorator