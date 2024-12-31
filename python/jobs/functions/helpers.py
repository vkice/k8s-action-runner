import datetime
import os
import uuid


def get_timestamp():
    """Returns the current timestamp as a formatted string."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


############################
# Github Actions Functions #
############################
# optional functions you can import to set outputs, environment variables, and step summaries in the GitHub Actions workflow
def _set_value(file_env_name, name, value, multiline=False):
    with open(os.environ[file_env_name], "a") as fh:
        if multiline:
            delimiter = uuid.uuid1()
            print(f"{name}<<{delimiter}", file=fh)
            print(value, file=fh)
            print(delimiter, file=fh)
        else:
            print(f"{name}={value}", file=fh)


def set_output(name, value, env="GITHUB_OUTPUT", multiline=False):
    _set_value(env, name, value, multiline)


def set_env(name, value, env="GITHUB_ENV", multiline=False):
    _set_value(env, name, value, multiline)


def set_summary(value, env="GITHUB_STEP_SUMMARY"):
    with open(os.environ[env], "a") as fh:
        print(f"{value}", file=fh)