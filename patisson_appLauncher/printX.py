"""
This module provides a framework for displaying styled text blocks with optional callable execution.

It includes classes and functions to define, format, and render blocks with specific styles.

Modules:
    shutil, textwrap: For terminal size and text wrapping functionality.
    enum: Provides the `BlockType` enumeration.
    typing: Used for type annotations and generics.
    colorama: For ANSI color formatting.
    pydantic: To define the `CallableWrapper` model.

Classes:
    BlockType (Enum):
        Enumeration for different types of text blocks.
        Attributes:
            HEAD: Represents the header of a block.
            BODY: Represents the body of a block.
            TAIL: Represents the footer of a block.

    CallableWrapper (BaseModel, Generic[CallableResponse]):
        Wraps a callable with its arguments and keyword arguments for later execution.
        Attributes:
            func (Callable): The function to execute.
            args (Sequence[Any]): Positional arguments for the function.
            kwargs (Mapping[str, Any]): Keyword arguments for the function.
        Methods:
            __call__(): Executes the wrapped function.

    Block (Generic[CallableResponse]):
        Defines a styled text block that can also execute a callable.
        Attributes:
            text (Sequence[str | tuple[str, Callable]]): Text content or tuples of text and c
                allable functions.
            width (int): Width of the block; defaults to terminal width.
            block_type (BlockType): Type of the block (HEAD, BODY, or TAIL).
            styles (Optional[str]): Custom styles; defaults based on block type.
            func (Callable): Optional function to execute during rendering.
        Methods:
            get_styles_by_block_type(block_type: BlockType) -> str:
                Returns the default styles for the given block type.
            get_vline() -> str:
                Returns a styled vertical line separator.
            get_hline(width: int, edge_sym: str = '+') -> str:
                Returns a styled horizontal line with edge symbols.
            get_success_str(width: int, text: str = 'success') -> str:
                Returns a formatted success message for the block.
            __call__(*args, **kwargs) -> CallableResponse:
                Renders the block and executes its callable, if provided.

Functions:
    none(*args, **kwargs) -> None:
        A no-op function used as a default for callables.

    block_decorator(text: Sequence[str], block_type: BlockType = BlockType.BODY,
        styles: Optional[str] = None): A decorator to wrap functions with a `Block`.
        Args:
            text (Sequence[str]): Content of the block.
            block_type (BlockType): Type of block to use.
            styles (Optional[str]): Custom styles for the block.
        Returns:
            Function decorator that wraps the given function in a `Block`.

Usage Example:
    @block_decorator(["Processing..."], block_type=BlockType.HEAD)
    def sample_function():
        print("Function logic here.")

    sample_function()
"""

import shutil
import textwrap
from enum import Enum
from typing import Any, Callable, Generic, Mapping, Optional, Sequence, TypeVar

from colorama import Back, Fore, Style, init  # noqa: F401
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
    """Wraps a callable function along with its arguments and keyword arguments."""

    func: Callable[..., CallableResponse]
    args: Sequence[Any] = []
    kwargs: Mapping[str, Any] = {}

    def __call__(self) -> CallableResponse:
        return self.func(*self.args, **self.kwargs)


class Block(Generic[CallableResponse]):
    """Defines a styled text block that can optionally execute a callable."""

    def __init__(
        self,
        text: Sequence[str | tuple[str, Callable[..., CallableResponse]]],
        width: Optional[int] = None,
        block_type: BlockType = BlockType.BODY,
        styles: Optional[str] = None,
        func: Callable[..., CallableResponse] = none,
    ) -> None:
        """
        Initialize a Block with text content, styles, and optional callable.

        Args:
            text: Text content or a combination of text and callable functions.
            width: Width of the block; defaults to terminal width.
            block_type: Type of block (HEAD, BODY, or TAIL).
            styles: Custom styles; defaults based on block type.
            func: Optional callable to execute during rendering.
        """
        self.func = func
        self.text = text
        self.width = width if width is not None else shutil.get_terminal_size().columns
        self.styles = styles if styles is not None else self.get_styles_by_block_type(block_type)
        self.block_type = block_type

    @staticmethod
    def get_styles_by_block_type(block_type: BlockType) -> str:
        """Return default styles for the given block type."""
        styles = {BlockType.HEAD: Style.BRIGHT + "", BlockType.BODY: "", BlockType.TAIL: Style.BRIGHT + ""}
        return styles[block_type]

    def get_vline(self) -> str:
        """Return a styled vertical line separator for the block."""
        return Style.RESET_ALL + self.styles + "|" + Style.RESET_ALL

    @staticmethod
    def get_hline(width: int, edge_sym: str = "+") -> str:
        """Return a styled horizontal line with customizable edge symbols."""
        return edge_sym + "-" * (width - 2) + edge_sym

    @staticmethod
    def get_success_str(width: int, text: str = "success") -> str:
        """Format a success message, centered within the block width."""
        return Style.RESET_ALL + Style.BRIGHT + Fore.GREEN + text.center(width - 2) + Style.RESET_ALL

    def __call__(self, *args, **kwargs) -> CallableResponse:
        """
        Render the block with its styles and text.

        Executes the optional callable after rendering.

        Returns:
            The result of the callable function execution, if provided.
        """

        def body():
            for text_ in self.text:

                if isinstance(text_, str):
                    wrapped_text = textwrap.fill(text_, width=self.width)
                    for line in wrapped_text.splitlines():
                        print(self.get_vline() + self.styles + line.center(self.width - 2) + self.get_vline())

                elif isinstance(text_, Sequence):
                    wrapped_text = textwrap.fill(text_[0], width=self.width)
                    for line in wrapped_text.splitlines():
                        print(
                            self.get_vline()
                            + self.styles
                            + Style.DIM
                            + line.center(self.width - 2)
                            + self.get_vline()
                        )
                        text_[1]()
                        print("\033[F")
                        print(
                            self.styles
                            + self.get_vline()
                            + self.get_success_str(self.width)
                            + self.get_vline()
                        )
                        print(
                            self.get_vline()
                            + self.styles
                            + Style.DIM
                            + ("|" + int((self.width - 4) / 2) * "-" + "|").center(self.width - 2)
                            + self.get_vline()
                        )

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


def block_decorator(
    text: Sequence[str], block_type: BlockType = BlockType.BODY, styles: Optional[str] = None
):
    """
    Wrap a function in a styled `Block`.

    Args:
        text: The text content for the block.
        block_type: The type of block to use (HEAD, BODY, or TAIL).
        styles: Optional custom styles for the block.

    Returns:
        A decorator function that applies the block styling and behavior.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            block = Block(func=func, text=text, block_type=block_type, styles=styles)
            return block(*args, **kwargs)

        return wrapper

    return decorator
