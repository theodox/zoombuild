import configparser
import os
import sys
from datetime import datetime
from io import StringIO
from . import __version__ 

METADATA_FILE = "environment.ini"
DEPLOY_KEY = "deploy"
FOLDER_KEY = "folder"
CHECKSUM_KEY = "checksum"
PYTHON_KEY = "python"
PROJECT_KEY = "project"
ZIP_KEY = "archive"
BUILD_KEY = "build"
PYTHON_VERSION = "python_version"


def project_keys():
    readable_version, *_ = sys.version.split(" ")   

    return {
        'METADATA_FILE':METADATA_FILE,
        'PYTHON_VERSION':readable_version,
        'DEPLOY_KEY':DEPLOY_KEY,
        'FOLDER_KEY':FOLDER_KEY,
        'CHECKSUM_KEY':CHECKSUM_KEY,
        'ZIP_KEY':ZIP_KEY,
        'BUILD_KEY':BUILD_KEY,
        'PYTHON_KEY':PYTHON_KEY,
        'PROJECT_KEY':PROJECT_KEY,
    }


def add_python_metadata(project, cfg):
    cfg[PYTHON_KEY] = {
        "python": project.python_version,
        "dependencies": project.dependencies,
    }

def add_project_metadata(project, cfg):
    cfg[PROJECT_KEY] = {
        "name": project.name,
        "version": project.version,
        "description": project.description,
    }

def add_build_metadata(cfg):
    cfg[BUILD_KEY] = {
        "created": datetime.now(),
        "machine": os.getenv("COMPUTERNAME", "unknown"),
        "user": os.getenv("USERNAME", "unknown"),
        "builder_version": __version__,
        "python_version": sys.version,
    }


def create_binary_metadata(project, binary_zip, deploy_folder, checksum):
    """
    Returns a string in INI format with metadata about this build.

    The key functional part of the metadata is the final section,
    which includes the checksum for the requirements.txt.  This
    will be consumed by the unzipper function in the zip files __main__
    method
    """
    cfg = configparser.ConfigParser()
    add_project_metadata(project, cfg)
    add_python_metadata(project, cfg)
    add_build_metadata(cfg)

    cfg[DEPLOY_KEY] = {
        FOLDER_KEY: deploy_folder,
        CHECKSUM_KEY: checksum,
        ZIP_KEY: os.path.basename(binary_zip),
    }
    tmp = StringIO()
    cfg.write(tmp)
    return tmp.getvalue()

def create_archive_metadata(project, python_zip):
    """
    Returns a string in INI format with metadata about this build.
    """
    cfg = configparser.ConfigParser()
    add_project_metadata(project, cfg)
    add_python_metadata(project, cfg)
    cfg[ZIP_KEY] = {
        "archive": os.path.basename(python_zip),
    }

    add_build_metadata(cfg)
    tmp = StringIO()
    cfg.write(tmp)
    return tmp.getvalue()