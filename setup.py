import pathlib
from setuptools import setup, find_packages

README = (pathlib.Path(__file__).parent / "README.md").read_text()

extra_deps = ["pandas", "netCDF4", "xarray", "rasterio", "fiona"]
dev_deps = ["pytest", "pytest-xdist", "pytest-cov", "mkdocs", "mknotebooks", "mkdocstrings", "mkdocstrings-python"]

setup(
    name='hsclient',
    version='1.1.6',
    packages=find_packages(include=['hsclient', 'hsclient.*'],
                           exclude=("tests",)),
    install_requires=[
        'hsmodels>=1.0.4',
        'requests',
        'requests_oauthlib',
        'setuptools',
    ],
    extras_require={
        "pandas": ["pandas"],
        "xarray": ["netCDF4", "xarray"],
        "rasterio": ["rasterio"],
        "fiona": ["fiona"],
        "all": extra_deps,
        "dev": extra_deps + dev_deps,
    },
    url='https://github.com/hydroshare/hsclient',
    license='MIT',
    author='Scott Black',
    author_email='scott.black@usu.edu',
    description='A python client for managing HydroShare resources',
    python_requires='>=3.9',
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
