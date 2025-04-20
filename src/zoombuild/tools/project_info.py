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
        result = self.package_search()
        return os.path.abspath(result) if result else None

    def package_search(self):
        """
        Find the package directory in the project. This is done by searching for the 'packages' key in the pyproject.toml file.
        If the key is not found, it will look for common package directories like 'src', 'source', 'pkg', or 'package'.
        If none of these directories exist, it will return the project root directory.
        """

        def recursive_key_search(data, key):
            if isinstance(data, dict):
                if key in data:
                    return data[key]
                for sub_value in data.values():
                    result = recursive_key_search(sub_value, key)
                    if result is not None:
                        return result
            return None

        result = recursive_key_search(self.toml, "packages")
        if result:
            if isinstance(result, list):
                # this does assume the first package is the one we want,
                # it's not clear that there's any reliable standard
                # in pyroject.toml for this
                result = result[0]
            return os.path.join(self.project_root, result)
        else:
            for dir in ("src","source","pkg","package", "packages"):
                full_path = os.path.join(self.project_root, dir)
                if os.path.isdir(full_path):
                    return full_path
            return self.project_root

    @property
    def name(self):
        return self.toml["project"]["name"]

    @property
    def version(self):
        return self.toml["project"]["version"]

    @property
    def description(self):
        return self.toml["project"]["description"]

    def __repr__(self):
        return f"PyProject({self.project_file})"
