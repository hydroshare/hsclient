from setuptools import setup, find_packages

setup(
    name='hs_rdf',
    version='0.1',
    packages=find_packages(include=['hs_rdf', 'hs_rdf.*']),
    install_requires=[
        'rdflib == 5.0.0',
        'requests == 2.24.0',
        'pydantic == 1.7.2'
    ],
    url='https://github.com/sblack-usu/hs_rdf',
    license='',
    author='Scott Black',
    author_email='scott.black@usu.edu',
    description='A python client for managing hydroshare resources'
)
