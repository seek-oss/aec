from pathlib import Path

from setuptools import find_packages, setup

import src.aec as aec

long_description = Path("README.md").read_text()

setup(
    name="aec-cli",
    version=aec.__version__,
    description="AWS EC2 CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seek-oss/aec",
    license="MIT",
    entry_points={"console_scripts": ["aec = aec.main:main"]},
    python_requires=">=3.7",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "boto3==1.17.62",
        "boto3-stubs[ec2,compute-optimizer,ssm]==1.17.62.0",
        "pytoml==0.1.21",
        "pytz==2021.1",
        "rich==10.1.0",
    ],
    extras_require={
        "dev": [
            "black==21.4b2",
            "darglint==1.8.0",
            "isort==5.8.0",
            "flake8==3.9.1",
            "flake8-annotations==2.6.2",
            "flake8-colors==0.1.9",
            "moto[ec2]==2.0.5",
            "pre-commit==2.12.1",
            "pytest==6.2.3",
            "twine==3.4.1",
        ]
    },
)
