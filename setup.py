from setuptools import setup, find_packages

install_requires = open("requirements.txt").read().strip().split("\n")

setup(
    name="aec",
    version="0.1",
    description="AWS Easy CLI",
    entry_points={"console_scripts": ["ec2 = tools.ec2:main", "sqs = tools.sqs:main"]},
    python_requires=">=3.6",
    packages=find_packages(),
    install_requires=install_requires,
)
