import configparser
import os
import shutil
import sys
import zipfile
from datetime import datetime
from io import StringIO

__version__ = (0, 0, 1)
__builder__ = __name__
METADATA_FILE = "environment.ini"


def default_filter(pth):
    return os.path.isdir(pth) or pth.endswith(".py")


def compile_tree(source_tree, zipname, optimize=1, filter=default_filter):
    delete_caches(source_tree)

    with zipfile.PyZipFile(zipname, "w", optimize=optimize) as archive:
        for dir in os.listdir(source_tree):
            archive.writepy(os.path.join(source_tree, dir), filterfunc=filter)

        for resource_file, relpath in find_resource_files(source_tree):
            archive.write(resource_file, relpath)

        write_metadata(archive)

    return zipname


def write_metadata(archive):
    cfg = configparser.ConfigParser()
    cfg["metadata"] = {
        "created": datetime.now(),
        "python": sys.version_info,
        "machine": os.getenv("COMPUTERNAME", "unknown"),
        "user": os.getenv("USERNAME", "unknown"),
        "version": __version__,
        "tool": __builder__,
    }

    tmp = StringIO()
    cfg.write(tmp)
    archive.writestr(METADATA_FILE, tmp.getvalue())


def delete_caches(source_tree):
    delenda = []
    for root, dirs, _ in os.walk(source_tree):
        for d in dirs:
            if d == "__pycache__":
                delenda.append(os.path.join(root, d))

    for d in delenda:
        shutil.rmtree(d)


def find_resource_files(source_tree):
    for root, _, files in os.walk(source_tree):
        for f in files:
            if f.endswith(".pyc") or f.endswith(".py"):
                continue
            full_file = os.path.join(root, f)
            relpath = os.path.relpath(full_file, source_tree)
            yield full_file, relpath


if __name__ == "__main__":
    if os.path.exists("test.zip"):
        os.remove("test.zip")
    compile_tree("src", "test.zip", optimize=1)
