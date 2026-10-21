from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def load_tool(relative_path, name):
    path = Path(__file__).parents[1] / relative_path
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
