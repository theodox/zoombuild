import os
import zoombuild
import zoombuild.tools
from zoombuild.tools.project_info import PyProject

TOML_TESTS = os.path.join(os.path.dirname(__file__), "project_examples")

def test_zb():
    assert (zoombuild.tools is not None)


def test_project_from_pytest():
    prj_file = os.path.join(TOML_TESTS, "pytest_prj.toml")
    test = PyProject(prj_file)
    result = test.find_test_dir()
    assert os.path.isabs(result)
    assert os.path.basename(result) == "pytest_tests"

def test_project_from_nose():
    prj_file = os.path.join(TOML_TESTS, "nose_prj.toml")
    test = PyProject(prj_file)
    result = test.find_test_dir()
    assert os.path.isabs(result)
    assert os.path.basename(result) == "nose_tests"

def test_project_from_tox():
    prj_file = os.path.join(TOML_TESTS, "tox_prj.toml")
    test = PyProject(prj_file)
    result = test.find_test_dir()
    assert os.path.isabs(result)
    assert os.path.basename(result) == "tox_tests"

def test_project_from_unittest():
    prj_file = os.path.join(TOML_TESTS, "unittest_prj.toml")
    test = PyProject(prj_file)
    result = test.find_test_dir()
    assert os.path.isabs(result)
    assert os.path.basename(result) == "unittest_tests"

def test_source_from_pytest():
    prj_file = os.path.join(TOML_TESTS, "pytest_prj.toml")
    test = PyProject(prj_file)
    result = test.find_package_dir()
    assert os.path.isabs(result)
    assert os.path.basename(result) == "src"
    