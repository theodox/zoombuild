import os
import pathlib
import site
import logging

logger = logging.getLogger("zoombuild")
logging.basicConfig()
logger.setLevel(logging.INFO)

import pytest


from .project_info import PyProject
from . import metadata

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("{message}", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)


def main():
    my_dir = os.path.dirname(__file__)
    zoombuild_dir = pathlib.Path(os.path.dirname(my_dir))
    site.addsitedir(zoombuild_dir)
    logger.info(f"added {zoombuild_dir} to path")

    test_dir = pathlib.Path(zoombuild_dir, "..", "..", "tests")

    print(pytest.main(test_dir))
