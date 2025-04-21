import compileall
import configparser
import importlib.resources as resources
import logging
import os
import pathlib
import subprocess
import sys
import zipfile
import zlib
import platform

import click
import tqdm

from . import metadata
from .project_info import PyProject

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("{message}", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)


# this script is included
# as the __main__ of the
# binary zip
def generate_unzip_text():
    unzip_text = resources.files(__name__).joinpath("unpacker_script.txt").read_text()
    replacements = metadata.project_keys()
    return unzip_text.format(**replacements)


def validate_zip(checksum, zip):
    with zipfile.ZipFile(zip, "r") as archive:
        parser = configparser.ConfigParser()
        with archive.open(metadata.METADATA_FILE, "r") as cs:
            data = cs.read().decode("utf-8")
            parser.read_string(data)
            zip_checksum = parser[metadata.DEPLOY_KEY][metadata.CHECKSUM_KEY]
        return zip_checksum == checksum


def collect_requirements(project: PyProject):
    """
    Gets the requirements.txt for the project and a checksum for
    its contents
    """

    result = subprocess.check_output(["uv", "pip", "compile", project.project_file])
    checksum = str(zlib.crc32(result))
    return result, checksum


def _precompile_bytecode(venv_site_packages):
    if compileall.compile_path(venv_site_packages, optimize=2, quiet=2):
        logger.info("compiled bytecode")
    else:
        logger.warning("failed to compile bytecode - abort")
        sys.exit(99)


def _precompute_file_count(directory):
    total_items = 0
    for _, dirs, files in os.walk(directory):
        total_items += len(files)
    return total_items


def archive_venv(project: PyProject, output=None, deploy_folder="deploy"):
    logger.info("Packing .venv")

    venv = pathlib.Path(project.find_virtualenv())
    venv_site_packages = venv / "Lib" / "site-packages"

    if not output:
        platform_string = platform.system().lower()
        output = pathlib.Path(project.project_root) / f"{project.name}.bin.{platform_string}.zip"

    target_zip = pathlib.Path(output).expanduser().resolve()
    requirements, checksum = collect_requirements(project)
    
    logger.info(f"syncing virtual environment {venv}...")
    project.sync()

    if target_zip.exists():
        logger.info("comparing dependencies")
        if validate_zip(checksum, target_zip):
            # this means we don't need to re-vendor
            logger.info("no new vendored dependencies, complete")
            sys.exit(0)
        else:
            logger.warning("dependencies or version have changed")
            target_zip.unlink()

    _precompile_bytecode(venv_site_packages)

    try:
        with zipfile.ZipFile(target_zip, "w") as archive:
            file_total = _precompute_file_count(venv_site_packages)
            with tqdm.tqdm(total=file_total, desc="copying", unit=" files") as progress:
                for root, _, files in os.walk(venv_site_packages):
                    root_path = pathlib.Path(root)
                    if root_path == venv_site_packages:
                        continue
                    if root_path == venv_site_packages / "__pycache__":
                        continue
                    for f in files:
                        full_path = root_path / f
                        archive_path = full_path.relative_to(venv_site_packages)
                        archive.write(full_path, archive_path)
                        progress.update(1)
                        logger.debug(f)

                logger.debug("adding unzipper")
                main_script = generate_unzip_text()
                archive.writestr("__main__.py", main_script)
                progress.update(1)

                logger.debug("adding requirements")
                archive.writestr("requirements.txt", requirements)
                progress.update(1)

                INI_text = metadata.create_binary_metadata(
                    project, output, deploy_folder, checksum
                )
                archive.writestr(metadata.METADATA_FILE, INI_text)
                progress.update(1)
                progress.update(1)
            progress.close()

    except Exception as e:
        logger.exception(e)
        logger.warning(f"build failed, removing {target_zip}")
        target_zip.unlink()

    logger.info(f"built {target_zip}")
    sys.exit(0)


@click.command(help="Package virtual environment into a deployable zip file")
@click.argument("project")
@click.option("--output", default=None, help="Output path for the zip file")
@click.option("--deploy-folder", default="deploy", help="Target folder name for deployment")
@click.option("--verbose", is_flag=True, help="Increase logging verbosity")
def main(project, output, deploy_folder, verbose):
    """
    Package a virtual environment into a self-extracting zip file.

    This tool creates a deployable zip with all dependencies from the virtual environment.
    The zip file contains a __main__.py script that handles extraction and updates.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
    project_path = pathlib.Path(project)
    if not project_path.exists():
        raise ValueError(f"Project {project} not found")

    prj = PyProject(project_path)

    archive_venv(prj, output=output, deploy_folder=deploy_folder)

