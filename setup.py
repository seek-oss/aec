from setuptools import setup, find_packages

setup(
    name='aec',
    version='0.1',
    description='AWS Easy CLI',
    entry_points={'console_scripts': ['ec2 = tools.ec2:main', 'sqs = tools.sqs:main']},
    packages=find_packages(),
    install_requires=['boto3==1.9.130', 'pytoml==0.1.20', 'argh==0.26.2', 'pyjq==2.3.1'],
)