from pathlib import Path

from setuptools import find_packages, setup

install_requires = Path("requirements.txt").read_text()
extras_dev = Path("requirements.dev.txt").read_text()

long_description = Path("README.md").read_text()

setup(
    name="aec",
    version="0.4.7",
    description="AWS Easy CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seek-oss/aec",
    license="MIT",
    entry_points={"console_scripts": ["aec = aec.main:main"]},
    python_requires=">=3.7",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={"dev": extras_dev},
)
