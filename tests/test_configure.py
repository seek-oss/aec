import os

from pyfakefs.fake_filesystem import FakeFilesystem

from aec.util.configure import example

# get cwd of the real file system before the fake fs starts
cwd = os.getcwd()


def test_example(fs: FakeFilesystem):
    fs.add_real_directory(cwd)
    example()
    assert os.path.exists(os.path.expanduser("~/.aec/ec2.toml"))
    assert os.path.exists(os.path.expanduser("~/.aec/userdata/amzn-install-docker.yaml"))
