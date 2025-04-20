import configparser
import os
import shutil
import sys
import zipfile
from datetime import datetime
from io import StringIO
import logging

from .binary_packager import METADATA_FILE
from .project_info import PyProject
import click

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("{message}", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)


__version__ = (0, 0, 2)
__builder__ = __name__


def _default_filter(pth):
    return os.path.isdir(pth) or pth.endswith(".py")


def compile_tree(project:PyProject, zipname, optimize=1, filter=_default_filter):
    
    logger.info("Compiling %s", project)
    if not zipname:
        zipname = os.path.join(project.project_root, project.name + ".zip")

    source_tree = project.find_package_dir()
    logger.info("Compiling %s", source_tree)

    if not os.path.exists(source_tree):
        raise RuntimeError("Could not find source directory in {project.name}")
    
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
        "tool": __name__,
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



@click.command(help='Package Python project into a distributable zip file')
@click.argument('project')
@click.option('--output',
              default = None,
              help = "Output path for the zip file"
              )
@click.option("--verbose", is_flag=True, help="Increase logging verbosity")
@click.option('--optimize',
              default = 1,
              help = 'Optimize compiled output (default = 1, strips asserts and __DEBUG__)')
def main(project, output, optimize, verbose):
    if verbose:
        logger.setLevel(logging.DEBUG)
    if not os.path.exists(project):
        raise ValueError("Project {project} not found")

    prj = PyProject(project)
    compile_tree(prj, output, optimize)
