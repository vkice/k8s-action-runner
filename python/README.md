# K8s Action Runner - Python Module

## Local

The module supports local development and configuration, to quickly get you started, these are the following prerequisites:

1. Python Package Manager [UV](https://docs.astral.sh/uv/getting-started/installation/) set up on local machine, as this manages dependencies, version lock, and sets up the virtual environment. You are not required to utilize UV, but that is my preferred implementation of dependency management in Python projects.

    1a. Inside the directory with the files `.python-version` and `uv.lock`, run the following to setup the necessary files to run the script locally:

        - `uv python install`
        - `uv sync --all-extras --frozen`
    
    1b. The following will allow you to update the locks, be sure to run `uv -help` for more information as well:

        - `uv add PACKAGE_NAME` # Adds a dependency
        - `uv lock --upgrade-package PACKAGE_NAME` # Updates one package
        - `uv lock --upgrade` # Updates all packages


2. Local Kubernetes Cluster, I have provided a config file for **K3D** under `./dev/local/config.yaml`

    2a. This can be created using `k3d cluster create --config ./dev/local/config.yaml`
    2b. This can be torn down using `k3d cluster delete k8s-action-runner`

Once set up, you can trigger the script using this command, it's very important to first ensure you have the correct `kubectx` selected first, which the K3D Config file configures for you:

- `mv python/.venv/ ./.venv` # Move the virtual environment to the root directory, this allows execution as a module and is what occurs in the example GitHub Actions Workflow
- `uv run --frozen --module python.main -l true`

    - `--module python.main` runs the script as a module, this is required for the proper imports from subfolders. Note you must execute it from one directory up, i.e. `folder` as the subdirectory would be `folder/python/main.py` otherwise it will error out
    - `-l true` is the local argument to tell the script you are using local variables with a local cluster