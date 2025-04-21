import logging
import os
import subprocess
import sys
from pathlib import Path

import click

from .project_info import PyProject

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("{message}", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)


def create_test_runner(prj, test_folder):
    test_env = os.environ.copy()
    test_env["VIRTUAL_ENV"] = str(prj.find_virtualenv())
    logger.debug(f"Running tests in: '{test_folder}")

    # this could probably be more elegant.  It looks like we need the
    # '--with pytest pytest' to ensure that we get the pytest runner
    # inside the target project's venv -- if you do the more straightforward
    # 'uv run pytest' it seems to default to to runner for this project,
    # which would lead to weirdness when the target project is on a different
    # version of python
    runner = subprocess.Popen(
        ["uv", "run", "--with", "pytest", "pytest", test_folder],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=test_env,
        cwd=prj.project_root,
        shell=True,
    )

    return runner


def sync_target_project(prj):
    sync_proc = subprocess.Popen(
        ["uv", "sync"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=prj.project_root
    )
    sync_proc.wait(timeout=120)
    if sync_proc.returncode != 0:
        logger.error(f"Sync failed with error code {sync_proc.returncode}")
        stdout, stderr = sync_proc.communicate()
        logger.error(f"stdout: {stdout.decode()}")
        logger.error(f"stderr: {stderr.decode()}")
        sys.exit(sync_proc.returncode)


@click.command(help="Run all tests")
@click.argument("project")
@click.option("--verbose", is_flag=True, help="Increase logging verbosity")
@click.option("--test-dir", default="tests", help="Directory containing tests")
def main(project, verbose, test_dir):
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    project_path = Path(project)
    if not project_path.exists():
        raise ValueError(f"Project {project} not found")
    prj = PyProject(project_path)

    _test = test_dir
    if not _test:
        _test = prj.find_test_dir()
        if not _test:
            logger.warning(f"{prj.name} does not specify a test directory")
            for folder in ("tests", "test", "spec"):
                test_dir = Path(project_path, folder)
                if test_dir.exists():
                    logger.info(f"Using '{folder}' as test directory")
                    _test = test_dir
                    break
            if not _test:
                raise RuntimeError(f"Could not find test directory in {prj.name}")

    test_folder = Path(_test)
    if not test_folder.exists():
        raise RuntimeError(f"Could not find test directory in {prj.name}")

    logger.info(f"syncing dependencies for {prj.name}...")
    sync_target_project(prj)
    logger.info("sync complete")

    runner = create_test_runner(prj, test_folder)
    stdout, stderr = runner.communicate()

    # Ran, but failed tests
    if runner.returncode == 1:
        logger.error("Tests failed")
        logger.error(f"stdout: {stdout.decode()}")
        sys.exit(1)

    # failed to run
    if runner.returncode != 0:
        logger.error(f"Test run failed with error code {runner.returncode}")
        logger.error(f"stdout: {stdout.decode()}")
        logger.error(f"stderr: {stderr.decode()}")
        sys.exit(runner.returncode)

    logger.info("\n" + stdout.decode())
    sys.exit(0)
