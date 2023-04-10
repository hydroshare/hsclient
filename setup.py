import pathlib
from setuptools import setup, find_packages

README = (pathlib.Path(__file__).parent / "README.md").read_text()

setup(
    name='hsclient',
    version='0.3.3',
    packages=find_packages(include=['hsclient', 'hsclient.*'],
                           exclude=("tests",)),
    install_requires=[
        'hsmodels>=0.5.5',
        'requests',
        'requests_oauthlib',
        'pandas'
    ],
    url='https://github.com/hydroshare/hsclient',
    license='MIT',
    author='Scott Black',
    author_email='scott.black@usu.edu',
    description='A python client for managing HydroShare resources',
    python_requires='>=3.6',
    long_description=README,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
