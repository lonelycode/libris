from libris.settings.log_config import *
logger = logging.getLogger("module-finder")
from libris.settings.search_manager_settings import base_driver_module
import importlib


def load_class(full_class_string):
    """
    dynamically load a class from a string
    """

    class_data = full_class_string.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]

    module = importlib.import_module(module_path)
    # Finally, we retrieve the Class
    return getattr(module, class_str)


def module_finder(module_dot_path, base_module=base_driver_module):
    full_path = '.'.join([base_module, module_dot_path])
    cl = load_class(full_path)

    return cl