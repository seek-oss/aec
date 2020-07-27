from setuptools import find_packages, setup

install_requires = open("requirements.txt").read().strip().split("\n")
extras_dev = open("requirements.dev.txt").read().strip().split("\n")

setup(
    name="aec",
    version="0.2.0",
    description="AWS Easy CLI",
    entry_points={"console_scripts": ["aec = tools.main:main"]},
    python_requires=">=3.6",
    packages=find_packages(),
    package_data={"aec": ["config-example/ec2.toml"],},
    include_package_data=True,
    install_requires=install_requires,
    extras_require={"dev": extras_dev},
)
