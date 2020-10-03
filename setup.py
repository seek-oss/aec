from pathlib import Path

from setuptools import find_packages, setup

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
    install_requires=[
        "boto3-stubs[ec2,sqs,compute-optimizer,ssm]==1.14.52.1",
        "pyjq==2.4.0",
        "pytoml==0.1.21",
        "pytz==2020.1",
        "rich==7.1.0",
    ],
    extras_require={
        "dev": [
            "black==20.8b1",
            "darglint==1.5.4",
            "flake8==3.8.3",
            "flake8-annotations==2.4.1",
            "flake8-colors==0.1.6",
            "moto==1.3.16",
            "pre-commit==2.7.1",
            "pytest==6.1.0",
            "tox==3.20.0",
        ]
    },
)
