import zoombuild.tools.python_packager
import inspect


def test_main_imports():
    assert callable(zoombuild.tools.python_packager.main)


def test_main_signature():
    # using click we need to get the 'callback' to retrieve the original function
    original_main = zoombuild.tools.python_packager.main.callback
    sig = inspect.signature(original_main)
    assert "project" in sig.parameters
    assert "verbose" in sig.parameters
    assert "output" in sig.parameters