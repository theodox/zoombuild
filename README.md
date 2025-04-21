# ZoomBuild

ZoomBuild is a packaging tool for creating deployable Python environments. It bundles your virtual environment into a self-extracting zip file that can be used across different machines while maintaining dependency integrity.

## Features

- Creates portable, self-extracting zip archives of Python environments
- Incremental updates - only redeploys when dependencies change
- Built-in integrity checking via checksums
- Cross-platform compatibility

## Installation for Developers

ZoomBuild uses [uv](https://github.com/astral-sh/uv) for dependency management. To set up a development environment:

```powershell
# Clone the repository
git clone https://github.com/yourusername/zoombuild.git
cd zoombuild

# Create and activate a virtual environment with uv
uv venv

# Install the package in development mode with dev dependencies
uv pip install -e .
uv pip install --dev
```

## Developer Tools

### Binary Packager

The binary packager is a command-line tool that packages a virtual environment into a self-extracting zip file. When installed in development mode, it's available as the `zoombuild-package` command.

#### Basic Usage

```
# Package a project virtualenv with default settings
uv run zb-package  path/to/target/pyproject.toml

# Show help and available options
zb-package --help
```

#### Configuration Options

```
# Specify a custom output file
uv run zb-package --output "deployment/app.zip"

# Specify a custom deployment folder name 
# (this is the relative path to which the zipped 
# dependencies will unpack)
uv run zb-package --deploy-folder "app_environment"

# Enable verbose logging
uv run zb-package --verbose
```

#### Common Scenarios

**Creating a Development Build**

```powershell
# Create a development build with verbose logging
zoombuild-package --output "build/dev_env.zip" --verbose
```

**Creating a Production Build**

```powershell
# Create a production build with a specific deployment folder name
zoombuild-package --output "dist/production_env.zip" --deploy-folder "production"
```

## How It Works

The binary packager:

1. Compiles Python files to bytecode for faster execution
2. Collects all dependencies from your virtual environment
3. Generates a checksum for dependency tracking
4. Creates a self-extracting zip file with an embedded unzipper
5. Stores metadata for version and dependency tracking

When deployed, the package checks if dependencies have changed before unpacking, avoiding unnecessary reinstallation.

## Development with uv

ZoomBuild is designed to work seamlessly with uv for dependency management. The project configuration in `pyproject.toml` includes script entry points that are accessible when the package is installed.

### Managing Dependencies

```powershell
# Add a new dependency
uv add package_name

# Add a development dependency
uv add --dev package_name
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
