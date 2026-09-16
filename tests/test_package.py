import context_compiler


def test_package_imports() -> None:
    assert context_compiler is not None


def test_version_exposed() -> None:
    assert isinstance(context_compiler.__version__, str)
    assert context_compiler.__version__ == "0.1.0"
