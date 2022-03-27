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
    python_requires=">=3.6",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "boto3==1.21.27",
        "importlib_resources==5.6.0",
        "pytoml==0.1.21",
        "pytz==2022.1",
        "rich==12.0.1",
        "typing_extensions==4.1.1",
    ],
    extras_require={
        "dev": [
            "black==22.1.0",
            "build~=0.7",
            "boto3-stubs[ec2,compute-optimizer,ssm,s3]==1.21.27",
            "darglint==1.8.1",
            "isort==5.10.1",
            "flake8==4.0.1",
            "flake8-annotations==2.7.0",
            "flake8-colors==0.1.9",
            "moto[ec2]==3.1.1",
            "pre-commit==2.17.0",
            "pyfakefs==4.5.6",
            "pytest==7.1.1",
            "pytest-mock==3.7.0",
            "twine==3.8.0",
        ]
    },
)
