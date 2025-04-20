import logging
import os
import shutil
import zipfile
from pathlib import Path

import click
import tqdm

from .metadata import METADATA_FILE, create_archive_metadata
from .project_info import PyProject

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("{message}", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)


def _default_filter(pth):
    pPth = Path(pth)
    return pPth.is_dir() or pPth.suffix == ".py"


def write_metadata(archive, project):
    tmp = create_archive_metadata(project=project, python_zip=archive.filename)
    archive.writestr(METADATA_FILE, tmp)


def delete_caches(source_tree):
    delenda = source_tree.rglob("__pycache__")
    for d in delenda:
        shutil.rmtree(d)


def find_resource_files(source_tree):
    for root, _, files in os.walk(source_tree):
        for f in files:
            if f.endswith(".pyc") or f.endswith(".py"):
                continue
            full_file = Path(root) / f
            relpath = full_file.relative_to(source_tree)
            yield full_file, relpath


def compile_tree(project: PyProject, zipname, optimize=1, filter=_default_filter):
    if not zipname:
        zipname = Path(project.project_root) / f"{project.name}.zip"

    source_tree = Path(project.find_package_dir())
    logger.info(f"Compiling {project.project_file} to {zipname.name}")
    if not source_tree.exists():
        raise RuntimeError(f"Could not find source directory in {project.name}")

    delete_caches(source_tree)
    logger.info("Deleted python caches")

    with zipfile.PyZipFile(zipname, "w", optimize=optimize) as archive:
        total = len(list(source_tree.rglob("*.*"))) - 1
        with tqdm.tqdm(total=total, unit="files", desc="Compiling") as progress:
            for dir in source_tree.iterdir():
                archive.writepy(dir, filterfunc=filter)
                progress.update(1)

            for resource_file, relpath in find_resource_files(source_tree):
                archive.write(resource_file, relpath)
                progress.update(1)

            write_metadata(archive, project)
            progress.update(1)
            progress.close()

    return zipname


@click.command(help="Package Python project into a distributable zip file")
@click.argument("project")
@click.option(
    "--output",
    default=None,
    help="Output path for the zip file",
)
@click.option("--verbose", is_flag=True, help="Increase logging verbosity")
@click.option(
    "--optimize",
    default=1,
    help="Optimize compiled output (default = 1, strips asserts and __DEBUG__)",
)
def main(project, output, optimize, verbose):
    if verbose:
        logger.setLevel(logging.DEBUG)
    project_path = Path(project)
    if not project_path.exists():
        raise ValueError(f"Project {project} not found")

    prj = PyProject(project_path)
    compile_tree(prj, output, optimize)
