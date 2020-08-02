from setuptools import find_packages, setup

install_requires = open("requirements.txt").read().strip().split("\n")
extras_dev = open("requirements.dev.txt").read().strip().split("\n")
long_description = open("README.md").read()

setup(
    name="aec",
    version="0.2.0",
    description="AWS Easy CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seek-oss/aec",
    license="MIT",
    entry_points={"console_scripts": ["aec = tools.main:main"]},
    python_requires=">=3.6",
    packages=find_packages(exclude=["tests"]),
    install_requires=install_requires,
    extras_require={"dev": extras_dev},
)
