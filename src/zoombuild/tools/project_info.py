import tomli
import os


class PyProject:
    def __init__(self, project_path):
        assert project_path is not None, "No project path supplied"
        assert os.path.exists(project_path), "Supplied project does not exist"

        self.project_file = None

        if os.path.isdir(project_path):
            for p in os.listdir(project_path):
                if p.lower() == "pyproject.toml":
                    self.project_file = os.path.join(project_path, p)
                    break
        else:
            self.project_file = project_path

        self.project_file = os.path.abspath(self.project_file)
        self.project_root = os.path.dirname(self.project_file)

        with open(self.project_file, "rb") as handle:
            self.toml = tomli.load(handle)

    def find_virtualenv(self):
        return os.path.join(self.project_root, ".venv")

    def find_package_dir(self):
        """
        Find the package name in the project. This is done by searching for the 'packages' key in the pyproject.toml file.
        If the key is not found, it will look for common package directories like 'src', 'source', 'pkg', or 'package'.
        If none of these directories exist, it will return the project root directory.
        """
        result = self._package_search()
        if isinstance(result, list):
            result = result[0]
        return self.project_path(result) if result else None
        
    def find_test_dir(self):
        """
        Find the package name in the project. This is done by searching for the 'packages' key in the pyproject.toml file.
        If the key is not found, it will look for common package directories like 'src', 'source', 'pkg', or 'package'.
        If none of these directories exist, it will return the project root directory.
        """
        result = self._test_search()
        if isinstance(result, list):
            result = result[0]
        return self.project_path(result) if result else None
    
    def _recursive_key_search(self, data, key):
        if isinstance(data, dict):
            if key in data:
                return data[key]
            for sub_value in data.values():
                result = self._recursive_key_search(sub_value, key)
                if result is not None:
                    return result
        return None
      
    def _package_search(self):
        """
        Find the package directory in the project. This is done by searching for the 'packages' key in the pyproject.toml file.
        If the key is not found, it will look for common package directories like 'src', 'source', 'pkg', or 'package'.
        If none of these directories exist, it will return the project root directory.
        
        This version assumes there's a single root package directory.
        """
        result = self._recursive_key_search(self.toml, "packages")
        if result:
            return result
        else:
            # if no package is found, look for common package directories
            for dir in ("src","source","pkg","package", "packages"):
                full_path = os.path.join(self.project_root, dir)
                if os.path.isdir(full_path):
                    return dir
            return None

    def _test_search(self):
        """
        Find the test directory in the project. This is done by searching for the 'test' key in the pyproject.toml file.
        If the key is not found, it will look for common test directories like 'tests', 'test', or 'spec'.
        If none of these directories exist, it will return None.
        """
       
        # 'testpaths' is typically used in pytest or unittest
        # based projects
        result = self._recursive_key_search(self.toml, "testpaths")
        if result:
            return result
        
        # typical of nose based projects
        result = self._recursive_key_search(self.toml, "where")
        if result:
            return result

        tox_config = self.toml.get("tool", {}).get("tox", {}).get("testenv", {})
        if "commands" in tox_config:
            for command in tox_config["commands"]:
                if "pytest" in command or "unittest" in command:
                    # Extract directory from command (e.g., "pytest tests")
                    parts = command.split()
                    if len(parts) > 1:
                        result = parts[1]
                    if result:
                        return result
        
    def project_path(self, *path_segments):
        """
        Get the relative path from the project root to the specified path.
        """
        tokens = list(path_segments)
        tokens.insert(0, self.project_root)
        return( os.path.join(*tokens))

    @property
    def name(self):
        return self.toml["project"]["name"]

    @property
    def version(self):
        return self.toml["project"]["version"]

    @property
    def description(self):
        return self.toml["project"]["description"]
    
    @property
    def dependencies(self):
        return self.toml["project"].get("dependencies", [])
    
    @property
    def python_version(self):
        return self.toml["project"].get("requires-python", None)

    def __repr__(self):
        return f"PyProject({self.project_file})"
