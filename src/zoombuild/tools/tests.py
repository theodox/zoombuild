import os
import pathlib
import site
import logging
logger = logging.getLogger("zoombuild")
logging.basicConfig()
logger.setLevel(logging.INFO)

import pytest

def main():
    my_dir = os.path.dirname(__file__)
    zoombuild_dir = pathlib.Path(os.path.dirname(my_dir))
    site.addsitedir(zoombuild_dir)
    logger.info (f"added {zoombuild_dir} to path")

    test_dir = pathlib.Path(zoombuild_dir,"..", "..", "tests")

    pytest.main(test_dir)

