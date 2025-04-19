import tomli
import os


class PyProject:

    def __init__(self, project_path):
        assert project_path is not None, "No project path supplied"
        assert os.path.exists(project_path), "Supplied project does not exist"

        self.project_file = None
        
        if os.path.isdir(project_path):
            for p in os.listdir(project_path):
                if p.lower() == 'pyproject.toml':
                    self.project_file = os.path.join(project_path, p)
                    break
        else:
            self.project_file = project_path

        with open(self.project_file, 'rb') as handle:
            self.toml = tomli.load(handle)

        self.project_root = os.path.dirname(self.project_file)

    def find_virtualenv(self):
        return os.path.join(self.project_root, ".venv") 


    @property
    def name(self):
        return self.toml['project']['name']

    @property
    def version(self):
        return self.toml['project']['version']
    
    @property
    def description(self):
        return self.toml['project']['description']

