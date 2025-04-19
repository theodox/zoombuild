import os
import sys
import pathlib
import site

my_dir = os.path.dirname(__file__)
project_dir = pathlib.Path(os.path.dirname(my_dir))
src_dir =  project_dir / "src"
test_dir = project_dir / "tests"

site.addsitedir(src_dir)
print ("added", src_dir)

import pytest
pytest.main(test_dir)

