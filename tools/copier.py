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
from io import StringIO
from datetime import datetime

__builder__ = 'zoombuild'
__version__  = 0,1,0
METADATA_FILE = 'environment.ini'
DEPLOY_KEY = 'deploy'
FOLDER_KEY = 'folder'
CHECKSUM_KEY = 'checksum'

logging.basicConfig()
logger = logging.getLogger("zoombuild")
logger.setLevel(logging.INFO)
logger.info("! init")

unzipper = f"""
import os
import zipfile
import struct
import shutil
import sys
import configparser

zip = os.path.dirname(__file__)
cfg = configparser.ConfigParser()
with zipfile.ZipFile(zip, "r") as archive:
    with archive.open({METADATA_FILE}, 'r') as handle:
        cfg.read(handle)
    print (cfg)
    deploy_path = cfg[{DEPLOY_KEY}][{FOLDER_KEY}]
    checksum = cfg[{DEPLOY_KEY}][{CHECKSUM_KEY}]
        
if not os.path.isdir(deploy_path):
    print ("fresh deployment, unpacking into " + deploy_path)
    shutil.unpack_archive(zip, deploy_path)
    sys.exit(0)
else:
    parser = configparser.ConfigParser
    checksum_file = os.path.join(deploy_path, {METADATA_FILE})
    parser.read(checksum_file)
    saved_checksum = parser[{DEPLOY_KEY}][{CHECKSUM_KEY}]
    print("zip checksum", checksum, "disk checksum", saved_checksum)
    if (checksum == saved_checksum):
        print ("dependencies unchanged")
        sys.exit(0)
    else:
        print ("dependencies have changed, updating deployment")
        shutil.rmtree(deploy_path)
        shutil.unpack_archive(zip, extract_dir = deploy_path)
"""



def validate_zip(checksum, zip):
    with zipfile.ZipFile(zip, "r") as archive:
        with archive.open("checksum", "r") as cs:
            parser = configparser.ConfigParser()
            parser.read(cs)
            zip_checksum = parser[DEPLOY_KEY][CHECKSUM_KEY]
        return zip_checksum == checksum
    

def collect_requirements():
    """
    Gets the requirements.txt for the project and a checksum for 
    its contents
    """
    result = subprocess.check_output(["uv", "pip", "compile", "pyproject.toml"])
    checksum = str(zlib.crc32(result))
    return result, checksum

def precompile_bytecode(venv_site_packages):
    if compileall.compile_path(venv_site_packages, optimize=2, quiet=2):
        logger.info("compiled bytecode")
    else:
        logger.warning("failed to compile bytecode - abort")
        sys.exit(99)


def archive_venv(envlocation = ".venv", output = "./env.zip", deploy_folder = "deploy"):

    logger.info("Packing .venv")

    venv = pathlib.Path(envlocation)
    venv_site_packages = venv /  "Lib"/ "site-packages"


    precompile_bytecode(venv_site_packages)
    
    target_zip = os.path.abspath(os.path.expanduser(output))
    reqs, checksum = collect_requirements()    
    if os.path.exists(target_zip):
        logger.info ("comparing dependencies")
        if validate_zip(checksum, target_zip):
            # this means we don't need to re-vendor
            logger.info("no new vendored dependencies, complete")
            sys.exit(0)
        else:
            logger.warning("dependencies have changed")
            os.remove(target_zip)
    try:
        with zipfile.ZipFile(target_zip, "w") as archive:
            
            for rdf in tqdm.tqdm(os.walk(venv_site_packages)):
                root, dirs, files = rdf 
                logger.info(root)
                if root == str(venv_site_packages):
                    logger.info("ignore venv root")
                    continue
                if root == str (venv_site_packages / "__pycache__"):
                    logger.info("skip root pycache")
                    continue
                for f in files:
                    full_path =pathlib.Path(root, f)
                    archive_path = full_path.relative_to(venv_site_packages)
                    archive.write(os.path.join(root, f), archive_path)

            logger.info("adding unzipper")
            archive.writestr("__main__.py", unzipper)

            logger.info("adding requirements")
            archive.writestr("requirements.txt", reqs)

            cfg = configparser.ConfigParser()
            cfg['metadata'] = {
                'created': datetime.now(),
                'machine': os.getenv('COMPUTERNAME', 'unknown'),
                'user': os.getenv('USERNAME', 'unknown'),
                'version' : __version__,
                'tool' : __builder__
            }
            cfg [DEPLOY_KEY] = {
                FOLDER_KEY: deploy_folder,
                CHECKSUM_KEY: checksum
            }

            tmp = StringIO()
            cfg.write(tmp)
            archive.writestr(METADATA_FILE, tmp.getvalue())

    except Exception as e:
        logger.exception(e)
        logger.warning("build failed, removing {target_zip}")
        os.remove(target_zip)

    

if __name__ == '__main__':
    print ("! invoke")
    print (archive_venv)
    print(archive_venv())
