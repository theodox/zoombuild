import logging
import os
import sys
import shutil
import zipfile
from pathlib import Path
import subprocess
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
    return (pPth.is_dir() or pPth.suffix == ".py") and not pPth.name.startswith(".")


def write_metadata(archive, project):
    tmp = create_archive_metadata(project=project, python_zip=archive.filename)
    archive.writestr(METADATA_FILE, tmp)


def delete_caches(source_tree):
    delenda = source_tree.rglob("__pycache__")
    for d in delenda:
        shutil.rmtree(d)


def create_compiler(prj, source_tree, optimize=1):
    test_env = os.environ.copy()
    test_env["VIRTUAL_ENV"] = str(prj.find_virtualenv())

    # Note that we use the -b option to compile in the legacy
    # name/location format instead of in __pycache__ directories
    # This matches the result of using PyZipFile.writepy()
    runner = subprocess.Popen(
        ["uv", "run", "python", "-m", "compileall", "-b", "-o", str(optimize), str(source_tree)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=test_env,
        cwd=prj.project_root,
        shell=True,
    )

    return runner

def compile_tree(project: PyProject, source_dir, zipname, optimize=1, filter=_default_filter):
    if not zipname:
        zipname = Path(project.project_root) / f"{project.name}.zip"

    if source_dir:
        _src = source_dir
    else:
        _src = project.find_package_dir()

    if not _src:
        # potential future work: what to do with flat projects?
        # you can specify a manual source dir, but it's messy and error prone
        # because there's so much extra stuff in there that looks like a resource file
        raise RuntimeError(f"{project.name} does not specify a source directory")
    
    source_tree = Path(_src)
    logger.info(f"Compiling {project.project_file} to {zipname.name}")
    if not source_tree.exists():
        raise RuntimeError(f"Could not find source directory in {project.name}")

    delete_caches(source_tree)
    logger.info("Deleted python caches")

    # it would be nice to just use PyZipFile.writepy for these
    # but we need to run the compiler in the target project's venv
    # so we subprocess it and then do a copy

    compiler = create_compiler(project, source_tree, optimize=optimize)
    stdout, stderr = compiler.communicate()
    if compiler.returncode != 0:
        logger.error(f"Compiler failed: {stderr.decode()}")
        sys.exit(1)

    with zipfile.PyZipFile(zipname, "w", optimize=optimize) as archive:
        all_files = set (source_tree.rglob("*.*"))
        py_files = set (source_tree.rglob("*.py"))
        files_to_copy = all_files - py_files
        logger.info(f"Compiled {len(py_files)} python files")
        with tqdm.tqdm(total=len(files_to_copy), unit=" files", desc="Archiving") as progress:
            for file in files_to_copy:
                relpath = file.relative_to(source_tree)
                archive.write(file, relpath)
                progress.update(1)
            
            write_metadata(archive, project)
            progress.update(1)
            progress.close()

    return zipname


@click.command(help="Package Python project into a distributable zip file")
@click.argument("project")
@click.option("--source-dir", default=None, help="Source directory to compile")
@click.option(
    "--output",
    default=None,
    help="Output path for the zip file",
)
@click.option(
    "--optimize",
    default=1,
    help="Optimize compiled output (default = 1, strips asserts and __DEBUG__)",
)
@click.option("--verbose", is_flag=True, help="Increase logging verbosity")
def main(project, source_dir,  output, optimize, verbose):
    if verbose:
        logger.setLevel(logging.DEBUG)
    project_path = Path(project)
    if not project_path.exists():
        raise ValueError(f"Project {project} not found")

    prj = PyProject(project_path)
    compile_tree(prj, source_dir, output, optimize)
