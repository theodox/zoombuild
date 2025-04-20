import logging
import os
import pathlib
import site
import pytest

logger = logging.getLogger("zoombuild")
logging.basicConfig()
logger.setLevel(logging.INFO)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("{message}", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)


def main():
    my_dir = os.path.dirname(__file__)
    home_dir = pathlib.Path(os.path.dirname(my_dir))
    site.addsitedir(home_dir)
    logger.info(f"added {home_dir} to path")
    test_dir = pathlib.Path(home_dir, "..", "..", "tests")
    logger.info(pytest.main(test_dir))
