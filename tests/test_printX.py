from pytest import CaptureFixture

from patisson_appLauncher.printX import Block, BlockType, block_decorator


def test_block_rendering_body(capsys: CaptureFixture[str]):
    block = Block(text=["Sample text"], block_type=BlockType.BODY)
    block()
    captured = capsys.readouterr()
    assert "Sample text" in captured.out


def test_block_rendering_head(capsys: CaptureFixture[str]):
    block = Block(text=["Header text"], block_type=BlockType.HEAD)
    block()
    captured = capsys.readouterr()
    assert "Header text" in captured.out


def test_block_rendering_tail(capsys: CaptureFixture[str]):
    block = Block(text=["Footer text"], block_type=BlockType.TAIL)
    block()
    captured = capsys.readouterr()
    assert "Footer text" in captured.out


def test_block_decorator(capsys: CaptureFixture[str]):
    @block_decorator(["Decorated function"], block_type=BlockType.BODY)
    def sample_function():
        print("Function logic here.")

    sample_function()
    captured = capsys.readouterr()
    assert "Decorated function" in captured.out
    assert "Function logic here." in captured.out
