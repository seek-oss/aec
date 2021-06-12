from aec.util.configure import example
from pyfakefs.fake_filesystem import FakeFilesystem
import os

cwd = os.getcwd()

def test_example(fs: FakeFilesystem):
    fs.add_real_directory(cwd)
    example()
    assert os.path.exists(os.path.expanduser("~/.aec/ec2.toml"))
    assert os.path.exists(os.path.expanduser("~/.aec/userdata/amzn-install-docker.yaml"))
