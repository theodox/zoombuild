import zipfile
import tqdm
import os
import pathlib
import subprocess
import zlib
import compileall
import logging
import sys
import configparser
import click
from io import StringIO
from datetime import datetime
from .project_info import PyProject

__builder__ = "zoombuild"
__version__ = "0.1.3"
METADATA_FILE = "environment.ini"
DEPLOY_KEY = "deploy"
FOLDER_KEY = "folder"
CHECKSUM_KEY = "checksum"
ZIP_KEY = "archive"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("{message}", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)

# this script is included
# as the __main__ of the
# binary zip
unzip_main = f"""
import os
import zipfile
import struct
import shutil
import sys
import configparser

zip = os.path.dirname(__file__)
cfg = configparser.ConfigParser()
with zipfile.ZipFile(zip, "r") as archive:
    with archive.open('{METADATA_FILE}', 'r') as handle:
        data = handle.read().decode('utf-8')
        cfg.read_string(data)
    deploy_path = cfg['{DEPLOY_KEY}']['{FOLDER_KEY}']
    checksum = cfg['{DEPLOY_KEY}']['{CHECKSUM_KEY}']
        
if not os.path.isdir(deploy_path):
    print ("fresh deployment, unpacking into " + deploy_path)
    shutil.unpack_archive(zip, deploy_path)
    sys.exit(0)
else:
    parser = configparser.ConfigParser()
    checksum_file = os.path.join(deploy_path, '{METADATA_FILE}')
    parser.read(checksum_file)
    saved_checksum = parser['{DEPLOY_KEY}']['{CHECKSUM_KEY}']
    print("zip checksum", checksum, "disk checksum", saved_checksum)
    if (checksum == saved_checksum):
        print ("dependencies unchanged")
        sys.exit(0)
    else:
        print ("dependencies have changed, updating deployment")
        shutil.rmtree(deploy_path)
        shutil.unpack_archive(zip, extract_dir = deploy_path)
        sys.exit(0)
"""


def validate_zip(checksum, zip):
    with zipfile.ZipFile(zip, "r") as archive:
        parser = configparser.ConfigParser()
        with archive.open(METADATA_FILE, "r") as cs:
            data = cs.read().decode("utf-8")
            parser.read_string(data)
            zip_checksum = parser[DEPLOY_KEY][CHECKSUM_KEY]

            archive_version = parser["metadata"]["version"]
        return zip_checksum == checksum and archive_version == str(__version__)


def collect_requirements(project: PyProject):
    """
    Gets the requirements.txt for the project and a checksum for
    its contents
    """

    result = subprocess.check_output(["uv", "pip", "compile", project.project_file])
    checksum = str(zlib.crc32(result))
    return result, checksum


def precompile_bytecode(venv_site_packages):
    if compileall.compile_path(venv_site_packages, optimize=2, quiet=2):
        logger.info("compiled bytecode")
    else:
        logger.warning("failed to compile bytecode - abort")
        sys.exit(99)


def precompute_file_count(directory):
    total_items = 0
    for _, dirs, files in os.walk(directory):
        total_items += len(files)
    return total_items


def generate_ini(project, output, deploy_folder, checksum):
    """
    Returns a string in INI format with metadata about this build.

    The key functional part of the metadata is the final section,
    which includes the checksum for the requirements.txt.  This
    will be consumed by the unzipper function in the zip files __main__
    method
    """
    cfg = configparser.ConfigParser()
    cfg["project"] = {
        "name": project.name,
        "version": project.version,
    }
    cfg["metadata"] = {
        "created": datetime.now(),
        "machine": os.getenv("COMPUTERNAME", "unknown"),
        "user": os.getenv("USERNAME", "unknown"),
        "version": __version__,
        "tool": __builder__,
    }
    cfg[DEPLOY_KEY] = {
        FOLDER_KEY: deploy_folder,
        CHECKSUM_KEY: checksum,
        ZIP_KEY: os.path.basename(output),
    }

    tmp = StringIO()
    cfg.write(tmp)
    return tmp.getvalue()


def archive_venv(project: PyProject, output=None, deploy_folder="deploy"):
    logger.info("Packing .venv")

    venv = pathlib.Path(project.find_virtualenv())
    venv_site_packages = venv / "Lib" / "site-packages"

    if not output:
        output = os.path.join(".", project.name + "_binaries.zip")

    target_zip = os.path.abspath(os.path.expanduser(output))
    requirements, checksum = collect_requirements(project)
    if os.path.exists(target_zip):
        logger.info("comparing dependencies")
        if validate_zip(checksum, target_zip):
            # this means we don't need to re-vendor
            logger.info("no new vendored dependencies, complete")
            sys.exit(0)
        else:
            logger.warning("dependencies or version have changed")
            os.remove(target_zip)

    precompile_bytecode(venv_site_packages)

    try:
        with zipfile.ZipFile(target_zip, "w") as archive:
            file_total = precompute_file_count(venv_site_packages)
            with tqdm.tqdm(total=file_total, desc="copying", unit=" files") as progress:
                for root, _, files in os.walk(venv_site_packages):
                    if root == str(venv_site_packages):
                        continue
                    if root == str(venv_site_packages / "__pycache__"):
                        continue
                    for f in files:
                        full_path = pathlib.Path(root, f)
                        archive_path = full_path.relative_to(venv_site_packages)
                        archive.write(os.path.join(root, f), archive_path)
                        progress.update(1)
                        logger.debug(f)

                logger.debug("adding unzipper")
                archive.writestr("__main__.py", unzip_main)
                progress.update(1)

                logger.debug("adding requirements")
                archive.writestr("requirements.txt", requirements)
                progress.update(1)

                INI_text = generate_ini(project, output, deploy_folder, checksum)
                archive.writestr(METADATA_FILE, INI_text)
                progress.update(1)
                progress.update(1)
            progress.close()

    except Exception as e:
        logger.exception(e)
        logger.warning("build failed, removing {target_zip}")
        os.remove(target_zip)

    logger.info(f"built {target_zip}")
    sys.exit(0)


@click.command(help="Package virtual environment into a deployable zip file")
@click.argument("project")
@click.option("--output", default=None, help="Output path for the zip file (default: ./env.zip)")
@click.option(
    "--deploy-folder", default="deploy", help="Target folder name for deployment (default: deploy)"
)
@click.option("--verbose", is_flag=True, help="Increase logging verbosity")
def main(project, output, deploy_folder, verbose):
    """
    Package a virtual environment into a self-extracting zip file.

    This tool creates a deployable zip with all dependencies from the virtual environment.
    The zip file contains a __main__.py script that handles extraction and updates.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
    if not os.path.exists(project):
        raise ValueError("Project {project} not found")

    prj = PyProject(project)

    archive_venv(prj, output=output, deploy_folder=deploy_folder)


if __name__ == "__main__":
    main()
