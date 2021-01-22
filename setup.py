from setuptools import setup, find_packages

setup(
    name='hsclient',
    version='0.1',
    packages=find_packages(include=['hsclient', 'hsclient.*', 'hsclient.schemas.*', 'hsclient.schemas.rdf.*']),
    install_requires=[
        'rdflib',
        'requests',
        'pydantic',
        'email-validator',
        'pandas'
    ],
    url='https://github.com/sblack-usu/hsclient',
    license='',
    author='Scott Black',
    author_email='scott.black@usu.edu',
    description='A python client for managing hydroshare resources'
)
