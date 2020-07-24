from setuptools import find_packages, setup

install_requires = open("requirements.txt").read().strip().split("\n")
extras_dev = open("requirements.dev.txt").read().strip().split("\n")

setup(
    name="aec",
    version="0.1.2",
    description="AWS Easy CLI",
    entry_points={"console_scripts": ["ec2 = tools.ec2:main", "sqs = tools.sqs:main"]},
    python_requires=">=3.6",
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={"dev": extras_dev},
)
