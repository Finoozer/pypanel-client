import pathlib
import sys


def get_resource_path(relative_path):
    rel_path = pathlib.Path(relative_path)
    dev_base_path = pathlib.Path(__file__).resolve().parent.parent
    base_path = getattr(sys, "_MEIPASS", dev_base_path)
    return base_path / rel_path

