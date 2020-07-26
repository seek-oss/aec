import os
import shutil


def configure():
    """create example config files in ~/.aec/"""

    config_dir = os.path.expanduser("~/.aec/")
    shutil.copytree("./config-example", config_dir)

    print("Created example config in", config_dir)
